import logging
from datetime import datetime, timezone

import requests

from quant_tool.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger("quant_tool.telegram")


def send_message(text: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram credentials not configured — skipping message")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
    }

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            logger.info("Telegram alert sent successfully")
            return True

        except requests.exceptions.Timeout:
            logger.warning("Telegram timeout (attempt %d/%d)", attempt, max_retries)

        except requests.exceptions.HTTPError as e:
            logger.error("Telegram HTTP error: %s", e)
            return False

        except requests.exceptions.RequestException as e:
            logger.warning("Telegram network error (attempt %d/%d): %s", attempt, max_retries, e)

    logger.error("Failed to send Telegram message after %d attempts", max_retries)
    return False


def format_signal_alert(signal: dict) -> str:
    ts = signal.get("timestamp", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
    symbol = signal.get("symbol", "N/A")
    signal_type = signal.get("signal_type", "N/A")
    trigger = signal.get("indicator_trigger", "")

    emoji_map = {
        "STRONG_BUY": "🟢",
        "BUY_WATCH": "👀",
        "STRONG_SELL": "🔴",
        "SELL_WATCH": "⚠️",
        "BULLISH_CROSS": "📈",
        "BEARISH_CROSS": "📉",
        "BOUNCE_WATCH": "💫",
        "BREAKDOWN_WATCH": "💥",
        "UPTREND": "⬆️",
        "DOWNTREND": "⬇️",
    }
    emoji = emoji_map.get(signal_type, "📊")

    return (
        f"{emoji} <b>ALERT: {symbol}</b>\n"
        f"Signal: {signal_type}\n"
        f"Trigger: {trigger}\n"
        f"Time: {ts} UTC"
    )


def send_signal_alert(signal: dict) -> bool:
    msg = format_signal_alert(signal)
    return send_message(msg)


def send_error_alert(error_msg: str) -> bool:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    text = (
        f"🚨 <b>SYSTEM ERROR</b>\n"
        f"{error_msg}\n"
        f"Time: {ts} UTC"
    )
    return send_message(text)


def send_daily_summary(summary: dict) -> bool:
    text = (
        f"📊 <b>Daily Summary</b>\n"
        f"Total Trades: {summary.get('total_trades', 0)}\n"
        f"Win Rate: {summary.get('win_rate', 0):.1f}%\n"
        f"Profit Factor: {summary.get('profit_factor', 0)}\n"
        f"Equity: ${summary.get('equity', 0):.2f}\n"
        f"Drawdown: {summary.get('drawdown_pct', 0):.2f}%\n"
        f"Peak Equity: ${summary.get('peak_equity', 0):.2f}"
    )
    return send_message(text)
