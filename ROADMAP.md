# ROADMAP — React Migration (Phase 1–8)

Work top to bottom. Each phase has a prompt you can give to an AI agent, steps to verify, and a commit message.

---

## Phase 1 — Backend API Layer

**Goal:** Expose the existing `quant_tool/` Python analytics as a FastAPI REST API.

### Steps
- [ ] Install FastAPI + uvicorn (`pip install fastapi uvicorn`)
- [x] Create `backend/api/routes/market_data.py` — GET `/api/market-data/:symbol?limit=N`
- [x] Create `backend/api/routes/indicators.py` — GET `/api/indicators/:symbol?lookback=N`
- [x] Create `backend/api/routes/signals.py` — GET `/api/signals/:symbol?limit=N`
- [x] Create `backend/api/routes/sentiment.py` — GET `/api/sentiment/:symbol?limit=N`
- [x] Create `backend/api/routes/portfolio.py` — GET `/api/portfolio/summary`, GET `/api/portfolio/trades`
- [x] Create `backend/api/routes/analytics.py` — POST `/api/analytics/project`, POST `/api/analytics/risk`
- [x] Create `backend/api/ws/prices.py` — WebSocket `/ws/prices/:symbol` (placeholder)
- [x] Create `backend/api/main.py` — FastAPI app with CORS, router includes
- [x] Create `backend/requirements-backend.txt`
- [ ] Test: `uvicorn backend.api.main:app` — all endpoints return valid JSON
- [ ] Test: CORS allows `http://localhost:5173` (Vite dev server)

### Prompt for Agent
> Create a FastAPI backend in `backend/` that wraps the existing `quant_tool/` analytics library. Each domain (market_data, indicators, signals, sentiment, portfolio, analytics) gets its own router file in `backend/api/routes/`. Use `APIRouter(prefix="...", tags=["..."])`. Return Pydantic models. Add CORS for localhost:5173. The `backend/api/ws/prices.py` should be a WebSocket endpoint stub. Keep `backend/quant_tool/` as a dependency — never modify it. All endpoints call existing `quant_tool` functions. Test with uvicorn.

### Commit Message
```
feat: FastAPI backend layer wrapping quant_tool analytics
```

---

## Phase 2 — Frontend Scaffold

**Goal:** React + TypeScript + Vite project with build tooling, folder structure, and API client.

### Steps
- [ ] Run `npm create vite@latest frontend -- --template react-ts`
- [ ] Install dependencies: `zustand`, `@tanstack/react-query`, `axios`, `lightweight-charts`, `react-resizable-panels`
- [ ] Install dev dependencies: `tailwindcss`, `postcss`, `autoprefixer` (or skip for CSS modules)
- [ ] Create `frontend/src/types/index.ts` — all TypeScript interfaces (OHLCV, Signal, Trade, PortfolioSummary, Regime, etc.)
- [ ] Create `frontend/src/api/client.ts` — axios instance with base URL from env
- [ ] Create `frontend/src/store/index.ts` — Zustand store with slices: asset, chart, layout, connection
- [ ] Create `frontend/src/styles/tokens.css` — CSS custom properties for colors, typography, spacing
- [ ] Create `frontend/src/styles/globals.css` — reset, skeleton animations, base styles
- [ ] Create `frontend/src/App.tsx` — layout shell (TopBar + Sidebar + Workspace + StatusBar)
- [ ] Create `frontend/src/main.tsx` — entry point with React Query provider
- [ ] Create `.env.development` with `VITE_API_BASE_URL=http://localhost:8000`
- [ ] Test: `npm run dev` — blank shell renders, no console errors

### Prompt for Agent
> Scaffold a React + TypeScript + Vite project in `frontend/`. Create the full folder structure: `components/`, `charts/`, `hooks/`, `store/`, `api/`, `types/`, `styles/`. Install zustand, @tanstack/react-query, axios, lightweight-charts, and react-resizable-panels. Define all TypeScript types in `frontend/src/types/index.ts` matching the API responses from the FastAPI backend. Create an axios client with env-based base URL. Set up a Zustand store with 4 slices. Create CSS tokens file with the dark palette. Create a layout shell App.tsx with TopBar, Sidebar, Workspace, and StatusBar placeholder components. Use CSS modules for component styles (no Tailwind). The dev server must run on port 5173.

### Commit Message
```
feat: React + Vite scaffold with Zustand store, API client, and type definitions
```

---

## Phase 3 — Design System Components

**Goal:** All UI primitives as typed React components with tokens, loading, empty, error states.

### Steps
- [ ] Implement `StatusDot` — colored circle (fresh/aging/stale/no_data)
- [ ] Implement `Badge` — colored dot + text (positive/negative/neutral/warning/info)
- [ ] Implement `MetricCard` — label + value + delta arrow, skeleton, empty state
- [ ] Implement `TimeframePills` — horizontal pill group (1D/1W/1M/1Y/ALL)
- [ ] Implement `SignalCard` — emoji + type + trigger text
- [ ] Implement `GuideCard` — label:value list
- [ ] Implement `Panel` — title bar + collapsible body
- [ ] Implement `LoadingSkeleton` — configurable pulse rectangle
- [ ] Implement `ErrorBoundary` — React error boundary class component
- [ ] Implement `WatchlistTable` — dense table with StatusDot per row, sort, row selection
- [ ] Implement `Layout/TopBar` — window title + connection status
- [ ] Implement `Layout/Sidebar` — asset selector + refresh buttons + layout selector
- [ ] Implement `Layout/Workspace` — panel grid container
- [ ] Test: Storybook or manual render test for each component in isolation

### Prompt for Agent
> Build all React components in `frontend/src/components/` based on the design tokens in `tokens.css`. Every component: (1) typed props interface exported, (2) handles loading/empty/error/default states, (3) uses CSS modules with token variables, (4) has no side effects. Build MetricCard with delta direction arrows, WatchlistTable with sortable columns and row click callback, SignalCard with emoji lookup table. Layout components (TopBar, Sidebar, Workspace) should use react-resizable-panels for the workspace grid. Each component is one `.tsx` + one `.module.css` file. Import lightweight-charts only in the `charts/` directory (next phase).

### Commit Message
```
feat: design system components — MetricCard, WatchlistTable, SignalCard, Panels, Layout
```

---

## Phase 4 — Chart Engine (TradingView Lightweight Charts)

**Goal:** Multi-pane financial chart with candlesticks, indicator overlays, crosshair sync.

### Steps
- [ ] Implement `TVChart.tsx` — main price chart with CandlestickSeries
- [ ] Implement indicator layers: EMA20, EMA50, SMA200 (LineSeries), Bollinger Bands (LineSeries upper/lower)
- [ ] Implement `RSIPane.tsx` — separate pane below price chart with LineSeries
- [ ] Implement `VolumePane.tsx` — histogram pane below RSI
- [ ] Implement cross-pane crosshair sync via chart `crosshairMove` event
- [ ] Implement timeframe zoom via `timeScale().setVisibleRange()`
- [ ] Implement buy/sell marker annotations on price chart
- [ ] Implement chart resize handler via ResizeObserver
- [ ] Cleanup: destroy chart on unmount in useEffect return

### Prompt for Agent
> Create `frontend/src/charts/TVChart.tsx` using TradingView Lightweight Charts (`lightweight-charts` npm package). The chart shows candlesticks with EMA20, EMA50, SMA200, and Bollinger Band overlays as LineSeries. Accept OHLCV data as a prop — format timestamps as UTC seconds. Use `useRef` for the chart container div and chart instance. Create the chart in `useEffect` on mount, destroy on unmount. Add `ResizeObserver` to handle container resize. Create `RSIPane.tsx` and `VolumePane.tsx` as separate chart instances below the price chart. Sync crosshair across all 3 panes by listening to `crosshairMove` on the price chart and calling `setCrosshairPosition` on the other panes. Wire timeframe pills to `timeScale().setVisibleRange()`. Style all chart elements to match the dark token palette.

### Commit Message
```
feat: multi-pane TradingView chart with indicator overlays and crosshair sync
```

---

## Phase 5 — State Management & Data Fetching

**Goal:** All data flows through React Query + Zustand, with WebSocket real-time updates.

### Steps
- [ ] Implement `useMarketData` — React Query hook, polls every 5 min
- [ ] Implement `useIndicators` — React Query hook, polls every 5 min
- [ ] Implement `useSignals` — React Query hook, polls every 2 min
- [ ] Implement `usePortfolio` — React Query hook, polls every 1 min
- [ ] Implement `useSentiment` — React Query hook, polls every 2 min
- [ ] Implement `useWebSocket` — custom hook with auto-reconnect, exponential backoff
- [ ] Wire Zustand asset slice: selecting asset updates all queries
- [ ] Wire Zustand chart slice: timeframe + active indicators toggle
- [ ] Wire Zustand layout slice: panel visibility, column ratio, preset
- [ ] Wire Zustand connection slice: WebSocket status, latency
- [ ] Implement cache invalidation: manual refresh clears React Query cache

### Prompt for Agent
> Create data hooks in `frontend/src/hooks/` using `@tanstack/react-query`. Each hook (useMarketData, useIndicators, useSignals, usePortfolio, useSentiment) calls the FastAPI backend via the axios client, returns typed data, and has a configurable staleTime/refetchInterval. Create `useWebSocket` hook that manages a WebSocket connection to `/ws/prices/:symbol` with auto-reconnect (1s, 2s, 4s, 8s… max 30s), heartbeat ping every 30s, and connection status reporting. Wire the Zustand store so that selecting a different asset in the Sidebar triggers all query refetches with the new symbol. The chart timeframe and active indicators toggles should be in Zustand chart slice and read by the chart component.

### Commit Message
```
feat: React Query hooks for all API endpoints + WebSocket real-time hook
```

---

## Phase 6 — Workspace Layout & Keyboard Shortcuts

**Goal:** Resizable panel layout, layout presets, keyboard shortcuts, responsive design.

### Steps
- [ ] Implement resizable panel layout using `react-resizable-panels`
- [ ] Implement layout presets: Default, Full Chart, Analysis, Trades Only
- [ ] Implement preset load/save via Zustand layout slice
- [ ] Implement keyboard shortcuts: ← → (asset), 1-5 (timeframe), R (refresh), T (preset cycle), ? (help)
- [ ] Implement keyboard shortcut help overlay modal
- [ ] Implement responsive CSS breakpoints: ≥1200px, 768–1199px, <768px
- [ ] Implement column reflow: side-by-side → stacked on mobile

### Prompt for Agent
> Replace the static column layout in Workspace.tsx with `react-resizable-panels` (PanelGroup, Panel, PanelResizeHandle). Create 3 layout presets stored in Zustand: Default (watchlist + chart + signals), Full Chart (chart only), Analysis (all panels including sentiment). Add a layout preset dropdown in the Sidebar. Implement keyboard shortcuts via a `useEffect` with `document.addEventListener('keydown', ...)`: ArrowLeft/Right for asset switching, digits 1-5 for timeframe, R for refresh, T for preset cycling, ? for help overlay. The help overlay should be a modal dismissable by pressing ? again or clicking outside. Add CSS media queries in `globals.css` for tablet (<1200px) and mobile (<768px) with column reflow.

### Commit Message
```
feat: resizable panel layout with presets, keyboard shortcuts, responsive CSS
```

---

## Phase 7 — Production Polish

**Goal:** Error boundaries, loading skeletons, empty states, performance optimization.

### Steps
- [ ] Wrap each panel in ErrorBoundary component
- [ ] Add LoadingSkeleton to every data-dependent component
- [ ] Implement empty state for every panel (no data — show message + action button)
- [ ] Add transition animations (panel open/close, data refresh)
- [ ] Add performance timing (console.log render times for each section)
- [ ] Add data freshness indicator in TopBar
- [ ] Add connection status indicator in TopBar
- [ ] Final responsive QA at all 3 breakpoints

### Prompt for Agent
> Add production polish across all components. Create an ErrorBoundary class component in `components/ErrorBoundary.tsx` that renders a red-bordered fallback with "Retry" button. Wrap every panel in the Workspace in its own ErrorBoundary (one panel crash doesn't kill others). Add LoadingSkeleton pulse animation to MetricCard, WatchlistTable rows, TVChart, SignalCard list. Every data-dependent component must handle 4 states: loading (skeleton), empty (icon + message + action button), error (error boundary fallback), and default (real data). Add CSS transitions for panel show/hide (300ms ease). Add a console.time / console.timeEnd performance marker for each section.

### Commit Message
```
feat: error boundaries, loading skeletons, empty states, performance polish
```

---

## Phase 8 — Integration Testing

**Goal:** End-to-end verification, bug fixes, README, deploy docs.

### Steps
- [ ] Full manual test: backend starts, frontend starts, data loads
- [ ] Test: select each asset, chart updates
- [ ] Test: change timeframe, chart re-renders
- [ ] Test: toggle indicators on/off
- [ ] Test: layout presets show/hide panels
- [ ] Test: keyboard shortcuts work in all panels
- [ ] Test: browser resize at all 3 breakpoints
- [ ] Test: refresh buttons clear cache and re-fetch
- [ ] Test: empty database shows appropriate messages
- [ ] Fix any bugs found
- [ ] Write `README.md` with setup instructions
- [ ] Update `AGENTS.md` with final architecture

### Prompt for Agent
> Run comprehensive end-to-end tests on the full application. Start the FastAPI backend with `uvicorn backend.api.main:app` and the Vite dev server with `npm run dev`. Test every feature: asset selection, timeframe change, indicator toggles, layout presets, keyboard shortcuts, browser responsiveness, manual data refresh. Test edge cases: empty database, network failure (stop the backend while frontend is running), rapid clicking. Fix any bugs found. Write a README.md with setup instructions (clone, install backend deps, install frontend deps, run both). Update AGENTS.md if architecture changed.

### Commit Message
```
feat: production-ready React + FastAPI trading dashboard
```

---

## Summary

| Phase | Name | Est. Time | Commit Message |
|-------|------|-----------|----------------|
| 1 | Backend API | 2 days | `feat: FastAPI backend layer wrapping quant_tool analytics` |
| 2 | Frontend Scaffold | 1 day | `feat: React + Vite scaffold with Zustand store, API client, and type definitions` |
| 3 | Design System | 3 days | `feat: design system components — MetricCard, WatchlistTable, SignalCard, Panels, Layout` |
| 4 | Chart Engine | 2 days | `feat: multi-pane TradingView chart with indicator overlays and crosshair sync` |
| 5 | State & Data | 2 days | `feat: React Query hooks for all API endpoints + WebSocket real-time hook` |
| 6 | Layout & Shortcuts | 1 day | `feat: resizable panel layout with presets, keyboard shortcuts, responsive CSS` |
| 7 | Production Polish | 2 days | `feat: error boundaries, loading skeletons, empty states, performance polish` |
| 8 | Integration Testing | 1 day | `feat: production-ready React + FastAPI trading dashboard` |
| **Total** | | **~14 days** | |
