# 006 — Layout & Workspace

## Goal
Implement the final workspace layout: resizable panels, layout presets, keyboard shortcuts, sidebar navigation, and basic responsive behavior.

## Components

| Component | Description |
|-----------|-------------|
| `Workspace.tsx` (update) | Wrap panels in `react-resizable-panels` groups |
| `TopBar.tsx` (update) | Symbol selector, timeframe pills, connection status |
| `Sidebar.tsx` (update) | Watchlist, signal list, portfolio summary |

## Layout Presets
- **Default**: Sidebar (240px) + Chart (1fr) + Right panel (320px)
- **Compact**: Sidebar (180px) + Chart (1fr) — no right panel
- **Wide**: Sidebar (280px) + Chart (1fr) + Right panel (400px)

Stored in Zustand `layoutSlice` and toggleable via keyboard shortcut.

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+\`` | Toggle sidebar |
| `Ctrl+Shift+\`` | Cycle layout preset |
| `1-5` | Select timeframe (1H, 4H, 1D, 1W, 1M) |
| `Ctrl+[` | Previous symbol |
| `Ctrl+]` | Next symbol |
| `Ctrl+Shift+R` | Reset layout to default |

## Responsive
- <1024px: Stack panels vertically, sidebar becomes collapsible overlay
- <640px: Full-screen chart, components in bottom sheet
