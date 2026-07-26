# Roadmap

```
Phase 1 ─ Foundation (COMPLETE)
  quant_tool/ database, analytics, fetchers, scheduler
  Streamlit dashboard v1 (deprecated — replaced by React)

Phase 2 ─ React Migration (CURRENT — 8 phases)
├── 001 Backend API Layer
│   └── FastAPI REST endpoints wrapping quant_tool
├── 002 Frontend Scaffold
│   └── Vite + React + TS + Zustand + React Query
├── 003 Design System Components
│   └── MetricCard, WatchlistTable, SignalCard, Panels, Layout
├── 004 Chart Engine
│   └── TradingView Lightweight Charts, multi-pane, crosshair sync
├── 005 State & Data Fetching
│   └── React Query hooks, WebSocket hook, Zustand slices
├── 006 Layout & Keyboard
│   └── Resizable panels, presets, keyboard shortcuts, responsive
├── 007 Production Polish
│   └── Error boundaries, skeletons, empty states, performance
└── 008 Integration Testing
    └── End-to-end verification, README, deploy docs

Phase 3 ─ Hardening & Advanced Features (NEXT after React migration)
├── Binance WebSocket real-time price streaming
├── Connection health dashboard with latency graphs
├── Enhanced backtester (vectorized, multi-symbol)
├── Trade journal with filters and CSV export
├── User preferences persistence (localStorage)
├── Chart drawing tools (trend lines, S/R levels, Fibonacci)
├── Price alerts and indicator cross alerts
└── Unit test suite (vitest + pytest, >80% coverage)
```
