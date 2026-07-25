import logging
from datetime import datetime, timezone

import pandas as pd

from quant_tool.database.db_handler import get_connection

logger = logging.getLogger("quant_tool.data_quality")


def check_freshness(symbol: str, max_age_hours: int = 2) -> float:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT MAX(timestamp) AS latest FROM market_data WHERE symbol = ?",
            (symbol,),
        ).fetchone()
        if not row or not row["latest"]:
            return float("inf")

        latest_ts = pd.Timestamp(row["latest"])
        if latest_ts.tzinfo is None:
            latest_ts = latest_ts.tz_localize("UTC")

        age_seconds = (datetime.now(timezone.utc) - latest_ts).total_seconds()
        return max(age_seconds, 0.0)
    except Exception as exc:
        logger.error("Freshness check failed for %s: %s", symbol, exc)
        return float("inf")
    finally:
        conn.close()


def freshness_status(symbol: str, max_age_hours: int = 2) -> str:
    age_sec = check_freshness(symbol, max_age_hours)
    if age_sec == float("inf"):
        return "no_data"
    age_hours = age_sec / 3600
    if age_hours > max_age_hours * 2:
        return "stale"
    if age_hours > max_age_hours:
        return "aging"
    return "fresh"


def detect_gaps(symbol: str) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT timestamp FROM market_data WHERE symbol = ? ORDER BY timestamp ASC",
            (symbol,),
        ).fetchall()

        if len(rows) < 2:
            return []

        timestamps = [pd.Timestamp(r["timestamp"]) for r in rows]
        gaps = []
        for i in range(1, len(timestamps)):
            diff = (timestamps[i] - timestamps[i - 1]).total_seconds()
            if diff > 7200:
                gaps.append({
                    "from": timestamps[i - 1].strftime("%Y-%m-%d %H:%M:%S"),
                    "to": timestamps[i].strftime("%Y-%m-%d %H:%M:%S"),
                    "gap_hours": round(diff / 3600, 2),
                })
        return gaps
    except Exception as exc:
        logger.error("Gap detection failed for %s: %s", symbol, exc)
        return []
    finally:
        conn.close()


def detect_outliers(symbol: str, z_thresh: float = 3.0) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT timestamp, close, volume FROM market_data WHERE symbol = ? ORDER BY timestamp ASC",
            (symbol,),
        ).fetchall()

        if len(rows) < 20:
            return []

        closes = [r["close"] for r in rows]
        mean = sum(closes) / len(closes)
        variance = sum((c - mean) ** 2 for c in closes) / len(closes)
        std = variance ** 0.5

        if std == 0:
            return []

        outliers = []
        for r in rows:
            z = abs((r["close"] - mean) / std)
            if z > z_thresh:
                outliers.append({
                    "timestamp": r["timestamp"],
                    "close": r["close"],
                    "z_score": round(z, 2),
                })
        return outliers
    except Exception as exc:
        logger.error("Outlier detection failed for %s: %s", symbol, exc)
        return []
    finally:
        conn.close()
