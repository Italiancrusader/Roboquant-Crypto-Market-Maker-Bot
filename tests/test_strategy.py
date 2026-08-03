"""Unit tests for the A-S math. Run with: python -m pytest tests/ -v"""

import math
import random

import pytest

from hyperliquid_mm.strategy import (
    EwmaVolatility,
    StrategyParams,
    Quotes,
    compute_quotes,
)


PARAMS = StrategyParams(
    gamma=0.1, k=1.0, horizon_seconds=60.0, min_spread_bps=2.0, max_spread_bps=100.0
)


class TestEwmaVolatility:
    def test_constant_price_floors_at_minimum(self):
        vol = EwmaVolatility(half_life_seconds=60.0)
        for i in range(100):
            vol.update(1000.0, float(i))
        assert vol.variance_per_second == vol.floor_var

    def test_recovers_known_volatility(self):
        """Feed a GBM path with known per-second vol; EWMA should get close."""
        rng = random.Random(42)
        sigma_per_sec = 1e-4  # relative
        vol = EwmaVolatility(half_life_seconds=300.0)
        price = 2000.0
        for i in range(20_000):
            price *= math.exp(rng.gauss(0.0, sigma_per_sec))
            vol.update(price, float(i))
        estimated = vol.sigma_per_sqrt_second
        assert estimated == pytest.approx(sigma_per_sec, rel=0.15)

    def test_irregular_sampling_unbiased(self):
        """Same process sampled at irregular intervals should give a similar
        per-second estimate (this is what the old bot got wrong with its
        hardcoded sqrt(3600) scaling)."""
        rng = random.Random(7)
        sigma_per_sec = 2e-4
        vol = EwmaVolatility(half_life_seconds=300.0)
        t, price = 0.0, 2000.0
        for _ in range(20_000):
            dt = rng.choice([0.5, 1.0, 2.0, 5.0])
            t += dt
            price *= math.exp(rng.gauss(0.0, sigma_per_sec * math.sqrt(dt)))
            vol.update(price, t)
        assert vol.sigma_per_sqrt_second == pytest.approx(sigma_per_sec, rel=0.2)

    def test_ignores_non_positive_dt_and_price(self):
        vol = EwmaVolatility(half_life_seconds=60.0)
        vol.update(100.0, 1.0)
        vol.update(101.0, 1.0)  # dt == 0
        vol.update(-5.0, 2.0)  # bad price
        assert vol.sample_count == 0

    def test_warmup_gate(self):
        vol = EwmaVolatility(half_life_seconds=60.0)
        assert not vol.is_warm(warmup_seconds=10.0)
        for i in range(30):
            vol.update(1000.0 + i, float(i))
        assert vol.is_warm(warmup_seconds=10.0)


class TestComputeQuotes:
    VAR = (1e-4) ** 2  # per-second relative variance (1 bp/sqrt(s))

    def quotes(self, inventory_lots=0.0, var=None, params=PARAMS) -> Quotes:
        return compute_quotes(2000.0, inventory_lots, var or self.VAR, params)

    def test_flat_inventory_is_symmetric_around_mid(self):
        q = self.quotes(0.0)
        assert q.reservation_price == pytest.approx(2000.0)
        assert 2000.0 - q.bid == pytest.approx(q.ask - 2000.0)
        assert q.bid < 2000.0 < q.ask

    def test_terms_match_closed_form(self):
        q = self.quotes(0.0)
        sigma2_price = self.VAR * 2000.0**2
        assert q.risk_term == pytest.approx(0.1 * sigma2_price * 60.0)
        assert q.impact_term == pytest.approx((2.0 / 0.1) * math.log(1.0 + 0.1 / 1.0))

    def test_spread_within_guards_and_not_clamped_at_defaults(self):
        """With sane parameters the raw A-S spread must fall INSIDE the
        guard band — the audit found the old bot's spread always pinned at
        the cap, making the formula dead code."""
        q = self.quotes(0.0)
        mid = 2000.0
        assert not q.clamped
        assert mid * 2.0 / 10_000 < q.total_spread < mid * 100.0 / 10_000

    def test_long_inventory_skews_quotes_down(self):
        flat, long5 = self.quotes(0.0), self.quotes(5.0)
        assert long5.reservation_price < flat.reservation_price
        assert long5.ask < flat.ask  # ask more aggressive: leaning to sell
        assert long5.bid < flat.bid  # bid more passive: reluctant to buy more

    def test_short_inventory_skews_quotes_up(self):
        flat, short5 = self.quotes(0.0), self.quotes(-5.0)
        assert short5.reservation_price > flat.reservation_price
        assert short5.bid > flat.bid

    def test_skew_per_lot_equals_risk_term(self):
        flat, long1 = self.quotes(0.0), self.quotes(1.0)
        shift = flat.reservation_price - long1.reservation_price
        assert shift == pytest.approx(flat.risk_term)
        assert shift > 0

    def test_skew_is_economically_meaningful(self):
        """One order-size lot of inventory must move the reservation price by
        an amount visible at tick scale — the audit measured ~2e-9 USD in the
        old bot (i.e. no inventory management at all)."""
        q = self.quotes(1.0)
        assert q.risk_term > 0.01  # at least a cent per lot on a $2000 asset

    def test_higher_vol_widens_spread(self):
        calm = self.quotes(0.0, var=(0.5e-4) ** 2)
        wild = self.quotes(0.0, var=(5e-4) ** 2)
        assert wild.total_spread > calm.total_spread

    def test_higher_gamma_widens_spread(self):
        timid = StrategyParams(0.5, 1.0, 60.0, 2.0, 500.0)
        brave = StrategyParams(0.05, 1.0, 60.0, 2.0, 500.0)
        assert (
            self.quotes(0.0, params=timid).total_spread
            > self.quotes(0.0, params=brave).total_spread
        )

    def test_spread_clamps_and_flags(self):
        tight = StrategyParams(0.1, 1.0, 60.0, 2.0, 5.0)  # cap below raw spread
        q = self.quotes(0.0, params=tight)
        assert q.clamped
        assert q.total_spread == pytest.approx(2000.0 * 5.0 / 10_000)

    def test_rejects_bad_inputs(self):
        with pytest.raises(ValueError):
            compute_quotes(-1.0, 0.0, self.VAR, PARAMS)
        with pytest.raises(ValueError):
            StrategyParams(0.0, 1.0, 60.0, 2.0, 100.0)
        with pytest.raises(ValueError):
            StrategyParams(0.1, 1.0, 60.0, 10.0, 5.0)  # min > max
