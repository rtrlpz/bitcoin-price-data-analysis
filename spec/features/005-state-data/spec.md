# 005 — State & Data Fetching

## Goal
Implement all data fetching hooks (React Query), the WebSocket hook, and Zustand store slices. Wire the full data flow from API → cache → UI components.

## Hooks

| Hook | Source | Polling | Returns |
|------|--------|---------|---------|
| `useMarketData(symbol, limit?)` | `GET /api/market-data/:symbol` | 5 min | OHLCV rows |
| `useIndicators(symbol, lookback?)` | `GET /api/indicators/:symbol` | 5 min | indicator df |
| `useSignals(symbol, limit?)` | `GET /api/signals/:symbol` | 2 min | signal rows |
| `useSentiment(symbol, limit?)` | `GET /api/sentiment/:symbol` | 2 min | sentiment rows |
| `usePortfolioSummary()` | `GET /api/portfolio/summary` | 1 min | summary object |
| `usePortfolioTrades(status?)` | `GET /api/portfolio/trades` | 1 min | trade rows |
| `useWatchlist()` | `GET /api/watchlist` | 2 min | all symbols |
| `useWebSocket(symbol)` | `ws://...` | real-time | tick stream |

## Zustand Slices

| Slice | State | Actions |
|-------|-------|---------|
| `assetSlice` | `selectedAsset`, `assets` | `setAsset()` |
| `chartSlice` | `timeframe`, `indicatorVisibility` | `setTimeframe()`, `toggleIndicator()` |
| `layoutSlice` | `panelSizes`, `sidebarOpen` | `setPanelSizes()`, `toggleSidebar()` |
| `connectionSlice` | `wsStatus`, `lastPing` | `setWsStatus()` |

## Architecture
- React Query handles all HTTP caching, polling, refetch, stale time
- WebSocket hook is separate (not React Query) — manages own connection lifecycle
- Zustand slices are independent — combined in `store/index.ts` via `create()`
- Loading/error states flow from React Query through hooks to components
