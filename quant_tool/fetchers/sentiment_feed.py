import time
import logging
from datetime import datetime, timezone

import feedparser
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

from quant_tool.config import SYMBOLS
from quant_tool.database.db_handler import upsert_sentiment

logger = logging.getLogger("quant_tool.sentiment_feed")

_sia = None


def _get_sia():
    global _sia
    if _sia is not None:
        return _sia
    try:
        _sia = SentimentIntensityAnalyzer()
    except LookupError:
        try:
            nltk.download("vader_lexicon", quiet=True)
            _sia = SentimentIntensityAnalyzer()
        except (LookupError, Exception):
            logger.warning("VADER lexicon unavailable — sentiment scoring disabled")
            _sia = None
    return _sia

SYMBOL_KEYWORDS = {
    "BTC/USDT": ["bitcoin", "btc", "crypto market"],
    "ETH/USDT": ["ethereum", "eth", "ether"],
    "AAPL": ["apple", "aapl", "iphone", "ipad", "macbook", "tim cook"],
    "MSFT": ["microsoft", "msft", "windows", "azure", "satya nadella"],
    "GOOGL": ["google", "alphabet", "googl", "chrome", "android"],
    "AMZN": ["amazon", "amzn", "aws", "bezos"],
    "EURUSD=X": ["euro", "eur/usd", "eur usd", "european central bank"],
    "GBPUSD=X": ["pound", "sterling", "gbp/usd", "gbp usd", "bank of england"],
}

RSS_FEEDS = [
    {"url": "https://www.coindesk.com/arc/outboundfeeds/rss/", "source": "coindesk"},
    {"url": "https://feeds.content.dowjones.io/public/rss/mw_topstories", "source": "marketwatch"},
    {"url": "https://finance.yahoo.com/news/rssindex", "source": "yahoo_finance"},
]


def _match_symbol(headline: str) -> str:
    hl_lower = headline.lower()
    for symbol, keywords in SYMBOL_KEYWORDS.items():
        for kw in keywords:
            if kw in hl_lower:
                return symbol
    return "GENERAL"


def fetch_rss_headlines(feed_url: str, source: str, max_retries: int = 3):
    for attempt in range(1, max_retries + 1):
        try:
            feed = feedparser.parse(feed_url)
            if feed.bozo and not feed.entries:
                logger.warning("Malformed RSS feed %s (attempt %d/%d)", feed_url, attempt, max_retries)
                if attempt < max_retries:
                    time.sleep(5 * attempt)
                continue

            headlines = []
            for entry in feed.entries[:10]:
                headlines.append({
                    "headline": entry.get("title", ""),
                    "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                    "source": source,
                })
            logger.info("Fetched %d headlines from %s", len(headlines), source)
            return headlines

        except Exception as e:
            logger.warning("RSS fetch error %s (attempt %d/%d): %s", feed_url, attempt, max_retries, e)
            time.sleep(5 * attempt)

    logger.error("Exhausted retries for RSS feed %s", feed_url)
    return []


def score_headlines(headlines: list[dict]) -> list[dict]:
    sia = _get_sia()
    scored = []
    for h in headlines:
        if sia is not None:
            scores = sia.polarity_scores(h["headline"])
        else:
            scores = {"compound": 0.0}
        scored.append({
            "timestamp": h["timestamp"],
            "source": h["source"],
            "symbol": h.get("symbol", "GENERAL"),
            "sentiment_score": scores["compound"],
            "headline": h["headline"],
        })
    return scored


def fetch_all_sentiment():
    all_rows = []
    for feed in RSS_FEEDS:
        headlines = fetch_rss_headlines(feed["url"], feed["source"])
        for h in headlines:
            h["symbol"] = _match_symbol(h["headline"])
        scored = score_headlines(headlines)
        all_rows.extend(scored)
        time.sleep(2)

    if all_rows:
        upsert_sentiment(all_rows)
    logger.info("Total sentiment entries scored: %d — matched symbols: %s", len(all_rows),
                 {k: sum(1 for r in all_rows if r["symbol"] == k) for k in SYMBOL_KEYWORDS})
    return all_rows
