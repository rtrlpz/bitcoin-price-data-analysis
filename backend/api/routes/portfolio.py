from fastapi import APIRouter, Query
from quant_tool.analytics.backtester import PaperTrader
from quant_tool.database.db_handler import load_paper_trades

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.get("/summary")
async def get_summary():
    return PaperTrader().summary()


@router.get("/trades")
async def get_trades(status: str = Query("all", regex="^(open|closed|all)$")):
    return [dict(r) for r in load_paper_trades(status)]
