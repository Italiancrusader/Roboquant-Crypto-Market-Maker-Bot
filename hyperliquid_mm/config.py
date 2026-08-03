"""Configuration loading and validation.

Secrets (wallet address, API private key) come exclusively from environment
variables — never from config.json — so the config file is always safe to
commit or share.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Optional

WALLET_ADDRESS_ENV = "HL_WALLET_ADDRESS"
PRIVATE_KEY_ENV = "HL_PRIVATE_KEY"
# When testnet is enabled these take precedence, so mainnet and testnet
# credentials can live side by side in the same .env file.
TESTNET_WALLET_ADDRESS_ENV = "HL_TESTNET_WALLET_ADDRESS"
TESTNET_PRIVATE_KEY_ENV = "HL_TESTNET_PRIVATE_KEY"


class ConfigError(Exception):
    pass


# Written to config.json on first run when no config file exists yet
# (used by the packaged executable, where config.example.json isn't around).
DEFAULT_CONFIG = {
    "exchange": {"testnet": True},
    "trading": {"symbol": "ETH/USDC:USDC", "leverage": 3, "order_size": 0.01},
    "strategy": {
        "gamma": 0.1,
        "k": 1.0,
        "horizon_seconds": 60,
        "vol_half_life_seconds": 120,
        "warmup_seconds": 60,
        "min_spread_bps": 2.0,
        "max_spread_bps": 100.0,
        "update_interval_seconds": 1.0,
        "requote_tolerance_frac": 0.25,
        "min_requote_seconds": 5.0,
    },
    "risk": {
        "max_inventory_usd": 50,
        "session_loss_limit_usd": 5,
        "flatten_on_exit": True,
        "position_refresh_seconds": 10,
        "open_orders_refresh_seconds": 5,
    },
}


def write_default_config(path: str) -> None:
    with open(path, "w") as f:
        json.dump(DEFAULT_CONFIG, f, indent=2)
        f.write("\n")


@dataclass(frozen=True)
class BotConfig:
    # exchange
    testnet: bool
    wallet_address: Optional[str]
    private_key: Optional[str]
    # trading
    symbol: str
    leverage: int
    order_size: float  # base units per quote (one "lot")
    # strategy
    gamma: float
    k: float
    horizon_seconds: float
    vol_half_life_seconds: float
    warmup_seconds: float
    min_spread_bps: float
    max_spread_bps: float
    update_interval_seconds: float
    requote_tolerance_frac: float  # fraction of half-spread the quote may drift
    min_requote_seconds: float  # per-side floor between cancel/replace cycles
    # Trend gate: stand down (unwind-only) when the |move| over the lookback
    # exceeds trend_gate_z times what diffusion would produce. 0 disables.
    trend_gate_hours: float
    trend_gate_z: float
    # risk
    max_inventory_usd: float
    session_loss_limit_usd: float
    flatten_on_exit: bool
    position_refresh_seconds: float
    open_orders_refresh_seconds: float


def _require(section: dict, key: str, section_name: str):
    if key not in section:
        raise ConfigError(f"Missing required config key: {section_name}.{key}")
    return section[key]


def load_config(path: str, require_keys: bool = True) -> BotConfig:
    try:
        with open(path, "r") as f:
            raw = json.load(f)
    except FileNotFoundError:
        raise ConfigError(
            f"Config file not found: {path}. "
            "Copy config.example.json to config.json and edit it."
        )
    except json.JSONDecodeError as e:
        raise ConfigError(f"Config file {path} is not valid JSON: {e}")

    exchange = raw.get("exchange", {})
    trading = raw.get("trading", {})
    strategy = raw.get("strategy", {})
    risk = raw.get("risk", {})

    testnet = bool(exchange.get("testnet", True))
    wallet_address = os.environ.get(WALLET_ADDRESS_ENV) or None
    private_key = os.environ.get(PRIVATE_KEY_ENV) or None
    if testnet:
        wallet_address = os.environ.get(TESTNET_WALLET_ADDRESS_ENV) or wallet_address
        private_key = os.environ.get(TESTNET_PRIVATE_KEY_ENV) or private_key
    if wallet_address:
        wallet_address = wallet_address.strip()
    if private_key:
        private_key = private_key.strip()
    if require_keys:
        if not wallet_address or not private_key:
            raise ConfigError(
                f"Set {WALLET_ADDRESS_ENV} and {PRIVATE_KEY_ENV} in the environment "
                "(or in a .env file next to the bot). Never put keys in config.json. "
                "Use --dry-run to run without credentials."
            )

    cfg = BotConfig(
        testnet=testnet,
        wallet_address=wallet_address,
        private_key=private_key,
        symbol=str(_require(trading, "symbol", "trading")),
        leverage=int(trading.get("leverage", 1)),
        order_size=float(_require(trading, "order_size", "trading")),
        gamma=float(strategy.get("gamma", 0.1)),
        k=float(strategy.get("k", 1.0)),
        horizon_seconds=float(strategy.get("horizon_seconds", 60.0)),
        vol_half_life_seconds=float(strategy.get("vol_half_life_seconds", 120.0)),
        warmup_seconds=float(strategy.get("warmup_seconds", 60.0)),
        min_spread_bps=float(strategy.get("min_spread_bps", 2.0)),
        max_spread_bps=float(strategy.get("max_spread_bps", 100.0)),
        update_interval_seconds=float(strategy.get("update_interval_seconds", 1.0)),
        requote_tolerance_frac=float(strategy.get("requote_tolerance_frac", 0.25)),
        min_requote_seconds=float(strategy.get("min_requote_seconds", 5.0)),
        trend_gate_hours=float(strategy.get("trend_gate_hours", 0.0)),
        trend_gate_z=float(strategy.get("trend_gate_z", 1.5)),
        max_inventory_usd=float(risk.get("max_inventory_usd", 50.0)),
        session_loss_limit_usd=float(risk.get("session_loss_limit_usd", 5.0)),
        flatten_on_exit=bool(risk.get("flatten_on_exit", True)),
        position_refresh_seconds=float(risk.get("position_refresh_seconds", 10.0)),
        open_orders_refresh_seconds=float(risk.get("open_orders_refresh_seconds", 5.0)),
    )

    _validate(cfg)
    return cfg


def _validate(cfg: BotConfig) -> None:
    problems = []
    if cfg.order_size <= 0:
        problems.append("trading.order_size must be positive")
    if cfg.leverage < 1:
        problems.append("trading.leverage must be >= 1")
    if cfg.gamma <= 0 or cfg.k <= 0:
        problems.append("strategy.gamma and strategy.k must be positive")
    if cfg.horizon_seconds <= 0:
        problems.append("strategy.horizon_seconds must be positive")
    if not 0 < cfg.min_spread_bps <= cfg.max_spread_bps:
        problems.append("require 0 < min_spread_bps <= max_spread_bps")
    if cfg.update_interval_seconds < 0.5:
        problems.append("strategy.update_interval_seconds must be >= 0.5")
    if cfg.max_inventory_usd <= 0:
        problems.append("risk.max_inventory_usd must be positive")
    if cfg.session_loss_limit_usd <= 0:
        problems.append("risk.session_loss_limit_usd must be positive")
    if problems:
        raise ConfigError("Invalid config: " + "; ".join(problems))
