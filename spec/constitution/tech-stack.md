# Tech Stack

## Backend Runtime
| Layer | Choice | Rationale |
|-------|--------|-----------|
| Language | Python 3.13 | Existing analytics codebase |
| Framework | FastAPI | Async support, auto-docs (OpenAPI), Pydantic validation, CORS built-in |
| Server | uvicorn | ASGI server for FastAPI |
| Package manager | pip + requirements.txt | Works with existing Python venv |

## Frontend Runtime
| Layer | Choice | Rationale |
|-------|--------|-----------|
| Language | TypeScript 5.x | Type safety for complex state, catch bugs at build time |
| Framework | React 18+ | Component model, ecosystem, industry standard for trading UIs |
| Build tool | Vite 5+ | Fast HMR, TypeScript/JSX out of the box, minimal config |
| Package manager | npm | Standard for React ecosystem |

## UI Layer
| Component | Choice | Rationale |
|-----------|--------|-----------|
| Styling | CSS Modules + custom properties | Scoped styles, no runtime overhead, token-driven |
| State (global) | Zustand | Minimal boilerplate, slice pattern, no providers, works outside React tree |
| State (server) | @tanstack/react-query | Automatic caching, background refetch, stale management, devtools |
| HTTP client | axios | Interceptors for auth/error handling, base URL config |
| Charting | lightweight-charts (TradingView) | Canvas-rendered, 60fps, 10K+ candles, crosshair, designed for financial data |
| Layout | react-resizable-panels | Drag-to-resize panels, React 18 compatible, lightweight |

## Data Ingestion (unchanged)
| Source | Library | Data | Frequency |
|--------|---------|------|-----------|
| Crypto (Binance, Coinbase) | CCXT 4.0+ | OHLCV 1h | Every 60 min |
| Stocks | yfinance 0.2.30+ | OHLCV 1d | Every 60 min |
| Stocks (supplemental) | Finnhub REST API | OHLCV 1d | Fallback if yfinance fails |
| Forex | yfinance | OHLCV 1d | Every 60 min |
| Sentiment | feedparser (RSS) + NLTK VADER | Headlines + score | Every 60 min |

## Analytics (unchanged)
| Library | Purpose |
|---------|---------|
| pandas 2.0+ | Dataframes, time series manipulation |
| numpy 1.26+ | Numerical operations |
| pandas-ta 0.3.14+ | Technical indicators (RSI, EMA, MACD, Bollinger, ATR) |
| scipy | Statistical functions, volatility calculations |
| schedule 1.2+ | In-process task scheduler for pipeline runs |

## Why This Stack
| Alternative | Reason Rejected |
|-------------|-----------------|
| Streamlit | Full-page reruns, no true component model, HTML-string components, no production charting library |
| Next.js | Overkill for SPA — no SSR needed, Vite is simpler for a dashboard |
| Tailwind CSS | Utility classes conflict with token-driven design; CSS Modules give explicit control |
| Recharts / Nivo | SVG-based, slow >1000 data points; lightweight-charts is canvas-based and purpose-built for finance |
| Redux Toolkit | More boilerplate than Zustand for this scale; Zustand's slice pattern matches our domain boundaries |
| Vue / Svelte | Smaller ecosystems for trading UI components; React has the most financial-charting library support |
