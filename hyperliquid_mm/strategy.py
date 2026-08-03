"""Avellaneda-Stoikov quoting math.

Pure functions/classes with no exchange or I/O dependencies so the math can be
unit-tested in isolation.

Units convention (kept consistent throughout):

- ``mid`` and all prices are in quote currency (USD/USDC).
- Volatility is estimated as an EWMA of squared log returns normalised by the
  actual elapsed time between samples, giving a *relative variance per second*.
  It is converted to price units via ``sigma2_price = sigma2_rel * mid**2``
  (USD^2 per second).
- ``gamma`` (risk aversion) and ``k`` (order-book liquidity/intensity decay)
  are both in 1/USD, so every term of the A-S formulas below is in USD.
- Inventory ``q`` is expressed in *lots*, i.e. multiples of the configured
  order size. This follows the discrete-unit convention of the original paper
  and gives the inventory skew a magnitude comparable to the spread (holding
  one lot skews the reservation price by exactly the risk term).
- ``tau`` is a fixed rolling horizon in seconds. We deliberately do not decay
  tau to zero within a session: for a perpetual, 24/7 market the standard
  practice is the stationary (infinite-horizon) approximation rather than the
  terminal-time behaviour of the original finite-horizon model.

Formulas (Avellaneda & Stoikov, 2008):

    reservation price  r = s - q * gamma * sigma^2 * tau
    optimal spread     delta = gamma * sigma^2 * tau + (2/gamma) * ln(1 + gamma/k)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional


class EwmaVolatility:
    """EWMA estimator of per-second relative return variance.

    Handles irregular sampling by normalising each squared log return by the
    actual elapsed time and by scaling the EWMA decay to the gap length.
    """

    def __init__(self, half_life_seconds: float, floor_sigma_rel: float = 1e-6):
        if half_life_seconds <= 0:
            raise ValueError("half_life_seconds must be positive")
        self.half_life_seconds = half_life_seconds
        self.floor_var = floor_sigma_rel**2
        self._var_per_sec: Optional[float] = None
        self._last_mid: Optional[float] = None
        self._last_ts: Optional[float] = None
        self.elapsed_seconds = 0.0
        self.sample_count = 0

    def update(self, mid: float, timestamp: float) -> None:
        if mid <= 0:
            return
        if self._last_mid is None or self._last_ts is None:
            self._last_mid, self._last_ts = mid, timestamp
            return
        dt = timestamp - self._last_ts
        if dt <= 0:
            return
        log_ret = math.log(mid / self._last_mid)
        inst_var = (log_ret * log_ret) / dt  # relative variance per second
        if self._var_per_sec is None:
            self._var_per_sec = inst_var
        else:
            # Decay scaled to the gap so irregular sampling stays unbiased.
            alpha = 1.0 - 0.5 ** (dt / self.half_life_seconds)
            self._var_per_sec += alpha * (inst_var - self._var_per_sec)
        self._last_mid, self._last_ts = mid, timestamp
        self.elapsed_seconds += dt
        self.sample_count += 1

    @property
    def variance_per_second(self) -> float:
        """Relative return variance per second, floored away from zero."""
        if self._var_per_sec is None:
            return self.floor_var
        return max(self._var_per_sec, self.floor_var)

    @property
    def sigma_per_sqrt_second(self) -> float:
        return math.sqrt(self.variance_per_second)

    def is_warm(self, warmup_seconds: float, min_samples: int = 10) -> bool:
        return self.elapsed_seconds >= warmup_seconds and self.sample_count >= min_samples


@dataclass(frozen=True)
class StrategyParams:
    gamma: float  # risk aversion, 1/USD
    k: float  # order-book intensity decay, 1/USD
    horizon_seconds: float  # rolling horizon tau
    min_spread_bps: float  # total-spread floor, basis points of mid
    max_spread_bps: float  # total-spread cap, basis points of mid

    def __post_init__(self) -> None:
        if self.gamma <= 0 or self.k <= 0 or self.horizon_seconds <= 0:
            raise ValueError("gamma, k and horizon_seconds must be positive")
        if not 0 < self.min_spread_bps <= self.max_spread_bps:
            raise ValueError("require 0 < min_spread_bps <= max_spread_bps")


@dataclass(frozen=True)
class Quotes:
    bid: float
    ask: float
    reservation_price: float
    total_spread: float
    risk_term: float  # gamma * sigma^2 * tau, USD (also the skew per lot)
    impact_term: float  # (2/gamma) * ln(1 + gamma/k), USD
    clamped: bool  # True when the raw A-S spread hit the min/max guard


def trend_zscore(
    mid_now: float,
    mid_then: float,
    elapsed_seconds: float,
    sigma_rel_per_sqrt_second: float,
) -> float:
    """How trending is the market, in diffusion units?

    Returns |relative move| divided by the move a random walk with the
    current volatility would produce over the same window. z >> 1 means a
    directional trend; quoting symmetrically into it is adverse selection.
    Used as a stand-down gate: research on 52 days of Hyperliquid data
    showed wide symmetric quoting earns in chop and bleeds in trends.
    """
    if mid_now <= 0 or mid_then <= 0 or elapsed_seconds <= 0:
        return 0.0
    expected = sigma_rel_per_sqrt_second * math.sqrt(elapsed_seconds)
    if expected <= 0:
        return 0.0
    move = abs(mid_now - mid_then) / mid_now
    return move / expected


def compute_quotes(
    mid: float,
    inventory_lots: float,
    variance_rel_per_second: float,
    params: StrategyParams,
) -> Quotes:
    """Compute A-S bid/ask around the reservation price.

    ``inventory_lots`` is signed: positive when long. A long inventory pushes
    the reservation price (and both quotes) down, making the ask more
    attractive and the bid less, so the book leans toward unwinding.
    """
    if mid <= 0:
        raise ValueError("mid must be positive")
    sigma2_price = variance_rel_per_second * mid * mid  # USD^2 per second
    risk_term = params.gamma * sigma2_price * params.horizon_seconds
    impact_term = (2.0 / params.gamma) * math.log(1.0 + params.gamma / params.k)
    raw_spread = risk_term + impact_term

    min_spread = mid * params.min_spread_bps / 10_000.0
    max_spread = mid * params.max_spread_bps / 10_000.0
    total_spread = min(max(raw_spread, min_spread), max_spread)
    clamped = total_spread != raw_spread

    reservation = mid - inventory_lots * risk_term
    half = total_spread / 2.0
    return Quotes(
        bid=reservation - half,
        ask=reservation + half,
        reservation_price=reservation,
        total_spread=total_spread,
        risk_term=risk_term,
        impact_term=impact_term,
        clamped=clamped,
    )
