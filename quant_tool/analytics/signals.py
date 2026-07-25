import logging
from datetime import datetime, timezone

import pandas as pd

from quant_tool.analytics.indicators import compute_indicators
from quant_tool.database.db_handler import load_sentiment, upsert_signal

logger = logging.getLogger("quant_tool.signals")


def latest_sentiment(symbol: str, lookback_hours: int = 24) -> float:
    rows = load_sentiment(symbol, limit=50)
    if not rows:
        return 0.0

    cutoff = pd.Timestamp.now(tz=timezone.utc) - pd.Timedelta(hours=lookback_hours)
    scores = []
    for r in rows:
        ts = pd.Timestamp(r["timestamp"])
        if ts.tzinfo is None:
            ts = ts.tz_localize("UTC")
        if ts >= cutoff:
            scores.append(r["sentiment_score"])

    if not scores:
        return 0.0
    return sum(scores) / len(scores)


def evaluate_signals(symbol: str) -> list[dict]:
    df = compute_indicators(symbol, lookback=500)
    if df.empty:
        return []

    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else last
    sentiment = latest_sentiment(symbol)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    signals = []

    price = float(last["close"])
    rsi = float(last.get("rsi", 50))
    macd = float(last.get("macd", 0))
    macd_signal = float(last.get("macd_signal", 0))
    prev_macd = float(prev.get("macd", 0))
    prev_macd_signal = float(prev.get("macd_signal", 0))

    ema_20 = float(last.get("ema_20", price))
    ema_50 = float(last.get("ema_50", price))
    sma_200 = float(last.get("sma_200", 0))
    bb_lower = float(last.get("bb_lower", 0))
    bb_upper = float(last.get("bb_upper", 0))

    if rsi < 30 and sentiment > 0.3:
        signals.append({
            "timestamp": ts,
            "symbol": symbol,
            "signal_type": "STRONG_BUY",
            "indicator_trigger": f"RSI={rsi:.1f} (oversold) + Sentiment={sentiment:.2f} (bullish divergence)",
            "status": "active",
        })
    elif rsi < 30:
        signals.append({
            "timestamp": ts,
            "symbol": symbol,
            "signal_type": "BUY_WATCH",
            "indicator_trigger": f"RSI={rsi:.1f} (oversold)",
            "status": "active",
        })

    if rsi > 70 and sentiment < -0.3:
        signals.append({
            "timestamp": ts,
            "symbol": symbol,
            "signal_type": "STRONG_SELL",
            "indicator_trigger": f"RSI={rsi:.1f} (overbought) + Sentiment={sentiment:.2f} (bearish divergence)",
            "status": "active",
        })
    elif rsi > 70:
        signals.append({
            "timestamp": ts,
            "symbol": symbol,
            "signal_type": "SELL_WATCH",
            "indicator_trigger": f"RSI={rsi:.1f} (overbought)",
            "status": "active",
        })

    if prev_macd <= prev_macd_signal and macd > macd_signal:
        signals.append({
            "timestamp": ts,
            "symbol": symbol,
            "signal_type": "BULLISH_CROSS",
            "indicator_trigger": f"MACD crossed above signal line",
            "status": "active",
        })
    elif prev_macd >= prev_macd_signal and macd < macd_signal:
        signals.append({
            "timestamp": ts,
            "symbol": symbol,
            "signal_type": "BEARISH_CROSS",
            "indicator_trigger": f"MACD crossed below signal line",
            "status": "active",
        })

    if price <= bb_lower and bb_lower > 0:
        signals.append({
            "timestamp": ts,
            "symbol": symbol,
            "signal_type": "BOUNCE_WATCH",
            "indicator_trigger": f"Price at lower Bollinger Band (${bb_lower:.2f})",
            "status": "active",
        })
    elif price >= bb_upper and bb_upper > 0:
        signals.append({
            "timestamp": ts,
            "symbol": symbol,
            "signal_type": "BREAKDOWN_WATCH",
            "indicator_trigger": f"Price at upper Bollinger Band (${bb_upper:.2f})",
            "status": "active",
        })

    if sma_200 > 0:
        if ema_20 > sma_200:
            signals.append({
                "timestamp": ts,
                "symbol": symbol,
                "signal_type": "UPTREND",
                "indicator_trigger": f"EMA20 ({ema_20:.2f}) > SMA200 ({sma_200:.2f})",
                "status": "active",
            })
        else:
            signals.append({
                "timestamp": ts,
                "symbol": symbol,
                "signal_type": "DOWNTREND",
                "indicator_trigger": f"EMA20 ({ema_20:.2f}) <= SMA200 ({sma_200:.2f})",
                "status": "active",
            })

    if signals:
        upsert_signal(signals)

    return signals


def evaluate_all_symbols():
    from quant_tool.config import SYMBOLS

    all_signals = []
    for asset_class, symbols in SYMBOLS.items():
        for symbol in symbols:
            try:
                sigs = evaluate_signals(symbol)
                all_signals.extend(sigs)
            except Exception as e:
                logger.error("Signal evaluation failed for %s: %s", symbol, e)
    return all_signals
