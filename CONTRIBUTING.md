# Contributing

Thanks for your interest! This project is a market maker for Hyperliquid
perpetuals implementing the Avellaneda-Stoikov model.

## Development setup

```bash
git clone https://github.com/Italiancrusader/Roboquant-Crypto-Market-Maker-Bot.git
cd Roboquant-Crypto-Market-Maker-Bot
python3 -m venv venv && source venv/bin/activate
pip install -e ".[dev]"
```

## Running

```bash
python run_bot.py --dry-run   # CLI against live market data, no credentials
python run_gui.py             # desktop control panel (needs a Python with Tk)
```

## Tests

```bash
python -m pytest tests/ -v
```

The strategy math (`hyperliquid_mm/strategy.py`) is pure and fully unit
tested — please keep it that way: no exchange or I/O code in that module, and
add tests for any change to the quoting formulas or the volatility estimator.

## Building executables

```bash
./build_executable.sh        # CLI binary + GUI app for the current platform
```

Cross-platform binaries are built by CI (`.github/workflows/build.yml`) on
tag pushes (`v*`) and manual dispatch.

## Guidelines

- Keep exchange I/O inside `hyperliquid_mm/exchange.py`.
- Secrets live in `.env` only — never in config files, code, or logs.
- Run the test suite and a `--dry-run` session before opening a PR.
- For changes to order placement or risk logic, include a testnet session log
  in the PR description.

## Reporting issues

Include the log file (`market_maker.log`), your config (never your `.env`),
and Python/ccxt versions. For suspected security issues, avoid public issues
— contact the maintainers directly.
