#!/usr/bin/env python3
"""Walk-forward market selection for the gated market maker.

Scans every Hyperliquid perp above a volume floor, backtests the trend-gated
wide-quoting config on each (5m candles, ~18 days), and recommends the
markets that were profitable in the selection window — the procedure that
validated walk-forward positive in the Aug 2026 study (+$19.53 OOS across
20 selected markets while rejected markets lost -$33.85).

Feature note from that study: hand-crafted "MM-friendliness" scores based on
wide spreads were anti-predictive (corr -0.54) — wide books mark toxic flow.
Empirical winners were liquid, tight-spread, high-churn markets. Trust the
backtest, not intuition.

Usage:
    python run_select.py                     # defaults: $1M volume floor
    python run_select.py --min-volume 5e6 --top 10
"""

import argparse
import dataclasses
import sys
import time

from hyperliquid_mm.backtest import fetch_candles, run_backtest
from hyperliquid_mm.config import ConfigError, load_config

REF_PRICE = 1841.0  # gamma/k calibration reference (ETH-scale)


def lot_for(price: float) -> float:
    """~$20 notional rounded to a clean step."""
    raw = 20.0 / price
    for step in (1000, 100, 10, 1, 0.1, 0.01, 0.001, 0.0001, 0.00001):
        if raw >= step:
            return max(round(raw / step) * step, step)
    return raw


def main() -> int:
    parser = argparse.ArgumentParser(description="walk-forward market selection")
    parser.add_argument("--config", default="config.chop-harvester.json")
    parser.add_argument("--min-volume", type=float, default=1e6,
                        help="24h notional volume floor in USD (default 1e6)")
    parser.add_argument("--min-pnl", type=float, default=0.5,
                        help="selection threshold on window PnL (default +$0.5)")
    parser.add_argument("--days", type=float, default=18.0)
    parser.add_argument("--top", type=int, default=15)
    args = parser.parse_args()

    try:
        base = load_config(args.config, require_keys=False)
    except ConfigError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1

    import ccxt
    ex = ccxt.hyperliquid({"enableRateLimit": True})
    ctx = ex.publicPostInfo({"type": "metaAndAssetCtxs"})
    universe = []
    for m, a in zip(ctx[0]["universe"], ctx[1]):
        if m.get("isDelisted"):
            continue
        vlm = float(a.get("dayNtlVlm", 0))
        px = float(a.get("markPx", 0) or 0)
        if vlm >= args.min_volume and px > 0:
            universe.append((m["name"], vlm))
    universe.sort(key=lambda r: -r[1])
    print(f"Scanning {len(universe)} markets with >${args.min_volume:,.0f}/day "
          f"volume over {args.days:g} days of 5m candles...")

    results = []
    for coin, vlm in universe:
        symbol = f"{coin}/USDC:USDC"
        try:
            candles = fetch_candles(symbol, "5m", args.days)
            time.sleep(0.6)  # pace the public API
        except Exception as e:
            print(f"  {coin}: skipped ({str(e)[:60]})")
            continue
        if len(candles) < 2000:
            continue
        price = candles[-1][4]
        scale = REF_PRICE / price
        cfg = dataclasses.replace(
            base, symbol=symbol, order_size=lot_for(price),
            gamma=base.gamma * scale, k=base.k * scale,
            session_loss_limit_usd=1e18)
        try:
            r = run_backtest(cfg, candles)
        except Exception as e:
            print(f"  {coin}: backtest failed ({str(e)[:60]})")
            continue
        results.append((r.pnl, coin, vlm, len(r.fills), r.max_drawdown))

    results.sort(reverse=True)
    selected = [r for r in results if r[0] >= args.min_pnl][:args.top]
    print(f"\nScanned {len(results)} | selected {len(selected)} "
          f"(PnL >= ${args.min_pnl:+.2f} in window):\n")
    print(f"{'coin':>10} {'window PnL':>10} {'fills':>6} {'maxDD':>6} {'vol/day':>9}")
    for pnl, coin, vlm, fills, dd in selected:
        print(f"{coin:>10} {pnl:>+9.2f}$ {fills:>6} {dd * 100:>5.2f}% {vlm / 1e6:>8.1f}M")
    if selected:
        print("\nRun one bot process per selected market, e.g.:")
        top = selected[0][1]
        print(f"  python run_bot.py --config config.chop-harvester.json  "
              f"# after setting trading.symbol to {top}/USDC:USDC")
        print("\nRe-run this selection weekly — the study's edge came from "
              "recent-window selection, and regimes rotate.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
