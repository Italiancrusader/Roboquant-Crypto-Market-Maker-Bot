"""Candle-driven backtester for the A-S market maker.

Runs the exact production quoting code (``strategy.compute_quotes`` and
``EwmaVolatility``) against historical Hyperliquid candles, with fill and
risk mechanics mirroring the live bot (inventory cap with reduce-only
unwind, session loss limit, flatten at end).

Fill model (deliberately conservative, documented in the README):

- Quotes computed at bar *t* are only eligible to fill against bar *t+1*
  (no look-ahead).
- A resting bid fills only if the next bar trades strictly BELOW it
  (``low < bid``); an ask only if ``high > ask``. Touches don't fill —
  queue position at the touch is unknowable from candles.
- Fills execute at the limit price with the maker fee. Both sides may fill
  in the same bar.
- The final position is flattened at the last close, paying the taker fee
  (mirrors ``flatten_on_exit``).

Metric definitions (Sharpe, max drawdown, win terminology) follow the
conventions of Roboquant's backtest-engine so results are comparable.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .config import BotConfig
from .strategy import EwmaVolatility, StrategyParams, compute_quotes, trend_zscore

# Hyperliquid default fee tier
MAKER_FEE = 0.00015
TAKER_FEE = 0.00045

Candle = Tuple[int, float, float, float, float, float]  # ts_ms, o, h, l, c, v


# ----------------------------------------------------------------------
# data
# ----------------------------------------------------------------------
def fetch_candles(
    symbol: str,
    timeframe: str = "1m",
    days: float = 7.0,
    testnet: bool = False,
) -> List[Candle]:
    """Fetch OHLCV candles from Hyperliquid via ccxt, paginating as needed."""
    import ccxt

    ex = ccxt.hyperliquid({"enableRateLimit": True})
    if testnet:
        ex.set_sandbox_mode(True)
    ex.load_markets()
    if symbol not in ex.markets:
        raise ValueError(f"Unknown symbol {symbol!r}")

    tf_ms = ex.parse_timeframe(timeframe) * 1000
    now_ms = ex.milliseconds()
    since = int(now_ms - days * 86_400_000)
    out: List[Candle] = []
    while since < now_ms:
        batch = ex.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
        if not batch:
            break
        for row in batch:
            if not out or row[0] > out[-1][0]:
                out.append(tuple(row))  # type: ignore[arg-type]
        new_since = batch[-1][0] + tf_ms
        if new_since <= since:
            break
        since = new_since
    return out


# ----------------------------------------------------------------------
# simulation
# ----------------------------------------------------------------------
@dataclass
class Fill:
    ts_ms: int
    side: str  # 'buy' | 'sell'
    price: float
    size: float
    fee: float
    maker: bool


@dataclass
class BacktestResult:
    symbol: str
    timeframe: str
    start_ms: int
    end_ms: int
    initial_capital: float
    final_equity: float
    fills: List[Fill]
    equity_curve: List[Tuple[int, float]]  # (ts_ms, equity)
    halted_reason: Optional[str] = None
    _cache: dict = field(default_factory=dict, repr=False)

    # -------------------------------------------------- core metrics
    @property
    def pnl(self) -> float:
        return self.final_equity - self.initial_capital

    @property
    def total_return(self) -> float:
        return self.pnl / self.initial_capital

    @property
    def fees_paid(self) -> float:
        return sum(f.fee for f in self.fills)

    @property
    def maker_volume(self) -> float:
        return sum(f.price * f.size for f in self.fills if f.maker)

    @property
    def n_buys(self) -> int:
        return sum(1 for f in self.fills if f.side == "buy")

    @property
    def n_sells(self) -> int:
        return sum(1 for f in self.fills if f.side == "sell")

    @property
    def duration_days(self) -> float:
        return (self.end_ms - self.start_ms) / 86_400_000

    @property
    def fills_per_day(self) -> float:
        d = self.duration_days
        return len(self.fills) / d if d > 0 else 0.0

    @property
    def max_drawdown(self) -> float:
        """Max peak-to-trough drawdown as a fraction of the peak."""
        peak, worst = float("-inf"), 0.0
        for _, eq in self.equity_curve:
            peak = max(peak, eq)
            if peak > 0:
                worst = max(worst, (peak - eq) / peak)
        return worst

    @property
    def sharpe(self) -> float:
        """Annualized Sharpe from per-bar equity returns (rf = 0)."""
        eqs = [eq for _, eq in self.equity_curve]
        if len(eqs) < 3:
            return 0.0
        rets = [(b - a) / a for a, b in zip(eqs, eqs[1:]) if a > 0]
        if len(rets) < 2:
            return 0.0
        mean = sum(rets) / len(rets)
        var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
        if var == 0:
            return 0.0
        bar_seconds = (self.end_ms - self.start_ms) / 1000 / max(len(eqs) - 1, 1)
        bars_per_year = 365 * 86_400 / max(bar_seconds, 1e-9)
        return mean / math.sqrt(var) * math.sqrt(bars_per_year)

    def summary(self) -> str:
        lines = [
            f"Backtest: {self.symbol} {self.timeframe} | "
            f"{self.duration_days:.1f} days | {len(self.equity_curve)} bars",
            f"  PnL:            ${self.pnl:+.2f}  ({self.total_return * 100:+.3f}% "
            f"on ${self.initial_capital:.0f})",
            f"  Fills:          {len(self.fills)} ({self.n_buys} buys / "
            f"{self.n_sells} sells, {self.fills_per_day:.1f}/day)",
            f"  Maker volume:   ${self.maker_volume:,.0f}",
            f"  Fees paid:      ${self.fees_paid:.2f}",
            f"  Max drawdown:   {self.max_drawdown * 100:.2f}%",
            f"  Sharpe (ann.):  {self.sharpe:.2f}",
        ]
        if self.halted_reason:
            lines.append(f"  HALTED EARLY:   {self.halted_reason}")
        return "\n".join(lines)


def run_backtest(
    cfg: BotConfig,
    candles: List[Candle],
    initial_capital: float = 1_000.0,
    maker_fee: float = MAKER_FEE,
    taker_fee: float = TAKER_FEE,
    tick_size: float = 0.0,
) -> BacktestResult:
    """Simulate the live bot's quoting/risk mechanics over candles.

    ``cfg`` is the same config the live bot uses — strategy parameters,
    order size, inventory cap and session loss limit are all honoured.
    """
    if len(candles) < 12:
        raise ValueError("Not enough candles to backtest")

    params = StrategyParams(
        gamma=cfg.gamma,
        k=cfg.k,
        horizon_seconds=cfg.horizon_seconds,
        min_spread_bps=cfg.min_spread_bps,
        max_spread_bps=cfg.max_spread_bps,
    )
    vol = EwmaVolatility(cfg.vol_half_life_seconds)

    cash = initial_capital
    inv = 0.0  # base units, signed
    fills: List[Fill] = []
    equity_curve: List[Tuple[int, float]] = []
    halted: Optional[str] = None

    pending_bid: Optional[Tuple[float, float]] = None  # (price, size)
    pending_ask: Optional[Tuple[float, float]] = None
    closes: List[Tuple[int, float]] = []  # (ts_ms, close) for the trend gate

    for ts_ms, _o, high, low, close, _v in candles:
        # 1) resolve last bar's quotes against this bar (no look-ahead)
        if pending_bid is not None and low < pending_bid[0]:
            px, sz = pending_bid
            fee = px * sz * maker_fee
            cash -= px * sz + fee
            inv += sz
            fills.append(Fill(ts_ms, "buy", px, sz, fee, maker=True))
        if pending_ask is not None and high > pending_ask[0]:
            px, sz = pending_ask
            fee = px * sz * maker_fee
            cash += px * sz - fee
            inv -= sz
            fills.append(Fill(ts_ms, "sell", px, sz, fee, maker=True))
        pending_bid = pending_ask = None

        # 2) mark to market + session loss limit (mirrors the live bot)
        equity = cash + inv * close
        equity_curve.append((ts_ms, equity))
        if equity - initial_capital <= -cfg.session_loss_limit_usd:
            fee = abs(inv) * close * taker_fee
            if inv != 0:
                cash += inv * close - fee
                fills.append(Fill(ts_ms, "sell" if inv > 0 else "buy",
                                  close, abs(inv), fee, maker=False))
                inv = 0.0
            halted = "session loss limit breached (flattened)"
            equity_curve[-1] = (ts_ms, cash)
            break

        # 3) update volatility and compute next bar's quotes
        vol.update(close, ts_ms / 1000.0)
        closes.append((ts_ms, close))
        if not vol.is_warm(cfg.warmup_seconds):
            continue

        # trend gate (mirrors the live bot): stand down to unwind-only when
        # the lookback move exceeds trend_gate_z diffusion units
        gated = False
        if cfg.trend_gate_hours > 0:
            window_ms = cfg.trend_gate_hours * 3_600_000
            while closes and closes[0][0] < ts_ms - window_ms:
                closes.pop(0)
            if closes and ts_ms - closes[0][0] >= window_ms * 0.5:
                then_ts, then_close = closes[0]
                z = trend_zscore(close, then_close, (ts_ms - then_ts) / 1000.0,
                                 vol.sigma_per_sqrt_second)
                gated = z > cfg.trend_gate_z

        q = compute_quotes(close, inv / cfg.order_size,
                           vol.variance_per_second, params)
        bid_px = min(q.bid, close - tick_size) if tick_size else min(q.bid, close)
        ask_px = max(q.ask, close + tick_size) if tick_size else max(q.ask, close)

        # inventory cap semantics identical to the live _desired_orders
        inv_usd = inv * close
        long_capped = inv_usd >= cfg.max_inventory_usd
        short_capped = inv_usd <= -cfg.max_inventory_usd
        if gated:
            long_capped = True
            short_capped = True
            if inv > 0:
                short_capped = False  # reduce-only sell allowed
            elif inv < 0:
                long_capped = False  # reduce-only buy allowed
        if not long_capped:
            size = min(cfg.order_size, abs(inv)) if short_capped else cfg.order_size
            if size > 0 and size * bid_px >= 10.0:
                pending_bid = (bid_px, size)
        if not short_capped:
            size = min(cfg.order_size, abs(inv)) if long_capped else cfg.order_size
            if size > 0 and size * ask_px >= 10.0:
                pending_ask = (ask_px, size)

    # 4) flatten whatever is left at the last close (flatten_on_exit)
    if halted is None and inv != 0:
        ts_ms, close = candles[-1][0], candles[-1][4]
        fee = abs(inv) * close * taker_fee
        cash += inv * close - fee
        fills.append(Fill(ts_ms, "sell" if inv > 0 else "buy",
                          close, abs(inv), fee, maker=False))
        inv = 0.0
        equity_curve[-1] = (ts_ms, cash)

    return BacktestResult(
        symbol=cfg.symbol,
        timeframe="?",
        start_ms=candles[0][0],
        end_ms=candles[-1][0],
        initial_capital=initial_capital,
        final_equity=equity_curve[-1][1] if equity_curve else initial_capital,
        fills=fills,
        equity_curve=equity_curve,
        halted_reason=halted,
    )


# ----------------------------------------------------------------------
# L1 (top-of-book) replay
# ----------------------------------------------------------------------
Tick = Tuple[int, float, float]  # ts_ms, best_bid, best_ask


def run_l1_backtest(
    cfg: BotConfig,
    ticks: List[Tick],
    initial_capital: float = 1_000.0,
    maker_fee: float = MAKER_FEE,
    taker_fee: float = TAKER_FEE,
    equity_sample_seconds: float = 60.0,
) -> BacktestResult:
    """Replay top-of-book ticks through the live bot's exact mechanics.

    Much higher fidelity than the candle backtest: production data cadence,
    the live requote tolerance/min-requote throttle, and the vol estimator
    fed real mid updates. Fill rule: a resting bid fills when the best ask
    drops to or below it (marketable flow traded through our level); the
    mirror for asks. Queue position is still not modeled — fills at the
    exact touch remain unknowable — so results stay conservative-leaning
    but much closer to live behaviour than candles.
    """
    if len(ticks) < 100:
        raise ValueError("Not enough ticks to backtest")

    params = StrategyParams(
        gamma=cfg.gamma, k=cfg.k, horizon_seconds=cfg.horizon_seconds,
        min_spread_bps=cfg.min_spread_bps, max_spread_bps=cfg.max_spread_bps,
    )
    vol = EwmaVolatility(cfg.vol_half_life_seconds)

    cash, inv = initial_capital, 0.0
    fills: List[Fill] = []
    equity_curve: List[Tuple[int, float]] = []
    halted: Optional[str] = None
    resting = {"buy": None, "sell": None}  # side -> (price, size, placed_ts_s)
    last_equity_sample = 0.0

    for ts_ms, best_bid, best_ask in ticks:
        if best_bid <= 0 or best_ask <= 0 or best_ask <= best_bid:
            continue
        now_s = ts_ms / 1000.0
        mid = (best_bid + best_ask) / 2.0

        # 1) fills: opposite touch crossing our resting level
        rb = resting["buy"]
        if rb is not None and best_ask <= rb[0]:
            px, sz, _ = rb
            fee = px * sz * maker_fee
            cash -= px * sz + fee
            inv += sz
            fills.append(Fill(ts_ms, "buy", px, sz, fee, maker=True))
            resting["buy"] = None
        ra = resting["sell"]
        if ra is not None and best_bid >= ra[0]:
            px, sz, _ = ra
            fee = px * sz * maker_fee
            cash += px * sz - fee
            inv -= sz
            fills.append(Fill(ts_ms, "sell", px, sz, fee, maker=True))
            resting["sell"] = None

        # 2) equity + loss limit (sampled to keep the curve small)
        equity = cash + inv * mid
        if now_s - last_equity_sample >= equity_sample_seconds:
            equity_curve.append((ts_ms, equity))
            last_equity_sample = now_s
        if equity - initial_capital <= -cfg.session_loss_limit_usd:
            fee = abs(inv) * mid * taker_fee
            if inv != 0:
                cash += inv * mid - fee
                fills.append(Fill(ts_ms, "sell" if inv > 0 else "buy",
                                  mid, abs(inv), fee, maker=False))
                inv = 0.0
            halted = "session loss limit breached (flattened)"
            equity_curve.append((ts_ms, cash))
            break

        # 3) vol + quotes with the live requote throttle
        vol.update(mid, now_s)
        if not vol.is_warm(cfg.warmup_seconds):
            continue

        q = compute_quotes(mid, inv / cfg.order_size,
                           vol.variance_per_second, params)
        bid_px = min(q.bid, best_ask * (1 - 1e-6))
        ask_px = max(q.ask, best_bid * (1 + 1e-6))
        half = q.total_spread / 2.0
        tol = cfg.requote_tolerance_frac * half

        inv_usd = inv * mid
        long_capped = inv_usd >= cfg.max_inventory_usd
        short_capped = inv_usd <= -cfg.max_inventory_usd

        for side, want_px, capped, other_capped in (
            ("buy", bid_px, long_capped, short_capped),
            ("sell", ask_px, short_capped, long_capped),
        ):
            if capped:
                resting[side] = None
                continue
            size = min(cfg.order_size, abs(inv)) if other_capped else cfg.order_size
            if size <= 0 or size * want_px < 10.0:
                resting[side] = None
                continue
            have = resting[side]
            if have is not None:
                drifted = abs(have[0] - want_px) > tol
                too_soon = now_s - have[2] < cfg.min_requote_seconds
                if not drifted or too_soon:
                    continue
            resting[side] = (want_px, size, now_s)

        # crossing guard mirrors live: never rest through the touch
        if resting["buy"] is not None and resting["buy"][0] >= best_ask:
            resting["buy"] = None
        if resting["sell"] is not None and resting["sell"][0] <= best_bid:
            resting["sell"] = None

    if halted is None:
        ts_ms = ticks[-1][0]
        mid = (ticks[-1][1] + ticks[-1][2]) / 2.0
        if inv != 0:
            fee = abs(inv) * mid * taker_fee
            cash += inv * mid - fee
            fills.append(Fill(ts_ms, "sell" if inv > 0 else "buy",
                              mid, abs(inv), fee, maker=False))
            inv = 0.0
        equity_curve.append((ts_ms, cash))

    return BacktestResult(
        symbol=cfg.symbol,
        timeframe="L1",
        start_ms=ticks[0][0],
        end_ms=ticks[-1][0],
        initial_capital=initial_capital,
        final_equity=equity_curve[-1][1] if equity_curve else initial_capital,
        fills=fills,
        equity_curve=equity_curve,
        halted_reason=halted,
    )
