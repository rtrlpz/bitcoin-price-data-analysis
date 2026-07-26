import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from backend.api.routes import market_data, indicators, signals, sentiment, portfolio, analytics

app = FastAPI(
    title="Quant Trading API",
    version="1.0.0",
    description="Multi-asset quantitative trading analytics backend",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(market_data.router)
app.include_router(indicators.router)
app.include_router(signals.router)
app.include_router(sentiment.router)
app.include_router(portfolio.router)
app.include_router(analytics.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
