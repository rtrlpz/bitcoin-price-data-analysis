import logging

import pandas as pd
import pandas_ta as ta

from quant_tool.database.db_handler import load_market_data
from quant_tool.analytics.indicators import rows_to_dataframe

logger = logging.getLogger("quant_tool.regime")


def detect_regime(symbol: str, lookback: int = 100) -> dict:
    rows = load_market_data(symbol, limit=lookback)
    if len(rows) < 30:
        return {"regime": "unknown", "adx": 0, "volatility": "normal", "direction": "neutral"}

    df = rows_to_dataframe(rows)
    if df.empty:
        return {"regime": "unknown", "adx": 0, "volatility": "normal", "direction": "neutral"}

    # ADX
    adx_df = df.ta.adx(length=14)
    adx_val = float(adx_df.iloc[-1]["ADX_14"]) if adx_df is not None and not adx_df.empty else 0.0
    di_plus = float(adx_df.iloc[-1]["DMP_14"]) if adx_df is not None and not adx_df.empty else 0.0
    di_minus = float(adx_df.iloc[-1]["DMN_14"]) if adx_df is not None and not adx_df.empty else 0.0

    # EMA slope
    ema_20 = df.ta.ema(length=20)
    if ema_20 is None or len(ema_20) < 20:
        slope = 0.0
    else:
        recent = ema_20.iloc[-20:]
        slope = (recent.iloc[-1] - recent.iloc[0]) / recent.iloc[0] if recent.iloc[0] != 0 else 0.0

    # Volatility (ATR / close)
    atr = df.ta.atr(length=14)
    atr_ratio = 0.0
    if atr is not None and not atr.empty:
        last_close = float(df.iloc[-1]["close"])
        if last_close > 0:
            atr_ratio = float(atr.iloc[-1]) / last_close

    vol_level = "high" if atr_ratio > 0.02 else "low" if atr_ratio < 0.005 else "normal"

    # Direction
    direction = "bullish" if di_plus > di_minus else "bearish"

    # Regime classification
    if adx_val >= 25 and direction == "bullish":
        regime = "trending_bull"
    elif adx_val >= 25 and direction == "bearish":
        regime = "trending_bear"
    elif adx_val < 20:
        regime = "ranging"
    else:
        regime = "weak_trend"

    if vol_level == "high" and regime in ("ranging", "weak_trend"):
        regime = "high_volatility"

    return {
        "regime": regime,
        "adx": round(adx_val, 1),
        "volatility": vol_level,
        "direction": direction,
        "atr_ratio": round(atr_ratio, 4),
        "ema_slope": round(slope, 6),
    }
