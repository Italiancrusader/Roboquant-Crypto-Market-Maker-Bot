"""Historical top-of-book data from Hyperliquid's S3 archive.

Hyperliquid publishes L2 book snapshots to a **requester-pays** bucket:

    s3://hyperliquid-archive/market_data/{YYYYMMDD}/{H}/l2Book/{COIN}.lz4

Downloading requires configured AWS credentials and bills transfer costs
(~$0.09/GB, i.e. cents per hour-file) to YOUR AWS account. Parsed ticks are
cached locally as CSV so each hour is paid for once.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import tempfile
from typing import List, Tuple

logger = logging.getLogger(__name__)

Tick = Tuple[int, float, float]  # ts_ms, best_bid, best_ask

BUCKET = "hyperliquid-archive"


def _cache_path(cache_dir: str, coin: str, date: str, hour: int) -> str:
    return os.path.join(cache_dir, f"l1_{coin}_{date}_{hour:02d}.csv")


def _parse_snapshot_line(line: str) -> Tick | None:
    """Extract (ts_ms, best_bid, best_ask) from one archive JSON line."""
    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        return None
    # Formats have varied over time; walk down defensively.
    data = obj.get("raw", obj)
    if isinstance(data, dict) and "data" in data:
        data = data["data"]
    levels = data.get("levels") if isinstance(data, dict) else None
    if not levels or len(levels) < 2 or not levels[0] or not levels[1]:
        return None
    ts = data.get("time") or obj.get("time")
    if isinstance(ts, str):
        from datetime import datetime, timezone
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            ts = int(dt.timestamp() * 1000)
        except ValueError:
            return None
    if not isinstance(ts, (int, float)):
        return None
    try:
        best_bid = float(levels[0][0]["px"])
        best_ask = float(levels[1][0]["px"])
    except (KeyError, TypeError, ValueError, IndexError):
        return None
    return int(ts), best_bid, best_ask


def fetch_l1_hour(
    coin: str, date: str, hour: int, cache_dir: str = "data"
) -> List[Tick]:
    """Download + parse one hour of book snapshots (cached after first use).

    ``coin`` is the bare asset name (e.g. "ETH"), ``date`` is YYYYMMDD.
    """
    os.makedirs(cache_dir, exist_ok=True)
    cache = _cache_path(cache_dir, coin, date, hour)
    if os.path.exists(cache):
        ticks: List[Tick] = []
        with open(cache) as f:
            next(f)  # header
            for row in f:
                ts, bid, ask = row.strip().split(",")
                ticks.append((int(ts), float(bid), float(ask)))
        return ticks

    try:
        import lz4.frame
    except ImportError:
        raise RuntimeError("The 'lz4' package is required: pip install lz4")

    key = f"market_data/{date}/{hour}/l2Book/{coin}.lz4"
    with tempfile.NamedTemporaryFile(suffix=".lz4", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        logger.info("Downloading s3://%s/%s (requester pays)", BUCKET, key)
        result = subprocess.run(
            ["aws", "s3", "cp", f"s3://{BUCKET}/{key}", tmp_path,
             "--request-payer", "requester"],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"S3 download failed for {key}: {result.stderr.strip()[:300]}"
            )
        ticks = []
        with lz4.frame.open(tmp_path, "rt") as f:
            for line in f:
                tick = _parse_snapshot_line(line)
                if tick is not None:
                    ticks.append(tick)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    if not ticks:
        raise RuntimeError(f"No parseable snapshots in {key}")
    ticks.sort(key=lambda t: t[0])
    with open(cache, "w") as f:
        f.write("ts_ms,best_bid,best_ask\n")
        for ts, bid, ask in ticks:
            f.write(f"{ts},{bid},{ask}\n")
    logger.info("Cached %d ticks -> %s", len(ticks), cache)
    return ticks


def fetch_l1_range(
    coin: str, date: str, start_hour: int, hours: int, cache_dir: str = "data"
) -> List[Tick]:
    """Fetch consecutive hours (all within one YYYYMMDD date)."""
    out: List[Tick] = []
    for h in range(start_hour, start_hour + hours):
        out.extend(fetch_l1_hour(coin, date, h, cache_dir))
    return out
