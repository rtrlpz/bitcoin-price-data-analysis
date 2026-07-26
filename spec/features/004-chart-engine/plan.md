# 004 — Implementation Plan

1. Read lightweight-charts documentation via Context7
2. Create `frontend/src/charts/TVChart.tsx` with candlestick series
3. Add EMA/SMA/Bollinger Band overlays as LineSeries
4. Create `frontend/src/charts/RSIPane.tsx`
5. Create `frontend/src/charts/VolumePane.tsx`
6. Implement crosshair sync across panes
7. Wire timeframe pills to `timeScale().setVisibleRange()`
8. Add ResizeObserver to handle container resize
9. Test with real market data from API
