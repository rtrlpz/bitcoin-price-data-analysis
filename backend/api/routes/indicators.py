from fastapi import APIRouter, Query

router = APIRouter(prefix="/api/indicators", tags=["indicators"])


@router.get("/{symbol}")
async def get_indicators(symbol: str, lookback: int = Query(500, ge=30, le=5000)):
    from quant_tool.analytics.indicators import compute_indicators
    df = compute_indicators(symbol, lookback)
    if df.empty:
        return []
    df.index = df.index.astype(str)
    return df.reset_index().to_dict(orient="records")
