ASSET_GUIDES = {
    "BTC": {
        "market_type": "Crypto (24/7 Market)",
        "best_style": "Swing Trading & Momentum",
        "entry_rule": "Buy on RSI < 30 (Oversold) combined with positive VADER sentiment.",
        "exit_rule": "Sell when RSI > 70 or price hits 2x ATR profit target.",
        "risk_rule": "Use tight ATR stop-losses. Never hold leverage when starting out.",
    },
    "ETH": {
        "market_type": "Crypto (24/7 Market)",
        "best_style": "Swing Trading & Momentum",
        "entry_rule": "Buy on RSI < 30 (Oversold) combined with positive VADER sentiment.",
        "exit_rule": "Sell when RSI > 70 or price hits 2x ATR profit target.",
        "risk_rule": "Use tight ATR stop-losses. Never hold leverage when starting out.",
    },
    "EURUSD": {
        "market_type": "Forex (Macro-Driven)",
        "best_style": "Session Breakouts & Range Trading",
        "entry_rule": "Trade during high-liquidity London/New York overlap hours. Watch for major CPI/Interest rate releases.",
        "exit_rule": "Take quick profits based on daily average pip ranges; avoid holding overnight.",
        "risk_rule": "Forex requires strict position sizing due to high structural leverage.",
    },
    "GBPUSD": {
        "market_type": "Forex (Macro-Driven)",
        "best_style": "Session Breakouts & Range Trading",
        "entry_rule": "Trade during high-liquidity London/New York overlap hours. Watch for major CPI/Interest rate releases.",
        "exit_rule": "Take quick profits based on daily average pip ranges; avoid holding overnight.",
        "risk_rule": "Forex requires strict position sizing due to high structural leverage.",
    },
    "AAPL": {
        "market_type": "Stocks (Equities)",
        "best_style": "Trend Following & Fundamental Alignment",
        "entry_rule": "Buy when price bounces off the 50-day Exponential Moving Average (EMA) during a broader market uptrend.",
        "exit_rule": "Sell if earnings disappoint or the 50 EMA breaks downward.",
        "risk_rule": "Set a hard 3% to 5% dollar stop-loss per position.",
    },
    "MSFT": {
        "market_type": "Stocks (Equities)",
        "best_style": "Trend Following & Fundamental Alignment",
        "entry_rule": "Buy when price bounces off the 50-day Exponential Moving Average (EMA) during a broader market uptrend.",
        "exit_rule": "Sell if earnings disappoint or the 50 EMA breaks downward.",
        "risk_rule": "Set a hard 3% to 5% dollar stop-loss per position.",
    },
    "GOOGL": {
        "market_type": "Stocks (Equities)",
        "best_style": "Trend Following & Fundamental Alignment",
        "entry_rule": "Buy when price bounces off the 50-day Exponential Moving Average (EMA) during a broader market uptrend.",
        "exit_rule": "Sell if earnings disappoint or the 50 EMA breaks downward.",
        "risk_rule": "Set a hard 3% to 5% dollar stop-loss per position.",
    },
    "AMZN": {
        "market_type": "Stocks (Equities)",
        "best_style": "Trend Following & Fundamental Alignment",
        "entry_rule": "Buy when price bounces off the 50-day Exponential Moving Average (EMA) during a broader market uptrend.",
        "exit_rule": "Sell if earnings disappoint or the 50 EMA breaks downward.",
        "risk_rule": "Set a hard 3% to 5% dollar stop-loss per position.",
    },
}

GENERIC_GUIDE = {
    "market_type": "General Market",
    "best_style": "Follow the primary trend; avoid counter-trend trades.",
    "entry_rule": "Look for confirmation from at least two indicators before entering.",
    "exit_rule": "Set a take-profit target at a key resistance level or technical overbought signal.",
    "risk_rule": "Never risk more than 1% of your capital on a single trade.",
}


def get_guide(symbol: str) -> dict:
    base = symbol.split("/")[0].split("=")[0]
    return ASSET_GUIDES.get(base, GENERIC_GUIDE)


TRADING_GUIDES = {
    "bitcoin": {
        "title": "Bitcoin (Crypto)",
        "icon": "₿",
        "style": "Trend Following / Swing Trading",
        "description": "24/7 market with high volatility. Best approached with trend confirmation and strict position sizing.",
        "entry": "Look for RSI < 30 (oversold) with bullish price action confirmation. Enter when price reclaims the 20 EMA after a dip.",
        "exit_take_profit": "When RSI enters overbought territory (>70) or price hits a 2× ATR profit target from entry.",
        "exit_stop_loss": "Strict ATR-based stop-loss (1.5× ATR) placed just below recent swing low. Never use high leverage — crypto can gap 10%+ in hours.",
        "loss_control": "Never risk more than 1% of capital per trade. Crypto whipsaws frequently — accept small losses as cost of doing business.",
        "tips": [
            "Avoid trading during low-volume weekend periods (manipulation risk).",
            "Use limit orders, not market orders — spreads widen during volatility.",
            "If a position moves 5% against you instantly, close it and re-evaluate.",
            "Correlation note: BTC often leads the altcoin market.",
        ],
    },
    "stocks": {
        "title": "Stocks (Equities)",
        "icon": "📈",
        "style": "Dollar-Cost Averaging (DCA) or Momentum",
        "description": "Open during standard exchange hours (9:30 AM–4:00 PM ET). More stable but gaps happen on earnings/news.",
        "entry": "DCA: Buy fixed dollar amount on a regular schedule regardless of price. Momentum: Enter when price > 50 EMA and 50 EMA > 200 EMA (golden cross).",
        "exit_take_profit": "Partial profits at 10–15% gain, or when company fundamentals shift. For momentum: trail stop under the rising 20 EMA.",
        "exit_stop_loss": "Hard percentage stop-loss (5–8% max loss per position). If the 50 EMA breaks downward, exit immediately.",
        "loss_control": "Use position sizing so no single stock exceeds 5% of your total portfolio. Diversify across sectors.",
        "tips": [
            "Never trade stocks in the first 15 minutes or last 15 minutes of the session (highest volatility).",
            "Earnings reports cause unpredictable gaps — close positions before if uncertain.",
            "Dividend stocks provide a cushion; factor in ex-dividend dates.",
            "Use limit orders to avoid paying the bid-ask spread on illiquid stocks.",
        ],
    },
    "forex": {
        "title": "Forex (Currencies)",
        "icon": "💱",
        "style": "Range Bound / Session Breakouts",
        "description": "Driven by macro economic data and interest rate decisions. High leverage amplifies both gains and losses.",
        "entry": "Trade during high-liquidity sessions (London/NY overlap, 8 AM–12 PM ET). Enter on breakouts of established daily ranges with volume confirmation.",
        "exit_take_profit": "Quick targets based on daily pip ranges (typically 20–50 pips for major pairs). Avoid holding through overnight swap fees.",
        "exit_stop_loss": "Tight stop-losses (20–30 pips) because forex relies heavily on leverage. Never risk more than 1% of account per trade.",
        "loss_control": "Forex is unforgiving. A 2% move against a 50:1 leveraged position wipes 100% of your margin. Use minimal leverage (5:1 or less).",
        "tips": [
            "Major news events (NFP, FOMC, CPI) cause instantaneous 50+ pip spikes — flatten positions 30 minutes before.",
            "The USD strength index correlates inversely with EUR/USD and GBP/USD.",
            "Avoid trading exotic pairs (USD/TRY, USD/BRL) due to erratic spreads and liquidity risk.",
            "Track central bank rate decisions — they set the medium-term trend direction.",
        ],
    },
}
