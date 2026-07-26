from fastapi import APIRouter, Query

router = APIRouter(prefix="/api/signals", tags=["signals"])


@router.get("/{symbol}")
async def get_signals(symbol: str, limit: int = Query(20, ge=1, le=100)):
    from quant_tool.database.db_handler import load_signals
    return [dict(r) for r in load_signals(symbol, limit)]
