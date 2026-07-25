import sqlite3
import logging
from datetime import datetime, timezone

from quant_tool.config import DB_PATH

logger = logging.getLogger("quant_tool.db")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS market_data (
    timestamp TEXT NOT NULL,
    symbol    TEXT NOT NULL,
    open      REAL,
    high      REAL,
    low       REAL,
    close     REAL,
    volume    REAL,
    asset_class TEXT,
    PRIMARY KEY (timestamp, symbol)
);

CREATE TABLE IF NOT EXISTS sentiment_data (
    timestamp      TEXT NOT NULL,
    source         TEXT NOT NULL,
    symbol         TEXT NOT NULL,
    sentiment_score REAL,
    headline       TEXT,
    PRIMARY KEY (timestamp, source, symbol)
);

CREATE TABLE IF NOT EXISTS trade_signals (
    timestamp        TEXT NOT NULL,
    symbol           TEXT NOT NULL,
    signal_type      TEXT NOT NULL,
    indicator_trigger TEXT,
    status           TEXT DEFAULT 'pending',
    PRIMARY KEY (timestamp, symbol, signal_type)
);

CREATE TABLE IF NOT EXISTS paper_trades (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       TEXT NOT NULL,
    symbol          TEXT NOT NULL,
    side            TEXT NOT NULL,
    quantity        REAL,
    entry_price     REAL,
    exit_price      REAL,
    stop_loss       REAL,
    take_profit     REAL,
    pnl             REAL,
    pnl_pct         REAL,
    fees            REAL,
    status          TEXT DEFAULT 'open'
);

CREATE TABLE IF NOT EXISTS paper_portfolio (
    key   TEXT PRIMARY KEY,
    value REAL
);

CREATE TABLE IF NOT EXISTS pipeline_health (
    timestamp TEXT NOT NULL,
    fetcher   TEXT NOT NULL,
    status    TEXT NOT NULL,
    rows_count INTEGER DEFAULT 0,
    error_msg TEXT DEFAULT '',
    duration_ms INTEGER DEFAULT 0,
    PRIMARY KEY (timestamp, fetcher)
);
"""


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db():
    conn = get_connection()
    try:
        conn.executescript(SCHEMA_SQL)
        conn.execute(
            "INSERT OR IGNORE INTO paper_portfolio (key, value) VALUES (?, ?)",
            ("cash", 10_000.0),
        )
        conn.execute(
            "INSERT OR IGNORE INTO paper_portfolio (key, value) VALUES (?, ?)",
            ("equity_peak", 10_000.0),
        )
        conn.commit()
        logger.info("Database initialised at %s", DB_PATH)
    except Exception as exc:
        logger.error("Failed to init DB: %s", exc)
        raise
    finally:
        conn.close()


def upsert_market_data(rows: list[dict]):
    conn = get_connection()
    try:
        sql = """
        INSERT OR REPLACE INTO market_data (timestamp, symbol, open, high, low, close, volume, asset_class)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        data = [
            (
                r["timestamp"],
                r["symbol"],
                r["open"],
                r["high"],
                r["low"],
                r["close"],
                r["volume"],
                r.get("asset_class", ""),
            )
            for r in rows
        ]
        conn.executemany(sql, data)
        conn.commit()
        logger.debug("Upserted %d market_data rows", len(rows))
    except Exception as exc:
        logger.error("market_data upsert failed: %s", exc)
        raise
    finally:
        conn.close()


def upsert_sentiment(rows: list[dict]):
    conn = get_connection()
    try:
        sql = """
        INSERT OR REPLACE INTO sentiment_data (timestamp, source, symbol, sentiment_score, headline)
        VALUES (?, ?, ?, ?, ?)
        """
        data = [
            (
                r["timestamp"],
                r["source"],
                r["symbol"],
                r["sentiment_score"],
                r["headline"],
            )
            for r in rows
        ]
        conn.executemany(sql, data)
        conn.commit()
        logger.debug("Upserted %d sentiment rows", len(rows))
    except Exception as exc:
        logger.error("sentiment upsert failed: %s", exc)
        raise
    finally:
        conn.close()


def upsert_signal(rows: list[dict]):
    conn = get_connection()
    try:
        sql = """
        INSERT OR REPLACE INTO trade_signals (timestamp, symbol, signal_type, indicator_trigger, status)
        VALUES (?, ?, ?, ?, ?)
        """
        data = [
            (
                r["timestamp"],
                r["symbol"],
                r["signal_type"],
                r.get("indicator_trigger", ""),
                r.get("status", "pending"),
            )
            for r in rows
        ]
        conn.executemany(sql, data)
        conn.commit()
        logger.info("Upserted %d signal rows", len(rows))
    except Exception as exc:
        logger.error("signal upsert failed: %s", exc)
        raise
    finally:
        conn.close()


def load_market_data(symbol: str, limit: int = 500) -> list[sqlite3.Row]:
    conn = get_connection()
    try:
        cursor = conn.execute(
            "SELECT * FROM market_data WHERE symbol = ? ORDER BY timestamp ASC LIMIT ?",
            (symbol, limit),
        )
        return cursor.fetchall()
    finally:
        conn.close()


def load_sentiment(symbol: str, limit: int = 100) -> list[sqlite3.Row]:
    conn = get_connection()
    try:
        cursor = conn.execute(
            "SELECT * FROM sentiment_data WHERE symbol = ? ORDER BY timestamp DESC LIMIT ?",
            (symbol, limit),
        )
        return cursor.fetchall()
    finally:
        conn.close()


def load_signals(symbol: str, limit: int = 50) -> list[sqlite3.Row]:
    conn = get_connection()
    try:
        cursor = conn.execute(
            "SELECT * FROM trade_signals WHERE symbol = ? ORDER BY timestamp DESC LIMIT ?",
            (symbol, limit),
        )
        return cursor.fetchall()
    finally:
        conn.close()


def get_portfolio_value(key: str) -> float:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT value FROM paper_portfolio WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else 0.0
    finally:
        conn.close()


def set_portfolio_value(key: str, value: float):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO paper_portfolio (key, value) VALUES (?, ?)",
            (key, value),
        )
        conn.commit()
    finally:
        conn.close()


def insert_paper_trade(trade: dict):
    conn = get_connection()
    try:
        columns = ", ".join(trade.keys())
        placeholders = ", ".join("?" for _ in trade)
        sql = f"INSERT INTO paper_trades ({columns}) VALUES ({placeholders})"
        conn.execute(sql, list(trade.values()))
        conn.commit()
    finally:
        conn.close()


def update_paper_trade(trade_id: int, updates: dict):
    conn = get_connection()
    try:
        sets = ", ".join(f"{k} = ?" for k in updates)
        conn.execute(
            f"UPDATE paper_trades SET {sets} WHERE id = ?",
            list(updates.values()) + [trade_id],
        )
        conn.commit()
    finally:
        conn.close()


def record_pipeline_health(fetcher: str, status: str, rows_count: int = 0, error_msg: str = "", duration_ms: int = 0):
    conn = get_connection()
    try:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "INSERT OR REPLACE INTO pipeline_health (timestamp, fetcher, status, rows_count, error_msg, duration_ms) VALUES (?, ?, ?, ?, ?, ?)",
            (ts, fetcher, status, rows_count, error_msg, duration_ms),
        )
        conn.commit()
    except Exception as exc:
        logger.error("Failed to record pipeline health: %s", exc)
    finally:
        conn.close()


def load_paper_trades(status: str = "all") -> list[sqlite3.Row]:
    conn = get_connection()
    try:
        if status == "all":
            cursor = conn.execute(
                "SELECT * FROM paper_trades ORDER BY timestamp DESC"
            )
        else:
            cursor = conn.execute(
                "SELECT * FROM paper_trades WHERE status = ? ORDER BY timestamp DESC",
                (status,),
            )
        return cursor.fetchall()
    finally:
        conn.close()
