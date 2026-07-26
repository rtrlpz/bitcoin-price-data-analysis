# 008 — Integration Testing

## Goal
End-to-end verification that all 7 previous phases work together. The dashboard loads, fetches data, renders charts, and handles errors gracefully.

## Test Scenarios

### Happy Path
1. `npm run dev` starts without errors
2. Dashboard loads in browser at localhost:5173
3. Loading splash shows → transitions to dashboard
4. TopBar shows symbol selector with BTC/USDT selected
5. Chart renders candlestick data with EMA/BB overlays
6. Volume histogram renders below price chart
7. Watchlist table shows all symbols with prices and changes
8. Signal card shows recent signals
9. Sidebar portfolio summary shows KPIs
10. Timeframe pills switch chart range

### Edge Cases
1. Start with API offline → all panels show error states
2. Start API mid-session → panels recover and load data
3. Select a symbol with no data → chart shows empty state
4. Resize browser window → chart + panels resize responsively
5. Toggle sidebar → layout adjusts smoothly
6. Cycle layout presets → panels rearrange correctly

### Console Check
- No React warnings about keys, deps, or missing fields
- No 404/500 API errors logged
- No unhandled promise rejections
- No CORS errors in browser devtools
