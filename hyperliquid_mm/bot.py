"""Main bot loop: quoting, order management and risk control."""

from __future__ import annotations

import logging
import signal
import threading
import time
from dataclasses import dataclass
from typing import Dict, Optional

import ccxt

from .config import BotConfig
from .exchange import HyperliquidClient, Position, TopOfBook
from .strategy import EwmaVolatility, StrategyParams, compute_quotes

logger = logging.getLogger(__name__)

MAX_CONSECUTIVE_ERRORS = 10
STATUS_EVERY_SECONDS = 10.0


@dataclass
class RestingOrder:
    id: str
    price: float
    size: float  # size as placed (not remaining), for stable diffing
    reduce_only: bool
    placed_at: float


@dataclass
class DesiredOrder:
    price: float
    size: float
    reduce_only: bool


class MarketMakerBot:
    def __init__(self, cfg: BotConfig, dry_run: bool = False):
        self.cfg = cfg
        self.dry_run = dry_run
        self.client = HyperliquidClient(cfg, dry_run=dry_run)
        self.vol = EwmaVolatility(cfg.vol_half_life_seconds)
        self.params = StrategyParams(
            gamma=cfg.gamma,
            k=cfg.k,
            horizon_seconds=cfg.horizon_seconds,
            min_spread_bps=cfg.min_spread_bps,
            max_spread_bps=cfg.max_spread_bps,
        )
        self.resting: Dict[str, Optional[RestingOrder]] = {"buy": None, "sell": None}
        self.position = Position(0.0, None, 0.0)
        self.equity_start: Optional[float] = None
        self.equity: float = 0.0
        self.session_fills = 0
        self._last_position_refresh = 0.0
        self._last_orders_refresh = 0.0
        self._last_status = 0.0
        self._force_position_refresh = True
        self.halted = False
        self.halt_reason: Optional[str] = None

    # ------------------------------------------------------------------
    def run(self) -> None:
        cfg = self.cfg
        logger.info(
            "Starting A-S market maker | %s | %s | order size %s | "
            "gamma=%s k=%s tau=%ss | max inventory $%s | loss limit $%s%s",
            cfg.symbol,
            "TESTNET" if cfg.testnet else "MAINNET",
            cfg.order_size, cfg.gamma, cfg.k, cfg.horizon_seconds,
            cfg.max_inventory_usd, cfg.session_loss_limit_usd,
            " | DRY RUN (no orders will be placed)" if self.dry_run else "",
        )
        self.client.set_leverage()
        # Clean slate: remove any orders left over from a previous session.
        if not self.dry_run:
            self.client.cancel_all_open_orders()

        # Graceful stop on SIGTERM (systemd, docker, kill): finish the current
        # iteration, then run the normal shutdown path. Signal handlers can only
        # be installed from the main thread; when embedded (e.g. GUI) the host
        # calls stop() instead.
        if threading.current_thread() is threading.main_thread():
            signal.signal(signal.SIGTERM, lambda *_: self._halt("SIGTERM received"))

        consecutive_errors = 0
        try:
            while not self.halted:
                loop_start = time.time()
                try:
                    self._step(loop_start)
                    consecutive_errors = 0
                except KeyboardInterrupt:
                    raise
                except ccxt.AuthenticationError as e:
                    self._halt(f"authentication failed: {e}")
                except ccxt.NetworkError as e:
                    logger.warning("Network issue (retrying): %s", e)
                    time.sleep(2.0)
                except Exception as e:
                    consecutive_errors += 1
                    logger.error(
                        "Loop error (%d/%d): %s",
                        consecutive_errors, MAX_CONSECUTIVE_ERRORS, e,
                    )
                    if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                        self._halt("too many consecutive errors")
                    else:
                        time.sleep(2.0)
                elapsed = time.time() - loop_start
                time.sleep(max(0.0, self.cfg.update_interval_seconds - elapsed))
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            self._shutdown()

    # ------------------------------------------------------------------
    def _step(self, now: float) -> None:
        top = self.client.fetch_top_of_book()
        mid = top.mid
        self.vol.update(mid, top.timestamp)

        if not self.vol.is_warm(self.cfg.warmup_seconds):
            if now - self._last_status >= STATUS_EVERY_SECONDS:
                logger.info(
                    "Warming up volatility estimator: %.0f/%.0fs",
                    self.vol.elapsed_seconds, self.cfg.warmup_seconds,
                )
                self._last_status = now
            return

        self._refresh_orders_if_due(now)
        self._refresh_position_if_due(now)

        if self._risk_breached():
            return

        quotes = compute_quotes(
            mid=mid,
            inventory_lots=self.position.size_base / self.cfg.order_size,
            variance_rel_per_second=self.vol.variance_per_second,
            params=self.params,
        )

        # Keep quotes maker-side: never price through the opposite touch.
        tick = self.client.tick_size
        bid_price = self.client.round_price(min(quotes.bid, top.best_ask - tick))
        ask_price = self.client.round_price(max(quotes.ask, top.best_bid + tick))

        desired = self._desired_orders(mid, bid_price, ask_price)
        half_spread = quotes.total_spread / 2.0
        for side in ("buy", "sell"):
            self._sync_side(side, desired.get(side), half_spread, now)

        if now - self._last_status >= STATUS_EVERY_SECONDS:
            self._print_status(top, quotes, desired)
            self._last_status = now

    # ------------------------------------------------------------------
    def _desired_orders(
        self, mid: float, bid_price: float, ask_price: float
    ) -> Dict[str, Optional[DesiredOrder]]:
        """Apply inventory limits and minimum-notional rules to raw quotes."""
        cfg = self.cfg
        pos = self.position.size_base
        inv_usd = pos * mid
        desired: Dict[str, Optional[DesiredOrder]] = {"buy": None, "sell": None}

        long_capped = inv_usd >= cfg.max_inventory_usd
        short_capped = inv_usd <= -cfg.max_inventory_usd

        # Buy side: suppressed when long inventory is at the cap. When short
        # beyond the cap it becomes the unwind side and turns reduce-only.
        if not long_capped:
            reduce_only = short_capped
            size = min(cfg.order_size, abs(pos)) if reduce_only else cfg.order_size
            desired["buy"] = self._make_desired(bid_price, size, reduce_only)

        # Sell side: mirror image.
        if not short_capped:
            reduce_only = long_capped
            size = min(cfg.order_size, abs(pos)) if reduce_only else cfg.order_size
            desired["sell"] = self._make_desired(ask_price, size, reduce_only)

        if long_capped or short_capped:
            side = "long" if long_capped else "short"
            logger.warning(
                "Inventory cap reached (%s $%.2f >= $%.2f): quoting reduce-only unwind",
                side, abs(inv_usd), cfg.max_inventory_usd,
            )
        return desired

    def _make_desired(
        self, price: float, size: float, reduce_only: bool
    ) -> Optional[DesiredOrder]:
        size = self.client.round_amount(size)
        if size <= 0 or size * price < self.client.min_notional:
            logger.warning(
                "Order notional $%.2f below exchange minimum $%.2f; side skipped "
                "(increase trading.order_size)",
                size * price, self.client.min_notional,
            )
            return None
        return DesiredOrder(price=price, size=size, reduce_only=reduce_only)

    # ------------------------------------------------------------------
    def _sync_side(
        self, side: str, want: Optional[DesiredOrder], half_spread: float, now: float
    ) -> None:
        have = self.resting[side]

        if want is None:
            if have is not None:
                self.client.cancel_orders([have.id])
                self.resting[side] = None
            return

        if have is not None:
            tolerance = max(self.cfg.requote_tolerance_frac * half_spread,
                            self.client.tick_size)
            drifted = abs(have.price - want.price) > tolerance
            resized = abs(have.size - want.size) > 0.2 * want.size
            mode_changed = have.reduce_only != want.reduce_only
            if not (drifted or resized or mode_changed):
                return
            if now - have.placed_at < self.cfg.min_requote_seconds:
                return  # rate-limit churn; keep queue position a bit longer
            self.client.cancel_orders([have.id])
            self.resting[side] = None

        order_id = self.client.place_post_only_limit(
            side, want.size, want.price, reduce_only=want.reduce_only
        )
        if order_id is not None:
            self.resting[side] = RestingOrder(
                id=order_id, price=want.price, size=want.size,
                reduce_only=want.reduce_only, placed_at=now,
            )

    # ------------------------------------------------------------------
    def _refresh_orders_if_due(self, now: float) -> None:
        if now - self._last_orders_refresh < self.cfg.open_orders_refresh_seconds:
            return
        self._last_orders_refresh = now
        if self.dry_run:
            return
        open_orders = self.client.fetch_open_orders()
        open_ids = {o.id for o in open_orders}

        for side in ("buy", "sell"):
            have = self.resting[side]
            if have is not None and have.id not in open_ids:
                logger.info("%s order %s no longer open — filled or cancelled", side, have.id)
                self.resting[side] = None
                self.session_fills += 1
                self._force_position_refresh = True

        # Defensive: cancel anything on the book we are not tracking
        # (e.g. leftovers after a reconnect).
        tracked = {o.id for o in self.resting.values() if o is not None}
        stray = [o.id for o in open_orders if o.id not in tracked]
        if stray:
            logger.warning("Cancelling %d untracked order(s): %s", len(stray), stray)
            self.client.cancel_orders(stray)

    def _refresh_position_if_due(self, now: float) -> None:
        due = (
            self._force_position_refresh
            or now - self._last_position_refresh >= self.cfg.position_refresh_seconds
        )
        if not due:
            return
        self._last_position_refresh = now
        self._force_position_refresh = False
        if self.dry_run:
            return
        previous = self.position.size_base
        self.position = self.client.fetch_position()
        self.equity = self.client.fetch_equity()
        if self.equity_start is None:
            self.equity_start = self.equity
            logger.info("Session starting equity: $%.2f", self.equity_start)
        delta = self.position.size_base - previous
        if abs(delta) > 1e-12:
            logger.info(
                "Position change: %+.6f -> now %+.6f %s",
                delta, self.position.size_base, self.cfg.symbol.split("/")[0],
            )

    # ------------------------------------------------------------------
    def _risk_breached(self) -> bool:
        if self.dry_run or self.equity_start is None:
            return False
        session_pnl = self.equity - self.equity_start
        if session_pnl <= -self.cfg.session_loss_limit_usd:
            logger.error(
                "SESSION LOSS LIMIT BREACHED: PnL $%.2f <= -$%.2f",
                session_pnl, self.cfg.session_loss_limit_usd,
            )
            self._halt("session loss limit breached", flatten=True)
            return True
        return False

    def _halt(self, reason: str, flatten: bool = False) -> None:
        self.halted = True
        self.halt_reason = reason
        self._flatten_requested = flatten
        logger.error("HALTING: %s", reason)

    def stop(self, reason: str = "stop requested") -> None:
        """Request a graceful stop from another thread (e.g. a GUI)."""
        self.halted = True
        self.halt_reason = reason

    # ------------------------------------------------------------------
    def _shutdown(self) -> None:
        logger.info("Shutting down: cancelling open orders")
        try:
            self.client.cancel_all_open_orders()
        except Exception as e:
            logger.error("Cleanup cancel failed: %s", e)

        flatten = self.cfg.flatten_on_exit or getattr(self, "_flatten_requested", False)
        if flatten and not self.dry_run:
            try:
                position = self.client.fetch_position()
                self.client.market_close_position(position)
            except Exception as e:
                logger.error(
                    "FAILED TO FLATTEN POSITION — close it manually on the exchange: %s", e
                )

        if not self.dry_run and self.equity_start is not None:
            try:
                final_equity = self.client.fetch_equity()
                logger.info(
                    "Session summary: equity $%.2f -> $%.2f (PnL $%+.2f), %d fill event(s)",
                    self.equity_start, final_equity,
                    final_equity - self.equity_start, self.session_fills,
                )
            except Exception:
                pass
        logger.info("Bot stopped%s", f" ({self.halt_reason})" if self.halt_reason else "")

    # ------------------------------------------------------------------
    def _print_status(self, top: TopOfBook, quotes, desired) -> None:
        mid = top.mid
        sigma_1m_bps = self.vol.sigma_per_sqrt_second * (60**0.5) * 10_000
        spread_bps = quotes.total_spread / mid * 10_000
        inv_usd = self.position.size_base * mid
        inv_pct = abs(inv_usd) / self.cfg.max_inventory_usd * 100
        buy = desired.get("buy")
        sell = desired.get("sell")
        logger.info(
            "mid=%.4f | sigma=%.1f bps/min^0.5 | spread=%.1f bps%s | skew/lot=%.4f | "
            "bid=%s ask=%s | pos=%+.6f ($%.2f, %.0f%% of cap) | equity=$%.2f | fills=%d",
            mid,
            sigma_1m_bps,
            spread_bps,
            " (clamped)" if quotes.clamped else "",
            quotes.risk_term,
            f"{buy.size}@{buy.price}" if buy else "—",
            f"{sell.size}@{sell.price}" if sell else "—",
            self.position.size_base,
            inv_usd,
            inv_pct,
            self.equity,
            self.session_fills,
        )
