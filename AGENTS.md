# AGENTS.md — Quant Trading Dashboard (React + FastAPI)

Architectural guidelines, MCP tool integrations, and agent skill protocols for the project.

> **Current Phase:** Phase 1 — Backend API & Frontend Scaffold
> **Next Step:** `ROADMAP.md` Phase 1

---

## 1. MCP Server & Tool Integrations

The following MCP servers must be available for autonomous development:

| Tool | Purpose | Required For |
|------|---------|--------------|
| **Context7** | Fetch up-to-date docs for React, FastAPI, Vite, TradingView Lightweight Charts, Zustand, React Query, TypeScript patterns | Every phase |
| **GitHub** | Create issues, manage PRs, read/write repository state, check CI status | Commits, code review |
| **WebFetch** | Read React/TradingView/TypeScript documentation URLs | Research during implementation |
| **Figma** | Extract design tokens, spacing, color palette from UI mockups | Phase 2 (Design System) |
| **Santiment** | Real-time crypto on-chain metrics, sentiment data | Phase 6+ (advanced features) |

---

## 2. Architecture Overview

```
backend/                          ← Python FastAPI server
├── api/
│   ├── main.py                   ← FastAPI app entry point
│   ├── routes/
│   │   ├── market_data.py        ← GET /api/market-data/:symbol
│   │   ├── indicators.py         ← GET /api/indicators/:symbol
│   │   ├── signals.py            ← GET /api/signals/:symbol
│   │   ├── sentiment.py          ← GET /api/sentiment/:symbol
│   │   ├── portfolio.py          ← GET/POST /api/portfolio/*
│   │   └── analytics.py          ← POST /api/analytics/project, /risk
│   └── ws/
│       └── prices.py             ← WebSocket /ws/prices/:symbol
├── quant_tool/                    ← Existing analytics engine (unchanged)
└── requirements-backend.txt       ← Python dependencies

frontend/                         ← React + TypeScript + Vite
├── src/
│   ├── components/               ← Reusable UI components
│   │   ├── MetricCard.tsx
│   │   ├── WatchlistTable.tsx
│   │   ├── SignalCard.tsx
│   │   ├── TimeframePills.tsx
│   │   ├── StatusDot.tsx
│   │   ├── GuideCard.tsx
│   │   ├── Badge.tsx
│   │   ├── Panel.tsx
│   │   ├── LoadingSkeleton.tsx
│   │   ├── ErrorBoundary.tsx
│   │   └── Layout/
│   │       ├── TopBar.tsx
│   │       ├── Sidebar.tsx
│   │       └── Workspace.tsx
│   ├── charts/                   ← Chart components (TradingView LW)
│   │   ├── TVChart.tsx
│   │   ├── RSIPane.tsx
│   │   └── VolumePane.tsx
│   ├── hooks/                    ← React hooks for data
│   │   ├── useMarketData.ts
│   │   ├── useIndicators.ts
│   │   ├── useSignals.ts
│   │   ├── usePortfolio.ts
│   │   ├── useSentiment.ts
│   │   └── useWebSocket.ts
│   ├── store/                    ← Zustand state management
│   │   └── index.ts
│   ├── api/                      ← API client (axios/fetch)
│   │   └── client.ts
│   ├── types/                    ← TypeScript type definitions
│   │   └── index.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── styles/
│       ├── tokens.css             ← Design tokens (CSS custom properties)
│       ├── globals.css            ← Base styles, skeleton animations
│       └── components.css         ← Component-specific styles
├── index.html
├── package.json
├── tsconfig.json
├── tsconfig.node.json
├── vite.config.ts
└── .env.development              ← API_BASE_URL=http://localhost:8000
```

**Key principle:** The `backend/quant_tool/` module is a **read-only dependency** — never modify it for frontend concerns. Only add new API routes that call into it.

---

## 3. Design System & Visual Standards

- **Palette:** Dark slate (`#0d1117` bg, `#161b22` surface, `#30363d` borders)
- **Typography:** `'SF Mono','JetBrains Mono','Consolas',monospace` for all financial figures; `Inter` or system sans-serif for labels
- **Colors:** Positive `#3fb950`, Negative `#f85149`, Warning `#d29922`, Info `#58a6ff`, Accent `#1f6feb`
- **Spacing grid:** 2px / 4px / 6px / 8px / 12px / 16px / 24px / 32px
- **All values defined as CSS custom properties in `tokens.css`** — no hardcoded values in components
- Components use CSS Modules or inline `style` objects referencing token variables

---

## 4. Charting Standards (TradingView Lightweight Charts)

- **Library:** `lightweight-charts` npm package (TradingView's official canvas charting library)
- **Series types:** `CandlestickSeries` for price, `LineSeries` for indicators, `HistogramSeries` for volume
- **Performance:** Canvas-rendered, 60fps, handles 10,000+ candles
- **Crosshair:** Built-in crosshair with price/axis labels; sync across panes via chart callbacks
- **Indicators:** Rendered as separate `LineSeries` overlays on the price pane (EMA, SMA, BB) or as individual panes (RSI, Volume)
- **Timeframes:** Chart `timeScale().setVisibleRange()` to zoom to selected timeframe

---

## 5. State Management Standards

- **Global state:** Zustand store (`frontend/src/store/index.ts`) — asset selection, timeframe, panel visibility, layout preset
- **Server state:** React Query (`@tanstack/react-query`) — all API data fetching, caching, polling, and cache invalidation
- **WebSocket:** Custom `useWebSocket` hook with auto-reconnect, exponential backoff, connection status
- **Local UI state:** React `useState` / `useReducer` for component-internal state (accordion open/close, hover, etc.)

---

## 6. API Design Conventions

| Method | Endpoint | Description | Cache |
|--------|----------|-------------|-------|
| GET | `/api/market-data/:symbol?limit=N` | OHLCV rows | 5 min |
| GET | `/api/indicators/:symbol?lookback=N` | Indicator dataframe as JSON | 5 min |
| GET | `/api/signals/:symbol?limit=N` | Recent signals | 2 min |
| GET | `/api/sentiment/:symbol?limit=N` | Sentiment rows | 2 min |
| GET | `/api/portfolio/summary` | Portfolio KPIs | 1 min |
| GET | `/api/portfolio/trades?status=open|closed|all` | Trade history | 1 min |
| GET | `/api/regime/:symbol` | Market regime | 5 min |
| GET | `/api/freshness/:symbol` | Data age status | 5 min |
| GET | `/api/watchlist` | All symbols prices+changes | 2 min |
| POST | `/api/analytics/project` | Growth projection | — |
| POST | `/api/analytics/risk` | Risk calculator | — |
| WS | `/ws/prices/:symbol` | Real-time tick stream | — |

**All responses:** `application/json`, snake_case keys, UTC ISO 8601 timestamps.

---

## 7. Autonomous Agent Skills

### Skill 1: Documentation Retrieval (Context7)
Before implementing any library feature, use Context7 to fetch current API docs for React, FastAPI, lightweight-charts, zustand, @tanstack/react-query, Vite, or TypeScript to prevent deprecation issues.

### Skill 2: FastAPI Route Implementation
1. Create routes in `backend/api/routes/`, one file per domain
2. Use `APIRouter(prefix="...", tags=["..."])` pattern
3. Return Pydantic models for auto-documented OpenAPI schema
4. Call existing `quant_tool` functions — never duplicate logic
5. Add `@st.cache_data`-equivalent server-side caching (optional, future)

### Skill 3: React Component Implementation
1. One component per file in `frontend/src/components/`
2. Props typed with TypeScript interfaces, exported
3. All CSS values reference tokens from `styles/tokens.css`
4. Handle 4 states: default, loading (skeleton), empty (message), error (fallback)
5. Unit-testable: pure props-in → JSX-out (no side effects)

### Skill 4: TradingView Chart Integration
1. Import `{ createChart, CandlestickSeries, LineSeries, HistogramSeries }` from `lightweight-charts`
2. Create chart in `useEffect` on mount, destroy on unmount
3. Use `useRef` for chart container div and chart instance
4. Wire timeframe pills to `timeScale().setVisibleRange()`
5. Handle resize via `ResizeObserver` on container div

### Skill 5: Zustand Store Pattern
1. Create slice-based store in `frontend/src/store/index.ts`
2. Slices: `assetSlice`, `chartSlice`, `layoutSlice`, `connectionSlice`
3. Each slice has state + actions, exported via hooks
4. Actions are idempotent — calling same value twice produces no re-render

### Skill 6: Spec-Driven Development
1. Read `ROADMAP.md` first to identify current phase
2. Read `spec/features/NNN-name/spec.md` for full spec
3. Use `spec/features/NNN-name/tasks.md` as live checklist
4. Mark `[ ]` → `[x]` as each task completes
5. Commit with the EXACT message specified in ROADMAP.md

---

## 8. Spec-Driven Architecture

```
ROADMAP.md                        ← Phases with prompts + commit messages
spec/
├── constitution/
│   ├── mission.md                ← What/why/for whom
│   ├── tech-stack.md             ← Technologies with rationale
│   └── roadmap.md                ← High-level phase descriptions
└── features/                      ← Per-phase specs
    ├── 001-backend-api/
    ├── 002-frontend-scaffold/
    ├── 003-design-system/
    ├── 004-chart-engine/
    ├── 005-state-data/
    ├── 006-layout-workspace/
    ├── 007-production-polish/
    └── 008-integration-testing/
```

**Rules:**
- Start at `ROADMAP.md` every session.
- Complete phases in order — no skipping.
- Commit exactly the message in ROADMAP.md when phase is done.
- All new UI code goes in `frontend/src/`. Never touch `backend/quant_tool/` except to add API routes.
