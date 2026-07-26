# 006 — Implementation Plan

1. Wrap Workspace.tsx in `PanelGroup`/`Panel`/`PanelResizeHandle` from `react-resizable-panels`
2. Update Sidebar.tsx with watchlist + signal feeds
3. Update TopBar.tsx with symbol selector + timeframe pills + status
4. Add layout presets as Zustand state, toggle via keyboard
5. Implement all keyboard shortcuts in a `useEffect` in App.tsx
6. Add CSS media queries for responsive breakpoints
7. Test all layout presets and resize handles
