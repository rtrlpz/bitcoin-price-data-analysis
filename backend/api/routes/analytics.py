from fastapi import APIRouter
from pydantic import BaseModel

from quant_tool.analytics.learning_calculator import project_growth, risk_calculator
from quant_tool.database.data_quality import freshness_status
from quant_tool.analytics.regime import detect_regime
from quant_tool.database.db_handler import load_market_data

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


class ProjectRequest(BaseModel):
    investment: float
    asset_class: str
    risk_level: str
    years: float


class RiskRequest(BaseModel):
    entry_price: float
    investment: float
    asset_class: str
    side: str = "buy"
    stop_loss: float | None = None


@router.post("/project")
async def project(req: ProjectRequest):
    return project_growth(req.investment, req.asset_class, req.risk_level, req.years)


@router.post("/risk")
async def risk(req: RiskRequest):
    return risk_calculator(req.entry_price, req.investment, req.asset_class, req.side, req.stop_loss)


@router.get("/freshness/{symbol}")
async def freshness(symbol: str):
    return {"symbol": symbol, "status": freshness_status(symbol)}


@router.get("/regime/{symbol}")
async def regime(symbol: str):
    return detect_regime(symbol)


@router.get("/watchlist")
async def watchlist():
    from quant_tool.config import SYMBOLS
    result = []
    for asset_class, symbols in SYMBOLS.items():
        for sym in symbols:
            rows = load_market_data(sym, limit=2)
            price = None
            change_pct = None
            if len(rows) >= 2:
                price = rows[-1]["close"]
                prev = rows[-2]["close"]
                change_pct = (price - prev) / prev * 100 if prev else 0
            elif len(rows) == 1:
                price = rows[-1]["close"]
                change_pct = 0.0
            result.append({
                "symbol": sym,
                "asset_class": asset_class,
                "price": price,
                "change_pct": change_pct,
                "freshness": freshness_status(sym),
            })
    return result
