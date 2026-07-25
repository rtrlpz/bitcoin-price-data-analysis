import time
import logging
from datetime import datetime, timezone

import schedule

from quant_tool.config import SYMBOLS, FETCH_INTERVAL_MINUTES
from quant_tool.database.db_handler import (
    init_db,
    get_connection,
    record_pipeline_health,
)
from quant_tool.fetchers.crypto_feed import fetch_all_crypto
from quant_tool.fetchers.stock_feed import fetch_all_stocks_and_forex
from quant_tool.fetchers.sentiment_feed import fetch_all_sentiment
from quant_tool.analytics.signals import evaluate_all_symbols
from quant_tool.analytics.backtester import PaperTrader
from quant_tool.notifications.telegram import send_error_alert

logger = logging.getLogger("quant_tool.scheduler")


def _has_data() -> bool:
    conn = get_connection()
    try:
        row = conn.execute("SELECT COUNT(*) AS cnt FROM market_data").fetchone()
        return row["cnt"] > 0
    except Exception:
        return False
    finally:
        conn.close()


def run_backfill():
    logger.info("Backfilling data — empty database detected")
    for fetcher, name in [
        (fetch_all_crypto, "crypto"),
        (fetch_all_stocks_and_forex, "stocks_forex"),
    ]:
        try:
            t0 = time.time()
            rows = fetcher()
            duration = int((time.time() - t0) * 1000)
            record_pipeline_health(f"backfill_{name}", "ok", len(rows), duration_ms=duration)
            logger.info("Backfill %s: %d rows in %dms", name, len(rows), duration)
        except Exception as e:
            record_pipeline_health(f"backfill_{name}", "error", error_msg=str(e))
            logger.error("Backfill %s failed: %s", name, e)
    fetch_all_sentiment()
    evaluate_all_symbols()
    logger.info("Backfill complete")


def run_pipeline():
    logger.info("Pipeline run starting at %s", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))

    # Crypto
    try:
        t0 = time.time()
        rows = fetch_all_crypto()
        duration = int((time.time() - t0) * 1000)
        record_pipeline_health("crypto", "ok", len(rows), duration_ms=duration)
    except Exception as e:
        record_pipeline_health("crypto", "error", error_msg=str(e))
        send_error_alert(f"Crypto fetch failed: {e}")

    # Stocks & Forex
    try:
        t0 = time.time()
        rows = fetch_all_stocks_and_forex()
        duration = int((time.time() - t0) * 1000)
        record_pipeline_health("stocks_forex", "ok", len(rows), duration_ms=duration)
    except Exception as e:
        record_pipeline_health("stocks_forex", "error", error_msg=str(e))
        send_error_alert(f"Stocks/Forex fetch failed: {e}")

    # Sentiment
    try:
        t0 = time.time()
        rows = fetch_all_sentiment()
        duration = int((time.time() - t0) * 1000)
        record_pipeline_health("sentiment", "ok", len(rows), duration_ms=duration)
    except Exception as e:
        record_pipeline_health("sentiment", "error", error_msg=str(e))

    # Signals
    try:
        evaluate_all_symbols()
    except Exception as e:
        logger.error("Signal evaluation failed: %s", e)

    # Paper trade stop/target checks
    try:
        pt = PaperTrader()
        pt.check_stops_and_targets()
        pt.update_equity_peak()
    except Exception as e:
        logger.error("Paper trader check failed: %s", e)

    logger.info("Pipeline run complete")


def run_forever():
    init_db()

    if not _has_data():
        run_backfill()

    run_pipeline()

    schedule.every(FETCH_INTERVAL_MINUTES).minutes.do(run_pipeline)

    logger.info("Scheduler started — running every %d minutes", FETCH_INTERVAL_MINUTES)

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    run_forever()
