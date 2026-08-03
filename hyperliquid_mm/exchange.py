"""Thin wrapper around ccxt's Hyperliquid connector.

All exchange interaction lives here so the bot loop and the strategy math
stay testable. In dry-run mode every mutating call is logged and skipped,
and account state is reported as flat/zero, which lets the full pipeline run
against live public market data without credentials.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import List, Optional

import ccxt

from .config import BotConfig

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TopOfBook:
    best_bid: float
    best_ask: float
    timestamp: float  # local receive time, seconds

    @property
    def mid(self) -> float:
        return (self.best_bid + self.best_ask) / 2.0


@dataclass(frozen=True)
class Position:
    size_base: float  # signed, positive = long
    entry_price: Optional[float]
    unrealized_pnl: float


@dataclass(frozen=True)
class OpenOrder:
    id: str
    side: str  # 'buy' | 'sell'
    price: float
    remaining: float


class HyperliquidClient:
    def __init__(self, cfg: BotConfig, dry_run: bool = False):
        self.cfg = cfg
        self.dry_run = dry_run
        self.symbol = cfg.symbol
        self._dry_run_order_seq = 0

        options = {}
        if cfg.wallet_address:
            options["walletAddress"] = cfg.wallet_address
            options["privateKey"] = cfg.private_key
        self.exchange = ccxt.hyperliquid({"enableRateLimit": True, **options})
        if cfg.testnet:
            self.exchange.set_sandbox_mode(True)
            logger.info("Connected to Hyperliquid TESTNET")
        else:
            logger.info("Connected to Hyperliquid MAINNET")

        self.exchange.load_markets()
        if self.symbol not in self.exchange.markets:
            perps = [s for s in self.exchange.markets if s.endswith(":USDC")]
            raise ValueError(
                f"Symbol {self.symbol!r} not found on Hyperliquid. "
                f"Perpetual symbols look like: {perps[:8]}"
            )
        self.market = self.exchange.markets[self.symbol]
        self.tick_size = float(self.market["precision"]["price"])
        self.amount_step = float(self.market["precision"]["amount"])
        self.min_notional = float(self.market["limits"]["cost"]["min"] or 10.0)
        logger.info(
            "Market %s: tick=%s, amount step=%s, min notional=$%s",
            self.symbol, self.tick_size, self.amount_step, self.min_notional,
        )

    # ------------------------------------------------------------------
    # formatting helpers
    # ------------------------------------------------------------------
    def round_price(self, price: float) -> float:
        return float(self.exchange.price_to_precision(self.symbol, price))

    def round_amount(self, amount: float) -> float:
        return float(self.exchange.amount_to_precision(self.symbol, amount))

    # ------------------------------------------------------------------
    # market data (public)
    # ------------------------------------------------------------------
    def fetch_top_of_book(self) -> TopOfBook:
        ob = self.exchange.fetch_order_book(self.symbol, limit=5)
        if not ob["bids"] or not ob["asks"]:
            raise RuntimeError("Empty order book")
        return TopOfBook(
            best_bid=float(ob["bids"][0][0]),
            best_ask=float(ob["asks"][0][0]),
            timestamp=time.time(),
        )

    # ------------------------------------------------------------------
    # account state
    # ------------------------------------------------------------------
    def set_leverage(self) -> None:
        if self.dry_run:
            logger.info("[dry-run] would set leverage to %dx", self.cfg.leverage)
            return
        try:
            self.exchange.set_leverage(self.cfg.leverage, self.symbol)
            logger.info("Leverage set to %dx", self.cfg.leverage)
        except ccxt.BaseError as e:
            # Fails when unchanged or when a position is open; not fatal.
            logger.warning("Could not set leverage (continuing): %s", e)

    def fetch_position(self) -> Position:
        if self.dry_run:
            return Position(0.0, None, 0.0)
        positions = self.exchange.fetch_positions([self.symbol])
        for p in positions:
            if p.get("symbol") != self.symbol:
                continue
            contracts = float(p.get("contracts") or 0.0)
            side = p.get("side")
            signed = -contracts if side == "short" else contracts
            entry = p.get("entryPrice")
            return Position(
                size_base=signed,
                entry_price=float(entry) if entry else None,
                unrealized_pnl=float(p.get("unrealizedPnl") or 0.0),
            )
        return Position(0.0, None, 0.0)

    def fetch_equity(self) -> float:
        """Total account value (USDC) including unrealized PnL."""
        if self.dry_run:
            return 0.0
        balance = self.exchange.fetch_balance()
        info = balance.get("info", {})
        account_value = info.get("marginSummary", {}).get("accountValue")
        if account_value is not None:
            return float(account_value)
        return float(balance.get("USDC", {}).get("total") or 0.0)

    # ------------------------------------------------------------------
    # orders
    # ------------------------------------------------------------------
    def fetch_open_orders(self) -> List[OpenOrder]:
        if self.dry_run:
            return []
        orders = self.exchange.fetch_open_orders(self.symbol)
        return [
            OpenOrder(
                id=str(o["id"]),
                side=o["side"],
                price=float(o["price"]),
                remaining=float(o.get("remaining") or o.get("amount") or 0.0),
            )
            for o in orders
        ]

    def place_post_only_limit(
        self, side: str, amount: float, price: float, reduce_only: bool = False
    ) -> Optional[str]:
        """Place an ALO (post-only) limit order. Returns the order id.

        Returns None when the order was rejected because it would have crossed
        the book (expected occasionally; the next cycle re-quotes).
        """
        amount = self.round_amount(amount)
        price = self.round_price(price)
        if self.dry_run:
            logger.info(
                "[dry-run] would place %s %s %s @ %s%s",
                side, amount, self.symbol, price, " (reduce-only)" if reduce_only else "",
            )
            # Simulated id so the requote/churn logic runs in dry-run too.
            self._dry_run_order_seq += 1
            return f"dry-{side}-{self._dry_run_order_seq}"
        params = {"postOnly": True}
        if reduce_only:
            params["reduceOnly"] = True
        try:
            order = self.exchange.create_limit_order(self.symbol, side, amount, price, params)
            return str(order["id"])
        except ccxt.OrderImmediatelyFillable:
            logger.info("Post-only %s @ %s would cross; skipped this cycle", side, price)
            return None
        except ccxt.InvalidOrder as e:
            if "could not immediately match" in str(e).lower() or "post only" in str(e).lower():
                logger.info("Post-only %s @ %s rejected (would cross); skipped", side, price)
                return None
            raise

    def cancel_orders(self, order_ids: List[str]) -> None:
        if not order_ids:
            return
        if self.dry_run:
            logger.info("[dry-run] would cancel orders %s", order_ids)
            return
        try:
            self.exchange.cancel_orders(order_ids, self.symbol)
        except ccxt.OrderNotFound:
            pass  # already filled or cancelled — position refresh will catch it

    def cancel_all_open_orders(self) -> None:
        try:
            ids = [o.id for o in self.fetch_open_orders()]
            self.cancel_orders(ids)
            if ids:
                logger.info("Cancelled %d open order(s)", len(ids))
        except ccxt.BaseError as e:
            logger.error("Failed to cancel open orders: %s", e)

    def market_close_position(self, position: Position) -> None:
        """Flatten via a reduce-only market order (IOC with slippage bound)."""
        if abs(position.size_base) <= 0:
            return
        side = "sell" if position.size_base > 0 else "buy"
        amount = self.round_amount(abs(position.size_base))
        if self.dry_run:
            logger.info("[dry-run] would market-close %s %s", side, amount)
            return
        top = self.fetch_top_of_book()
        # Hyperliquid market orders need a price bound; allow 1% slippage.
        price = top.best_ask * 1.01 if side == "buy" else top.best_bid * 0.99
        self.exchange.create_order(
            self.symbol, "market", side, amount, self.round_price(price),
            {"reduceOnly": True},
        )
        logger.warning("Flattened position: %s %s %s", side, amount, self.symbol)
