import time
import logging
from datetime import datetime, timezone

import ccxt

from quant_tool.config import SYMBOLS, TIMEFRAMES
from quant_tool.database.db_handler import upsert_market_data

logger = logging.getLogger("quant_tool.crypto_feed")

EXCHANGE_SETTINGS = {
    "binance": {"rateLimit": 1200, "enableRateLimit": True},
    "coinbase": {"rateLimit": 1000, "enableRateLimit": True},
}


def fetch_ohlcv(symbol: str, exchange_id: str = "binance", timeframe: str = "1h", limit: int = 200):
    exchange_class = getattr(ccxt, exchange_id, None)
    if exchange_class is None:
        logger.error("Unsupported exchange: %s", exchange_id)
        return []

    exchange = exchange_class(EXCHANGE_SETTINGS.get(exchange_id, {}))
    max_retries = 5

    for attempt in range(1, max_retries + 1):
        try:
            raw = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            rows = []
            for bar in raw:
                rows.append({
                    "timestamp": datetime.fromtimestamp(bar[0] / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                    "symbol": symbol,
                    "open": float(bar[1]),
                    "high": float(bar[2]),
                    "low": float(bar[3]),
                    "close": float(bar[4]),
                    "volume": float(bar[5]),
                    "asset_class": "crypto",
                })
            logger.info("Fetched %d bars for %s from %s", len(rows), symbol, exchange_id)
            return rows

        except ccxt.RateLimitExceeded as e:
            wait = min(60 * attempt, 300)
            logger.warning("Rate limited on %s (attempt %d/%d). Retrying in %ds...", exchange_id, attempt, max_retries, wait)
            time.sleep(wait)

        except ccxt.NetworkError as e:
            wait = min(30 * attempt, 120)
            logger.warning("Network error on %s (attempt %d/%d): %s. Retrying in %ds...", exchange_id, attempt, max_retries, e, wait)
            time.sleep(wait)

        except Exception as e:
            logger.error("Unhandled error fetching %s from %s: %s", symbol, exchange_id, e)
            return []

    logger.error("Exhausted retries for %s on %s", symbol, exchange_id)
    return []


def fetch_all_crypto():
    all_rows = []
    timeframe = TIMEFRAMES.get("crypto", "1h")
    for symbol in SYMBOLS.get("crypto", []):
        rows = fetch_ohlcv(symbol, exchange_id="binance", timeframe=timeframe)
        all_rows.extend(rows)
    if all_rows:
        upsert_market_data(all_rows)
    return all_rows
