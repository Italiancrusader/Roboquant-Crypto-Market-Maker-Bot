# Legacy code — do not use for trading

This directory preserves the previous generation of this repository for
reference:

- `HFTBOT.py` — standalone Bybit bot ("Avellaneda-Stoikov")
- `dist/` — the old multi-exchange package (`market_maker_bot.py`, config
  wizard, launchers)
- `ssrn-5066176.pdf` — Stoikov et al., *Market Making in Crypto* (Cornell FE,
  2024), the paper the original bots claimed to follow

A full audit (2026-08) found critical defects in both bots, including:

- **Broken A-S math**: a units error made the optimal-spread formula evaluate
  to 40–129% of price, so quotes were permanently pinned at the max-spread
  cap; the inventory skew evaluated to ~1e-9 USD (i.e. no inventory
  management at all).
- **Inventory double-counting**: fills were re-counted every polling cycle
  (~10–300× per trade) with no position reconciliation on restart.
- **Missing risk controls**: `stop_loss_percent`, `daily_loss_limit_usd`,
  `max_position_size_usd`, and notifications were collected by the config
  wizard but never read by any code.
- **Startup crash** on current ccxt (`ccxt.huobi` no longer exists).

The replacement lives at the repository root (`hyperliquid_mm/`), rebuilt
from scratch with corrected math, exchange-sourced position tracking, real
risk controls, and a test suite.
