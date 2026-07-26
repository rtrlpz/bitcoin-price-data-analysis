# 004 — Chart Engine

## Goal
Integrate TradingView Lightweight Charts (`lightweight-charts` npm package) with multi-pane support: price (candlestick + indicators), RSI, and volume panes with synchronized crosshair.

## Components

| Component | Description |
|-----------|-------------|
| `TVChart.tsx` | Main chart with CandlestickSeries + indicator overlays |
| `RSIPane.tsx` | Separate pane with RSI LineSeries |
| `VolumePane.tsx` | Separate pane with Volume HistogramSeries |

## Behavior
- Chart created in `useEffect` on mount, destroyed on unmount
- Container ref held in `useRef<HTMLDivElement>`, chart instance in `useRef<IChartApi>`
- Crosshair sync across panes via `chart.subscribeCrosshairMove()`
- Timeframe pills update `timeScale().setVisibleRange()`
- Resize handled via `ResizeObserver` on container div
- All series use token colors from `tokens.css`

## Data Flow
```
useMarketData(symbol) → OHLCV rows
  → TVChart: CandlestickSeries + LineSeries(EMA/SMA/BB)
  → RSIPane: LineSeries(RSI)
  → VolumePane: HistogramSeries(volume)
```
