import time
import logging
from datetime import datetime, timezone

import yfinance as yf
import requests

from quant_tool.config import SYMBOLS, TIMEFRAMES, FINNHUB_API_KEY
from quant_tool.database.db_handler import upsert_market_data

logger = logging.getLogger("quant_tool.stock_feed")


def fetch_yfinance(symbol: str, period: str = "2mo", interval: str = "1d"):
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            if df.empty:
                logger.warning("Empty yfinance response for %s", symbol)
                return []

            rows = []
            for idx, row in df.iterrows():
                ts = idx
                if hasattr(idx, "tzinfo") and idx.tzinfo is not None:
                    ts = idx.tz_convert("UTC")
                rows.append({
                    "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
                    "symbol": symbol,
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": float(row["Volume"]),
                    "asset_class": "stock" if "=X" not in symbol else "forex",
                })
            logger.info("Fetched %d bars for %s from yfinance", len(rows), symbol)
            return rows

        except Exception as e:
            wait = min(10 * attempt, 60)
            logger.warning("yfinance error for %s (attempt %d/%d): %s. Retrying in %ds...", symbol, attempt, max_retries, e, wait)
            time.sleep(wait)

    logger.error("Exhausted retries for %s via yfinance", symbol)
    return []


def fetch_finnhub_candle(symbol: str, resolution: str = "60"):
    if not FINNHUB_API_KEY:
        logger.warning("FINNHUB_API_KEY not set — skipping Finnhub fetch for %s", symbol)
        return []

    max_retries = 3
    url = "https://finnhub.io/api/v1/stock/candle"
    now = int(datetime.now(timezone.utc).timestamp())
    start = now - 86400 * 7

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(
                url,
                params={
                    "symbol": symbol.replace("=X", ""),
                    "resolution": resolution,
                    "from": start,
                    "to": now,
                    "token": FINNHUB_API_KEY,
                },
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()

            if data.get("s") != "ok" or "c" not in data:
                logger.warning("Finnhub returned non-ok status for %s", symbol)
                return []

            rows = []
            for i in range(len(data["t"])):
                rows.append({
                    "timestamp": datetime.fromtimestamp(data["t"][i], tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                    "symbol": symbol,
                    "open": float(data["o"][i]),
                    "high": float(data["h"][i]),
                    "low": float(data["l"][i]),
                    "close": float(data["c"][i]),
                    "volume": float(data["v"][i]),
                    "asset_class": "stock" if "=X" not in symbol else "forex",
                })
            logger.info("Fetched %d bars for %s from Finnhub", len(rows), symbol)
            return rows

        except requests.exceptions.HTTPError as e:
            if resp.status_code == 429:
                wait = min(60 * attempt, 300)
                logger.warning("Finnhub rate limited (attempt %d/%d). Retrying in %ds...", attempt, max_retries, wait)
                time.sleep(wait)
            else:
                logger.error("Finnhub HTTP error for %s: %s", symbol, e)
                return []

        except requests.exceptions.RequestException as e:
            wait = min(15 * attempt, 60)
            logger.warning("Finnhub network error (attempt %d/%d): %s. Retrying in %ds...", attempt, max_retries, e, wait)
            time.sleep(wait)

        except Exception as e:
            logger.error("Unhandled Finnhub error for %s: %s", symbol, e)
            return []

    logger.error("Exhausted retries for %s via Finnhub", symbol)
    return []


def fetch_all_stocks_and_forex():
    all_rows = []
    for symbol in SYMBOLS.get("stock", []):
        rows = fetch_yfinance(symbol, period="2mo", interval=TIMEFRAMES.get("stock", "1d"))
        all_rows.extend(rows)
        time.sleep(1)

    for symbol in SYMBOLS.get("forex", []):
        rows = fetch_yfinance(symbol, period="2mo", interval=TIMEFRAMES.get("forex", "1d"))
        all_rows.extend(rows)
        time.sleep(1)

    if FINNHUB_API_KEY:
        for symbol in SYMBOLS.get("stock", []):
            rows = fetch_finnhub_candle(symbol, resolution="60")
            all_rows.extend(rows)
            time.sleep(1)

    if all_rows:
        upsert_market_data(all_rows)
    return all_rows
