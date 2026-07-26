from fastapi import APIRouter, Query

router = APIRouter(prefix="/api/market-data", tags=["market_data"])


@router.get("/{symbol}")
async def get_market_data(symbol: str, limit: int = Query(500, ge=1, le=5000)):
    from quant_tool.database.db_handler import load_market_data
    return [dict(r) for r in load_market_data(symbol, limit)]
