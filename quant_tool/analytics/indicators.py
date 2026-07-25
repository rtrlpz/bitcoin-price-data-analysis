import math
import logging
from datetime import datetime, timezone

import pandas as pd
import pandas_ta as ta

from quant_tool.database.db_handler import load_market_data

logger = logging.getLogger("quant_tool.indicators")


def rows_to_dataframe(rows: list) -> pd.DataFrame:
    df = pd.DataFrame(
        [dict(r) for r in rows],
        columns=["timestamp", "open", "high", "low", "close", "volume"],
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df.set_index("timestamp", inplace=True)
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.sort_index(inplace=True)
    return df


def compute_indicators(symbol: str, lookback: int = 500) -> pd.DataFrame:
    rows = load_market_data(symbol, limit=lookback)
    if len(rows) < 30:
        logger.warning("Not enough data for %s to compute indicators (%d rows)", symbol, len(rows))
        return pd.DataFrame()

    df = rows_to_dataframe(rows)

    df.ta.rsi(length=14, append=True)
    df.ta.ema(length=20, append=True)
    df.ta.ema(length=50, append=True)
    df.ta.sma(length=200, append=True)
    df.ta.bbands(length=20, std=2, append=True)
    df.ta.atr(length=14, append=True)
    df.ta.macd(append=True)

    df.rename(
        columns={
            "RSI_14": "rsi",
            "EMA_20": "ema_20",
            "EMA_50": "ema_50",
            "SMA_200": "sma_200",
            "BBU_20_2.0": "bb_upper",
            "BBM_20_2.0": "bb_middle",
            "BBL_20_2.0": "bb_lower",
            "ATRr_14": "atr",
            "MACD_12_26_9": "macd",
            "MACDs_12_26_9": "macd_signal",
            "MACDh_12_26_9": "macd_hist",
        },
        inplace=True,
        errors="ignore",
    )

    df["log_return"] = df["close"].apply(lambda x: math.log(x) if x > 0 else 0.0).diff()
    df["pct_return"] = df["close"].pct_change()

    logger.info("Computed indicators for %s — %d rows", symbol, len(df))
    return df


def compute_atr_stop(symbol: str, lookback: int = 100) -> float | None:
    df = compute_indicators(symbol, lookback)
    if df.empty or "atr" not in df.columns:
        return None
    last = df.iloc[-1]
    return float(last["close"] - 1.5 * last["atr"])
