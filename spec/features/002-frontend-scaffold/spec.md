# 002 — Frontend Scaffold

## Goal
Create a Vite + React + TypeScript project under `frontend/` with all foundational files: types, API client, Zustand store, CSS tokens, and App shell.

## File Structure
```
frontend/
├── index.html
├── package.json
├── tsconfig.json
├── tsconfig.node.json
├── vite.config.ts
├── .env.development
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── api/
    │   └── client.ts              ← axios instance + typed functions
    ├── store/
    │   └── index.ts               ← Zustand (empty slices)
    ├── types/
    │   └── index.ts               ← All TypeScript interfaces
    ├── styles/
    │   ├── tokens.css             ← CSS custom properties
    │   ├── globals.css            ← Base reset + skeleton
    │   └── components.css         ← Component styles (empty)
    └── components/
        └── Layout/
            ├── TopBar.tsx
            ├── Sidebar.tsx
            └── Workspace.tsx
```

## Dependencies
- react, react-dom
- typescript, @types/react, @types/react-dom
- vite, @vitejs/plugin-react
- axios
- zustand
- @tanstack/react-query
- lightweight-charts
- react-resizable-panels

## Key Decisions
- No routing library — single-page dashboard (no router needed)
- CSS Modules + custom properties for styling (no Tailwind)
- All type interfaces in a single `types/index.ts` (project is small enough)
- Zustand store starts empty; slices added in Phase 5
