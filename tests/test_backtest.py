"""Backtester tests on synthetic candles with hand-computable outcomes."""

import pytest

from hyperliquid_mm.backtest import Fill, run_backtest
from hyperliquid_mm.config import BotConfig


def make_cfg(**overrides) -> BotConfig:
    base = dict(
        testnet=True, wallet_address=None, private_key=None,
        symbol="ETH/USDC:USDC", leverage=1, order_size=0.01,
        gamma=0.1, k=1.0, horizon_seconds=60.0,
        vol_half_life_seconds=120.0, warmup_seconds=60.0,
        min_spread_bps=2.0, max_spread_bps=100.0,
        update_interval_seconds=1.0, requote_tolerance_frac=0.25,
        min_requote_seconds=5.0,
        max_inventory_usd=50.0, session_loss_limit_usd=5.0,
        flatten_on_exit=True, position_refresh_seconds=10.0,
        open_orders_refresh_seconds=5.0,
    )
    base.update(overrides)
    return BotConfig(**base)


def bar(i, o, h, l, c):
    """1-minute candle at minute i."""
    return (i * 60_000, o, h, l, c, 1.0)


def flat_bars(n, price=2000.0, start=0):
    return [bar(start + i, price, price, price, price) for i in range(n)]


class TestFillModel:
    def test_flat_market_no_fills(self):
        """Constant price never crosses quotes -> no fills, equity unchanged
        (there is nothing to flatten)."""
        result = run_backtest(make_cfg(), flat_bars(60), initial_capital=1000)
        assert result.fills == []
        assert result.final_equity == pytest.approx(1000.0)

    def test_touch_does_not_fill(self):
        """Bar low exactly AT the bid must not fill (conservative model)."""
        cfg = make_cfg()
        bars = flat_bars(30)
        # quotes after warmup sit at 2000 +/- ~0.2 (2 bps min spread floor);
        # craft a bar whose low touches but does not cross a generous bid
        bars.append(bar(30, 2000, 2000, 1999.81, 2000))
        result = run_backtest(cfg, bars, initial_capital=1000)
        buys = [f for f in result.fills if f.side == "buy" and f.maker]
        assert buys == []

    def test_round_trip_captures_spread_minus_fees(self):
        """Dip through the bid then rip through the ask: one buy, one sell,
        PnL == (ask - bid) * size - maker fees on both legs."""
        cfg = make_cfg()
        bars = flat_bars(30)
        bars.append(bar(30, 2000, 2000, 1990.0, 2000))   # deep dip -> bid fills
        bars.append(bar(31, 2000, 2010.0, 2000, 2000))   # rip -> ask fills
        bars += flat_bars(10, start=32)
        result = run_backtest(cfg, bars, initial_capital=1000)

        makers = [f for f in result.fills if f.maker]
        assert [f.side for f in makers] == ["buy", "sell"]
        buy, sell = makers
        expected = (sell.price - buy.price) * buy.size - buy.fee - sell.fee
        assert result.pnl == pytest.approx(expected, abs=1e-9)
        assert result.pnl > 0  # spread capture beats maker fees at these prices

    def test_no_lookahead(self):
        """A bar's own range must not fill quotes computed from that bar.

        The previous bar's quotes MAY legitimately fill on the spike; but if
        the engine leaked the spike bar's own quotes onto itself we would see
        a second buy fill at the spike timestamp.
        """
        cfg = make_cfg()
        bars = flat_bars(30)
        bars.append(bar(30, 2000, 2020, 1980, 2000))
        bars += flat_bars(5, start=31)
        result = run_backtest(cfg, bars, initial_capital=1000)
        spike_ts = 30 * 60_000
        buys_on_spike = [f for f in result.fills
                         if f.maker and f.side == "buy" and f.ts_ms == spike_ts]
        assert len(buys_on_spike) <= 1


class TestRiskMechanics:
    def test_inventory_cap_respected(self):
        """A relentless downtrend keeps hitting the bid; inventory must stop
        growing at the cap (reduce-only after that)."""
        cfg = make_cfg(max_inventory_usd=40.0, session_loss_limit_usd=1e9)
        price = 2000.0
        bars = flat_bars(30, price)
        for i in range(60):
            nxt = price - 3.0
            bars.append(bar(30 + i, price, price, nxt - 1.0, nxt))
            price = nxt
        result = run_backtest(cfg, bars, initial_capital=10_000)
        inv = 0.0
        max_inv_usd = 0.0
        for f in result.fills:
            if not f.maker:
                continue
            inv += f.size if f.side == "buy" else -f.size
            max_inv_usd = max(max_inv_usd, abs(inv * f.price))
        # cap is enforced on next-bar quoting, so one extra lot of slack
        assert max_inv_usd <= 40.0 + cfg.order_size * 2000.0

    def test_session_loss_limit_flattens_and_halts(self):
        """A crash beyond the loss limit must flatten (taker) and stop."""
        cfg = make_cfg(order_size=0.5, max_inventory_usd=1e9,
                       session_loss_limit_usd=5.0)
        price = 2000.0
        bars = flat_bars(30, price)
        for i in range(120):
            nxt = price - 5.0
            bars.append(bar(30 + i, price, price, nxt - 1.0, nxt))
            price = nxt
        result = run_backtest(cfg, bars, initial_capital=1000)
        assert result.halted_reason is not None
        takers = [f for f in result.fills if not f.maker]
        assert len(takers) == 1 and takers[0].side == "sell"
        # equity stopped near the limit, not far beyond it
        assert result.pnl <= -5.0
        assert result.pnl > -5.0 - 25.0  # bounded overshoot (one bar's gap)

    def test_end_flatten_leaves_no_inventory(self):
        """Whatever inventory exists at the end is closed at the last bar."""
        cfg = make_cfg(session_loss_limit_usd=1e9)
        bars = flat_bars(30)
        bars.append(bar(30, 2000, 2000, 1990, 1995))  # buy fill, then end
        result = run_backtest(cfg, bars, initial_capital=1000)
        makers = [f for f in result.fills if f.maker]
        takers = [f for f in result.fills if not f.maker]
        if makers:  # a buy happened -> must be flattened by a taker sell
            assert takers and takers[-1].side == "sell"
            net = sum(f.size if f.side == "buy" else -f.size for f in result.fills)
            assert net == pytest.approx(0.0, abs=1e-12)


class TestMetrics:
    def test_summary_runs_and_sharpe_finite(self):
        result = run_backtest(make_cfg(), flat_bars(120), initial_capital=1000)
        text = result.summary()
        assert "PnL" in text and "Sharpe" in text
        assert result.sharpe == result.sharpe  # not NaN
        assert 0.0 <= result.max_drawdown <= 1.0
