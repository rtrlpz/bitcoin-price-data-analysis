# 007 — Implementation Plan

1. Wrap each major panel (chart, watchlist, portfolio, signals) with `ErrorBoundary`
2. Add skeleton loading states to all components that don't have them
3. Create empty state illustrations (simple SVG or styled divs)
4. Add connection health indicator in TopBar
5. Audit component renders — add React.memo where beneficial
6. Fix all React console warnings
7. Add initial loading splash screen
8. Test with API turned off: all panels show meaningful error/empty states
