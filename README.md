# Hyperliquid Avellaneda-Stoikov Market Maker

A market making bot for **Hyperliquid perpetuals** implementing the
**Avellaneda-Stoikov (2008)** model with consistent units, exchange-sourced
position tracking, and real risk controls.

Built and maintained by [Roboquant](https://roboquant.dev) — algorithmic
trading tools and education.

> ⚠️ Market making with leverage can lose money quickly. Run `--dry-run`
> first, then testnet, and only then mainnet with small size. See
> [Safety](#safety).

## Strategy

The bot quotes a bid and ask around a *reservation price* that leans against
current inventory:

```
reservation price   r = s − q·γ·σ²·τ
optimal spread      δ = γ·σ²·τ + (2/γ)·ln(1 + γ/k)
```

- `s` — mid price; `σ²` — EWMA variance of log returns, measured per second
  from real timestamps (robust to irregular sampling) and converted to price
  units.
- `q` — signed inventory in **lots** (multiples of your order size), so one
  lot of inventory skews the reservation price by exactly the risk term
  `γ·σ²·τ`. Long inventory pushes both quotes down (leaning to sell); short
  pushes them up.
- `τ` — a fixed rolling horizon (default 60 s). For a 24/7 perpetual market
  the stationary approximation is used rather than the original model's
  terminal-time countdown.
- `γ`, `k` are in 1/USD so every term is in dollars; with the default
  parameters the raw A-S spread lands *inside* the min/max guard band, and the
  status line reports whenever it gets clamped.

Orders are **post-only (ALO)** — the bot never pays taker fees; a quote that
would cross the book is simply skipped that cycle. Orders are cancelled and
replaced only when the target price drifts beyond a tolerance
(`requote_tolerance_frac` of the half-spread), which preserves queue priority
and respects Hyperliquid's per-address action budget.

## Risk controls

| Control | Behaviour |
|---|---|
| `max_inventory_usd` | At the cap the bot stops adding and quotes **reduce-only** on the unwind side (it never goes silent while holding a position). |
| `session_loss_limit_usd` | If account equity drops this much below the session start, the bot **flattens the position and halts**. |
| Position truth | Read from `fetch_positions` on the exchange — never inferred by accumulating trades. Restarts are safe. |
| Startup / shutdown | Cancels all resting orders on start (clean slate), on Ctrl-C, and on SIGTERM (systemd/docker friendly). Optional `flatten_on_exit`. |
| Error handling | Backoff on network errors; halts after 10 consecutive loop errors or on authentication failure — always through the cleanup path. |

## Quick start

**Want a desktop app?** Download `HyperliquidMM` for your OS from the
[Releases page](../../releases) (macOS `.app` / Windows `.exe`) — a control
panel with settings, start/stop buttons, live status, and logs. Put it in a
folder of its own; it creates `config.json` there and reads `.env` from the
same folder. Or run it from source with `python run_gui.py`.

**Prefer the terminal?** Use the standalone CLI executable. Download the
binary for your OS from the [Releases page](../../releases) (or build both
with `./build_executable.sh`), put it in an empty folder, and run it:

```bash
./hyperliquid-mm            # first run creates config.json with safe defaults
./hyperliquid-mm --dry-run  # quote against live data, no credentials needed
```

Add `HL_WALLET_ADDRESS` / `HL_PRIVATE_KEY` to a `.env` file next to the binary
(see [.env.example](.env.example)) and run again to trade. Executables are
per-platform; tagging a release (`git tag v1.x && git push --tags`) builds
Linux, macOS, and Windows binaries via GitHub Actions.

**With Python** — requires Python 3.9+.

```bash
git clone https://github.com/Italiancrusader/Roboquant-Crypto-Market-Maker-Bot.git
cd Roboquant-Crypto-Market-Maker-Bot
./start_bot.sh --dry-run     # Mac/Linux — or start_bot.bat on Windows
```

The launcher creates a virtualenv, installs dependencies, and generates
`config.json` and `.env` from their examples on first run. Prefer manual setup?

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp config.example.json config.json     # edit to taste; testnet is the default
```

**1. Dry run (no account needed).** Computes and logs quotes against live
market data without placing any orders:

```bash
python run_bot.py --dry-run
```

**2. Testnet.** Create a wallet on <https://app.hyperliquid-testnet.xyz>,
claim mock USDC, create an API wallet, then:

```bash
cp .env.example .env    # fill in HL_WALLET_ADDRESS and HL_PRIVATE_KEY
python run_bot.py
```

**3. Mainnet.** Set `"testnet": false` in `config.json`. The bot asks for
explicit confirmation before trading real funds.

Credentials are read **only** from the environment (or a `.env` file, which is
git-ignored) — never from `config.json`. Use a dedicated
[API wallet](https://app.hyperliquid.xyz/API) so the key cannot withdraw funds.

## Configuration

All keys live in `config.json` (see `config.example.json` for the annotated
defaults).

| Key | Default | Meaning |
|---|---|---|
| `trading.symbol` | `ETH/USDC:USDC` | Any Hyperliquid perpetual (ccxt symbol format). |
| `trading.order_size` | `0.01` | Quote size in base units = one inventory "lot". Notional must exceed Hyperliquid's $10 minimum. |
| `trading.leverage` | `3` | Isolated leverage set at startup. |
| `strategy.gamma` | `0.1` | Risk aversion (1/USD). Higher → wider spread, stronger inventory skew. |
| `strategy.k` | `1.0` | Order-book intensity decay (1/USD). Higher → tighter spread. |
| `strategy.horizon_seconds` | `60` | Rolling horizon τ. |
| `strategy.vol_half_life_seconds` | `120` | EWMA half-life of the volatility estimator. |
| `strategy.warmup_seconds` | `60` | No quoting until the vol estimate has this much data. |
| `strategy.min/max_spread_bps` | `2 / 100` | Guard band on the total spread; clamping is logged. |
| `strategy.requote_tolerance_frac` | `0.25` | Fraction of the half-spread the quote may drift before cancel/replace. |
| `strategy.min_requote_seconds` | `5` | Per-side floor between replacements (protects queue position and action budget). |
| `risk.max_inventory_usd` | `200` | Inventory cap (see table above). |
| `risk.session_loss_limit_usd` | `25` | Flatten-and-halt threshold. |
| `risk.flatten_on_exit` | `false` | Also market-close the position on any shutdown. |

## Repo layout

```
run_bot.py               CLI entry point (--config, --dry-run)
run_gui.py               desktop control panel entry point
hyperliquid_mm/
  strategy.py            A-S math + volatility estimator (pure, unit-tested)
  exchange.py            ccxt Hyperliquid wrapper (all I/O isolated here)
  bot.py                 main loop, order management, risk engine
  config.py              config loading/validation; secrets from env only
  gui.py                 tkinter control panel (settings, credentials, logs)
tests/test_strategy.py   unit tests — run: python -m pytest tests/
assets/                  app icons (Roboquant logo)
build_executable.sh      local binary/app build (PyInstaller)
.github/workflows/       CI: tests + Linux/macOS/Windows executables
```

## Development

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Safety

- Start with `--dry-run`, then testnet, then mainnet with the smallest size
  that clears the $10 notional minimum.
- The loss limit is per session (since process start). Restarting the bot
  resets the baseline equity.
- The bot manages a single symbol per process; run one process per market.
- Never commit `.env` or `config.json` (both are git-ignored).

## License

MIT — see [LICENSE](LICENSE).

## Links

- [Roboquant](https://roboquant.dev)
- [Hyperliquid app](https://app.hyperliquid.xyz) · [testnet](https://app.hyperliquid-testnet.xyz)
- Avellaneda & Stoikov (2008), *High-frequency trading in a limit order book*

## Disclaimer

This software is provided for educational purposes, without warranty of any
kind. Trading cryptocurrency derivatives involves substantial risk of loss.
You are solely responsible for any funds you put at risk.
