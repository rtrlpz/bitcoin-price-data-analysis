from fastapi import APIRouter, Query
from quant_tool.database.db_handler import load_sentiment
from quant_tool.analytics.signals import latest_sentiment

router = APIRouter(prefix="/api/sentiment", tags=["sentiment"])


@router.get("/{symbol}")
async def get_sentiment(symbol: str, limit: int = Query(10, ge=1, le=100)):
    return [dict(r) for r in load_sentiment(symbol, limit)]


@router.get("/{symbol}/score")
async def get_sentiment_score(symbol: str):
    return {"symbol": symbol, "score": latest_sentiment(symbol)}
