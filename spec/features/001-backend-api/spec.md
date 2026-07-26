# 001 — Backend API Layer

## Goal
Expose the existing `quant_tool/` Python analytics engine as a FastAPI REST API with auto-documented OpenAPI schema, CORS for the Vite dev server, and typed Pydantic responses.

## Routes

| Method | Endpoint | Source Module | Cache |
|--------|----------|---------------|-------|
| GET | `/api/market-data/{symbol}` | `db_handler.load_market_data` | No (handled by React Query) |
| GET | `/api/indicators/{symbol}` | `indicators.compute_indicators` | No |
| GET | `/api/signals/{symbol}` | `db_handler.load_signals` | No |
| GET | `/api/sentiment/{symbol}` | `db_handler.load_sentiment` | No |
| GET | `/api/sentiment/{symbol}/score` | `signals.latest_sentiment` | No |
| GET | `/api/portfolio/summary` | `backtester.PaperTrader().summary` | No |
| GET | `/api/portfolio/trades` | `db_handler.load_paper_trades` | No |
| POST | `/api/analytics/project` | `learning_calculator.project_growth` | No |
| POST | `/api/analytics/risk` | `learning_calculator.risk_calculator` | No |
| GET | `/api/freshness/{symbol}` | `data_quality.freshness_status` | No |
| GET | `/api/regime/{symbol}` | `regime.detect_regime` | No |
| GET | `/api/watchlist` | Composite of all symbols | No |
| GET | `/api/health` | — | No |

## File Structure
```
backend/
├── __init__.py
├── api/
│   ├── __init__.py
│   ├── main.py              ← FastAPI app, CORS, router includes
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── market_data.py
│   │   ├── indicators.py
│   │   ├── signals.py
│   │   ├── sentiment.py
│   │   ├── portfolio.py
│   │   └── analytics.py
│   └── ws/
│       ├── __init__.py
│       └── prices.py         ← WebSocket placeholder
└── requirements-backend.txt
```

## Key Decisions
- All `quant_tool` imports use Python's sys.path hack (existing pattern in app.py)
- SQLite `sqlite3.Row` objects are converted to `dict` before JSON serialization
- CORS allows `http://localhost:5173` only (Vite dev server)
- WebSocket endpoint is a placeholder — full implementation in Phase 5
