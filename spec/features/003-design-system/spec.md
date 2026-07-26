# 003 — Design System Components

## Goal
Build all reusable UI components in `frontend/src/components/` following the dark slate design system. Every component handles 4 states: default, loading (skeleton), empty, error.

## Components

| Component | States | Props |
|-----------|--------|-------|
| `MetricCard` | value, loading, error | `label, value, change?, icon?, loading?, error?` |
| `WatchlistTable` | rows, loading, empty, error | `rows: WatchlistRow[], loading?, error?` |
| `SignalCard` | signal, loading, empty, error | `signal: Signal, loading?, error?` |
| `TimeframePills` | active selection | `timeframes: string[], selected, onChange` |
| `StatusDot` | status color | `status: 'active'\|'warning'\|'error'\|'inactive'` |
| `GuideCard` | tip content | `title, children` |
| `Badge` | label + color | `label, variant: 'positive'\|'negative'\|'warning'\|'info'` |
| `Panel` | titled section | `title, children, actions?, loading?, error?` |
| `LoadingSkeleton` | loader shape | `variant: 'text'\|'card'\|'chart'\|'table'` |
| `ErrorBoundary` | error catch | `children, fallback?` |

## States
- **Default**: Props present, data available — normal render
- **Loading**: Show `<LoadingSkeleton>` matching component shape
- **Empty**: Props present but data is empty array/null — show message
- **Error**: Error boundary caught or `error` prop — show error message with retry
