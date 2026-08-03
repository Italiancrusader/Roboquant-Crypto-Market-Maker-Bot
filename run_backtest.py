#!/usr/bin/env python3
"""Backtest the A-S market maker on historical Hyperliquid candles.

Usage:
    python run_backtest.py --days 7
    python run_backtest.py --days 30 --symbol BTC/USDC:USDC --timeframe 5m
    python run_backtest.py --days 7 --csv equity.csv

Uses the same config.json as the live bot (strategy parameters, order size,
inventory cap, loss limit). No credentials needed — candle data is public.
"""

import argparse
import sys

from hyperliquid_mm.backtest import fetch_candles, run_backtest
from hyperliquid_mm.config import ConfigError, load_config


def main() -> int:
    parser = argparse.ArgumentParser(description="A-S market maker backtest")
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--symbol", default=None, help="override config symbol")
    parser.add_argument("--days", type=float, default=7.0)
    parser.add_argument("--timeframe", default="1m")
    parser.add_argument("--capital", type=float, default=1000.0)
    parser.add_argument("--testnet-data", action="store_true",
                        help="use testnet candles (default: mainnet — better data)")
    parser.add_argument("--csv", default=None, help="write equity curve to CSV")
    args = parser.parse_args()

    try:
        cfg = load_config(args.config, require_keys=False)
    except ConfigError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1
    symbol = args.symbol or cfg.symbol
    if args.symbol:
        cfg = type(cfg)(**{**cfg.__dict__, "symbol": args.symbol})

    print(f"Fetching {args.days:g} days of {args.timeframe} candles for {symbol}...")
    candles = fetch_candles(symbol, args.timeframe, args.days,
                            testnet=args.testnet_data)
    print(f"Got {len(candles)} candles. Running backtest...")

    result = run_backtest(cfg, candles, initial_capital=args.capital)
    result.timeframe = args.timeframe
    print()
    print(result.summary())
    print()
    print("Note: candle-level simulation is an approximation of the live "
          "1-second loop.\nFills are conservative (strict price cross, no "
          "queue modeling); treat results\nas indicative, not predictive.")

    if args.csv:
        with open(args.csv, "w") as f:
            f.write("timestamp_ms,equity\n")
            for ts, eq in result.equity_curve:
                f.write(f"{ts},{eq:.6f}\n")
        print(f"\nEquity curve written to {args.csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
