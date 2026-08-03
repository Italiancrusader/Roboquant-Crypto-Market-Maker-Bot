#!/usr/bin/env python3
"""Entry point for the Hyperliquid Avellaneda-Stoikov market maker.

Usage:
    python run_bot.py                    # uses config.json, requires HL_* env vars
    python run_bot.py --config my.json
    python run_bot.py --dry-run          # no credentials needed, no orders placed
"""

import argparse
import logging
import os
import sys

IS_FROZEN = getattr(sys, "frozen", False)  # True inside a PyInstaller binary

# Anchor config/.env/log next to the executable when packaged (a double-clicked
# binary starts in the user's home dir, which is not where its files belong).
BASE_DIR = os.path.dirname(sys.executable) if IS_FROZEN else os.getcwd()

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, ".env"))
except ImportError:
    pass

from hyperliquid_mm.bot import MarketMakerBot
from hyperliquid_mm.config import ConfigError, load_config, write_default_config


def main() -> int:
    parser = argparse.ArgumentParser(description="Hyperliquid A-S market maker")
    parser.add_argument("--config", default="config.json", help="path to config file")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="compute and log quotes against live market data without placing orders "
             "(no credentials required)",
    )
    args = parser.parse_args()

    if args.config == "config.json":
        args.config = os.path.join(BASE_DIR, "config.json")
    if not os.path.exists(args.config):
        write_default_config(args.config)
        print(
            f"No config found — created one with safe defaults "
            f"(testnet, ETH/USDC, 0.01 ETH orders) at:\n  {os.path.abspath(args.config)}\n"
            f"Review it, then put HL_WALLET_ADDRESS / HL_PRIVATE_KEY in a .env file "
            f"in the same folder and run again.\n"
            f"Tip: '--dry-run' works right now, with no credentials."
        )
        if IS_FROZEN and sys.stdin.isatty():
            input("\nPress Enter to exit...")
        return 0

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(BASE_DIR, "market_maker.log")),
            logging.StreamHandler(),
        ],
    )

    try:
        cfg = load_config(args.config, require_keys=not args.dry_run)
    except ConfigError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1

    if not cfg.testnet and not args.dry_run:
        print(
            "\n*** MAINNET mode: this bot will trade with real funds. ***\n"
            "Type 'yes' to continue: ",
            end="",
            flush=True,
        )
        if input().strip().lower() != "yes":
            print("Aborted.")
            return 1

    bot = MarketMakerBot(cfg, dry_run=args.dry_run)
    bot.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
