# 003 — Implementation Plan

1. Read `frontend/src/styles/tokens.css` for design token values
2. Create each component in `frontend/src/components/` one per file
3. Each component: typed props, CSS class from `styles/components.css`, 4-state handling
4. Create `LoadingSkeleton` first (depended on by all others)
5. Create `ErrorBoundary` second
6. Create remaining components in dependency order
7. Wire them into Layout components for visual testing
