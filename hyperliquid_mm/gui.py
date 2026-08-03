"""Desktop control panel for the Hyperliquid A-S market maker.

A thin tkinter shell around MarketMakerBot: edit the core config values,
start/stop the bot (which runs in a background thread), and watch live
status and logs. Credentials stay in .env — the GUI only reports whether
they are present, it never displays or stores keys.
"""

from __future__ import annotations

import json
import logging
import os
import queue
import re
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from .config import (
    ConfigError,
    PRIVATE_KEY_ENV,
    TESTNET_PRIVATE_KEY_ENV,
    TESTNET_WALLET_ADDRESS_ENV,
    WALLET_ADDRESS_ENV,
    load_config,
    write_default_config,
)

ADDR_RE = r"^0x[0-9a-fA-F]{40}$"
KEY_RE = r"^(0x)?[0-9a-fA-F]{64}$"

REFRESH_MS = 250
STATUS_FIELDS = [
    ("network", "Network"),
    ("state", "State"),
    ("mid", "Mid price"),
    ("spread", "Spread"),
    ("position", "Position"),
    ("equity", "Equity"),
    ("pnl", "Session PnL"),
    ("fills", "Fill events"),
]
# (config section, key, label, parser)
EDITABLE = [
    ("trading", "order_size", "Order size (base units)", float),
    ("trading", "leverage", "Leverage", int),
    ("strategy", "gamma", "Gamma (risk aversion)", float),
    ("strategy", "k", "k (book intensity)", float),
    ("risk", "max_inventory_usd", "Max inventory (USD)", float),
    ("risk", "session_loss_limit_usd", "Session loss limit (USD)", float),
]


class QueueLogHandler(logging.Handler):
    """Forwards log records to a thread-safe queue for the UI to drain."""

    def __init__(self, q: queue.Queue):
        super().__init__()
        self.q = q
        self.setFormatter(logging.Formatter("%(asctime)s %(levelname)-7s %(message)s",
                                            datefmt="%H:%M:%S"))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.q.put_nowait(self.format(record))
        except queue.Full:
            pass


class BotGui:
    def __init__(self, base_dir: str, smoke_test: bool = False):
        self.base_dir = base_dir
        self.config_path = os.path.join(base_dir, "config.json")
        if not os.path.exists(self.config_path):
            write_default_config(self.config_path)

        self.bot = None
        self.bot_thread = None
        self.log_queue: queue.Queue = queue.Queue(maxsize=5000)

        handler = QueueLogHandler(self.log_queue)
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(logging.INFO)
        logfile = os.path.join(base_dir, "market_maker.log")
        file_handler = logging.FileHandler(logfile)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)-7s %(message)s"))
        logging.getLogger().addHandler(file_handler)

        self.root = tk.Tk()
        self.root.title("Hyperliquid A-S Market Maker")
        self.root.geometry("880x640")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_layout()
        self._load_config_into_form()
        self._on_network_toggle()  # populates credentials fields + symbol list
        self.root.after(REFRESH_MS, self._tick)
        if smoke_test:
            self.root.after(2000, self.root.destroy)

    # ------------------------------------------------------------------ UI
    def _build_layout(self) -> None:
        root = self.root
        root.columnconfigure(0, weight=0)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(1, weight=1)

        # Left panel: settings + controls
        left = ttk.Frame(root, padding=10)
        left.grid(row=0, column=0, rowspan=2, sticky="nsw")

        ttk.Label(left, text="Settings", font=("", 13, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))

        r = 1
        # Symbol: dropdown fetched live from Hyperliquid (editable as fallback)
        ttk.Label(left, text="Symbol").grid(row=r, column=0, sticky="w", pady=2)
        self.symbol_var = tk.StringVar()
        self.symbol_box = ttk.Combobox(left, textvariable=self.symbol_var, width=15)
        self.symbol_box.grid(row=r, column=1, sticky="w", padx=(8, 0), pady=2)
        self.symbol_box.set("loading markets...")
        r += 1

        self.form_vars = {}
        for section, key, label, _parser in EDITABLE:
            ttk.Label(left, text=label).grid(row=r, column=0, sticky="w", pady=2)
            var = tk.StringVar()
            self.form_vars[(section, key)] = var
            ttk.Entry(left, textvariable=var, width=16).grid(
                row=r, column=1, sticky="w", padx=(8, 0), pady=2)
            r += 1

        self.testnet_var = tk.BooleanVar(value=True)
        self.testnet_var.trace_add("write", lambda *_: self._on_network_toggle())
        ttk.Checkbutton(left, text="Testnet", variable=self.testnet_var).grid(
            row=r, column=0, sticky="w", pady=(4, 0)); r += 1
        self.dry_run_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(left, text="Dry run (no orders)", variable=self.dry_run_var).grid(
            row=r, column=0, columnspan=2, sticky="w"); r += 1

        ttk.Button(left, text="Save settings", command=self._save_config).grid(
            row=r, column=0, columnspan=2, sticky="we", pady=(8, 2)); r += 1

        # Credentials — saved to .env next to the app, never into the binary
        # or config.json. The key field is write-only: it is never pre-filled.
        ttk.Label(left, text="Credentials", font=("", 13, "bold")).grid(
            row=r, column=0, columnspan=2, sticky="w", pady=(12, 4)); r += 1
        ttk.Label(left, text="Wallet address").grid(row=r, column=0, sticky="w")
        self.addr_var = tk.StringVar()
        ttk.Entry(left, textvariable=self.addr_var, width=16).grid(
            row=r, column=1, sticky="w", padx=(8, 0)); r += 1
        ttk.Label(left, text="API wallet key").grid(row=r, column=0, sticky="w")
        self.key_var = tk.StringVar()
        ttk.Entry(left, textvariable=self.key_var, width=16, show="•").grid(
            row=r, column=1, sticky="w", padx=(8, 0)); r += 1
        ttk.Button(left, text="Save credentials", command=self._save_credentials).grid(
            row=r, column=0, columnspan=2, sticky="we", pady=(4, 2)); r += 1

        self.start_btn = ttk.Button(left, text="▶  Start bot", command=self._start)
        self.start_btn.grid(row=r, column=0, columnspan=2, sticky="we", pady=2); r += 1
        self.stop_btn = ttk.Button(left, text="■  Stop bot", command=self._stop,
                                   state="disabled")
        self.stop_btn.grid(row=r, column=0, columnspan=2, sticky="we", pady=2); r += 1

        self.creds_label = ttk.Label(left, text="", wraplength=210, foreground="gray")
        self.creds_label.grid(row=r, column=0, columnspan=2, sticky="w", pady=(10, 0)); r += 1
        ttk.Button(left, text="Open data folder", command=self._open_folder).grid(
            row=r, column=0, columnspan=2, sticky="we", pady=(6, 0))

        # Right top: status grid
        status = ttk.LabelFrame(root, text="Status", padding=10)
        status.grid(row=0, column=1, sticky="new", padx=10, pady=(10, 4))
        self.status_vars = {}
        for i, (key, label) in enumerate(STATUS_FIELDS):
            ttk.Label(status, text=label + ":").grid(
                row=i // 4, column=(i % 4) * 2, sticky="w", padx=(0, 4), pady=2)
            var = tk.StringVar(value="—")
            self.status_vars[key] = var
            ttk.Label(status, textvariable=var, font=("", 12, "bold")).grid(
                row=i // 4, column=(i % 4) * 2 + 1, sticky="w", padx=(0, 16), pady=2)

        # Right bottom: log pane
        logf = ttk.LabelFrame(root, text="Log", padding=6)
        logf.grid(row=1, column=1, sticky="nsew", padx=10, pady=(4, 10))
        logf.rowconfigure(0, weight=1)
        logf.columnconfigure(0, weight=1)
        self.log_text = tk.Text(logf, height=18, state="disabled", wrap="none",
                                font=("Menlo", 10))
        self.log_text.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(logf, command=self.log_text.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scroll.set)

    # ------------------------------------------------------------ config io
    def _read_config_file(self) -> dict:
        with open(self.config_path) as f:
            return json.load(f)

    def _load_config_into_form(self) -> None:
        try:
            raw = self._read_config_file()
        except (OSError, json.JSONDecodeError) as e:
            messagebox.showerror("Config error", f"Cannot read config.json: {e}")
            return
        for section, key, _label, _parser in EDITABLE:
            val = raw.get(section, {}).get(key, "")
            self.form_vars[(section, key)].set(str(val))
        self.symbol_var.set(str(raw.get("trading", {}).get("symbol", "ETH/USDC:USDC")))
        self.testnet_var.set(bool(raw.get("exchange", {}).get("testnet", True)))

    def _save_config(self) -> bool:
        try:
            raw = self._read_config_file()
        except (OSError, json.JSONDecodeError):
            raw = {}
        for section, key, label, parser in EDITABLE:
            text = self.form_vars[(section, key)].get().strip()
            try:
                raw.setdefault(section, {})[key] = parser(text)
            except ValueError:
                messagebox.showerror("Invalid value", f"{label}: {text!r} is not valid")
                return False
        symbol = self.symbol_var.get().strip()
        if not symbol or symbol == "loading markets...":
            messagebox.showerror("Invalid value", "Choose a trading symbol first")
            return False
        raw.setdefault("trading", {})["symbol"] = symbol
        raw.setdefault("exchange", {})["testnet"] = bool(self.testnet_var.get())
        with open(self.config_path, "w") as f:
            json.dump(raw, f, indent=2)
            f.write("\n")
        self._refresh_credentials_banner()
        logging.getLogger(__name__).info("Settings saved to %s", self.config_path)
        return True

    # -------------------------------------------------------- credentials
    def _cred_env_names(self) -> tuple:
        if self.testnet_var.get():
            return TESTNET_WALLET_ADDRESS_ENV, TESTNET_PRIVATE_KEY_ENV
        return WALLET_ADDRESS_ENV, PRIVATE_KEY_ENV

    def _on_network_toggle(self) -> None:
        addr_env, _ = self._cred_env_names()
        self.addr_var.set(os.environ.get(addr_env, ""))
        self.key_var.set("")  # keys are write-only in the UI
        self._refresh_credentials_banner()
        self._fetch_symbols_async()

    # ------------------------------------------------------------- symbols
    def _fetch_symbols_async(self) -> None:
        """Populate the symbol dropdown from the exchange, off the UI thread."""
        testnet = bool(self.testnet_var.get())
        if getattr(self, "_symbols_fetched_for", None) == testnet:
            return  # already fetched (or fetching) for this network
        self._symbols_fetched_for = testnet

        def fetch() -> None:
            try:
                import ccxt  # deferred: slow import
                ex = ccxt.hyperliquid({"enableRateLimit": True})
                if testnet:
                    ex.set_sandbox_mode(True)
                ex.load_markets()
                symbols = sorted(
                    s for s, m in ex.markets.items()
                    if m.get("swap") and m.get("active") is not False
                )
            except Exception as e:
                logging.getLogger(__name__).warning("Could not fetch markets: %s", e)
                self._symbols_fetched_for = None  # allow retry on next toggle
                return
            def apply() -> None:
                if bool(self.testnet_var.get()) != testnet:
                    return  # toggle changed while fetching; a newer fetch is coming
                current = self.symbol_var.get()
                self.symbol_box["values"] = symbols
                if current in ("", "loading markets...") or current not in symbols:
                    self.symbol_var.set(
                        "ETH/USDC:USDC" if "ETH/USDC:USDC" in symbols
                        else (symbols[0] if symbols else current))
                logging.getLogger(__name__).info(
                    "Loaded %d %s markets from Hyperliquid",
                    len(symbols), "testnet" if testnet else "mainnet")
            try:
                self.root.after(0, apply)
            except tk.TclError:
                pass  # window closed while fetching

        threading.Thread(target=fetch, daemon=True, name="fetch-symbols").start()

    def _save_credentials(self) -> None:
        addr_env, key_env = self._cred_env_names()
        addr = self.addr_var.get().strip()
        key = self.key_var.get().strip()

        if addr and not re.fullmatch(ADDR_RE, addr):
            messagebox.showerror(
                "Invalid address", "Wallet address must look like 0x + 40 hex characters.")
            return
        if key and not re.fullmatch(KEY_RE, key):
            messagebox.showerror(
                "Invalid key", "Private key must be 64 hex characters (0x prefix optional).")
            return
        if not key and not os.environ.get(key_env):
            messagebox.showerror(
                "Missing key",
                "Enter the API wallet private key (create one under "
                "More → API on the Hyperliquid app).")
            return
        if key and not key.startswith("0x"):
            key = "0x" + key

        updates = {addr_env: addr}
        if key:
            updates[key_env] = key
        self._write_env_file(updates)
        for name, value in updates.items():
            os.environ[name] = value
        self.key_var.set("")
        self._refresh_credentials_banner()
        logging.getLogger(__name__).info(
            "Credentials saved to %s (%s)", self._env_path(),
            "testnet" if self.testnet_var.get() else "mainnet")

    def _env_path(self) -> str:
        return os.path.join(self.base_dir, ".env")

    def _write_env_file(self, updates: dict) -> None:
        """Update variables in .env, preserving unrelated lines. chmod 600."""
        path = self._env_path()
        lines = []
        if os.path.exists(path):
            with open(path) as f:
                lines = f.read().splitlines()
        remaining = dict(updates)
        out = []
        for line in lines:
            name = line.split("=", 1)[0].strip() if "=" in line else None
            if name in remaining:
                out.append(f"{name}={remaining.pop(name)}")
            else:
                out.append(line)
        out.extend(f"{k}={v}" for k, v in remaining.items())
        with open(path, "w") as f:
            f.write("\n".join(out) + "\n")
        os.chmod(path, 0o600)

    def _refresh_credentials_banner(self) -> None:
        env_var = TESTNET_PRIVATE_KEY_ENV if self.testnet_var.get() else PRIVATE_KEY_ENV
        if os.environ.get(env_var) or os.environ.get(PRIVATE_KEY_ENV):
            self.creds_label.config(
                text="✓ Credentials found in .env", foreground="green")
        else:
            self.creds_label.config(
                text="No credentials in .env — live trading unavailable. "
                     "Dry run works without them.",
                foreground="#b36b00")

    # ------------------------------------------------------------- control
    def _start(self) -> None:
        if self.bot_thread and self.bot_thread.is_alive():
            return
        if not self._save_config():
            return
        dry_run = bool(self.dry_run_var.get())
        try:
            cfg = load_config(self.config_path, require_keys=not dry_run)
        except ConfigError as e:
            messagebox.showerror("Cannot start", str(e))
            return
        if not cfg.testnet and not dry_run:
            if not messagebox.askyesno(
                "Real funds",
                "MAINNET mode: this bot will trade with real funds.\n\nContinue?",
            ):
                return

        from .bot import MarketMakerBot  # deferred: ccxt import is slow

        def run() -> None:
            try:
                self.bot = MarketMakerBot(cfg, dry_run=dry_run)
                self.bot.run()
            except Exception as e:  # surfaced via log pane
                logging.getLogger(__name__).error("Bot crashed: %s", e)
            finally:
                self.bot = None

        self.bot_thread = threading.Thread(target=run, daemon=True, name="bot")
        self.bot_thread.start()
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")

    def _stop(self) -> None:
        if self.bot is not None:
            self.bot.stop("stopped from control panel")
        self.stop_btn.config(state="disabled")

    def _on_close(self) -> None:
        if self.bot_thread and self.bot_thread.is_alive():
            if not messagebox.askyesno(
                "Bot is running",
                "Stop the bot and quit? Open orders will be cancelled.",
            ):
                return
            self._stop()
            self.bot_thread.join(timeout=15)
        self.root.destroy()

    def _open_folder(self) -> None:
        if sys.platform == "darwin":
            os.system(f'open "{self.base_dir}"')
        elif sys.platform == "win32":
            os.startfile(self.base_dir)  # type: ignore[attr-defined]
        else:
            os.system(f'xdg-open "{self.base_dir}"')

    # ------------------------------------------------------------- refresh
    def _tick(self) -> None:
        self._drain_logs()
        self._update_status()
        self.root.after(REFRESH_MS, self._tick)

    def _drain_logs(self) -> None:
        lines = []
        while True:
            try:
                lines.append(self.log_queue.get_nowait())
            except queue.Empty:
                break
        if lines:
            self.log_text.configure(state="normal")
            self.log_text.insert("end", "\n".join(lines) + "\n")
            # keep the pane bounded
            if float(self.log_text.index("end-1c").split(".")[0]) > 2000:
                self.log_text.delete("1.0", "500.0")
            self.log_text.see("end")
            self.log_text.configure(state="disabled")

    def _update_status(self) -> None:
        sv = self.status_vars
        running = self.bot_thread is not None and self.bot_thread.is_alive()
        bot = self.bot
        if not running or bot is None:
            sv["state"].set("stopped")
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            if bot is None and not running:
                for key in ("mid", "spread", "position", "pnl"):
                    pass  # keep last values visible after stop
            return
        cfg = bot.cfg
        sv["network"].set(("TESTNET" if cfg.testnet else "MAINNET")
                          + (" · dry-run" if bot.dry_run else ""))
        sv["state"].set("halted: " + bot.halt_reason if bot.halted else "running")
        vol = bot.vol
        if vol.sample_count and vol._last_mid:
            sv["mid"].set(f"{vol._last_mid:,.2f}")
        pos = bot.position.size_base
        sv["position"].set(f"{pos:+.4f}")
        sv["equity"].set(f"${bot.equity:,.2f}" if bot.equity else "—")
        if bot.equity_start is not None:
            sv["pnl"].set(f"${bot.equity - bot.equity_start:+,.2f}")
        sv["fills"].set(str(bot.session_fills))
        if vol.is_warm(cfg.warmup_seconds) and vol._last_mid:
            from .strategy import compute_quotes
            q = compute_quotes(vol._last_mid, pos / cfg.order_size,
                               vol.variance_per_second, bot.params)
            sv["spread"].set(f"{q.total_spread / vol._last_mid * 10_000:.1f} bps")
        else:
            sv["spread"].set("warming up")

    def run(self) -> None:
        self.root.mainloop()


def main() -> int:
    smoke = "--smoke-test" in sys.argv
    frozen = getattr(sys, "frozen", False)
    base_dir = os.path.dirname(sys.executable) if frozen else os.getcwd()
    # macOS .app bundles live in Contents/MacOS three levels deep; keep user
    # files next to the .app itself, not inside it.
    if frozen and sys.platform == "darwin" and "/Contents/MacOS" in sys.executable:
        base_dir = os.path.dirname(sys.executable.split("/Contents/MacOS")[0])

    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(base_dir, ".env"))
    except ImportError:
        pass

    gui = BotGui(base_dir, smoke_test=smoke)
    gui.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
