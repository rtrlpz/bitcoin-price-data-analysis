# 002 — Implementation Plan

1. Run `npm create vite@latest frontend -- --template react-ts`
2. Install additional dependencies: axios, zustand, @tanstack/react-query, lightweight-charts, react-resizable-panels
3. Create `frontend/src/types/index.ts` with all interfaces
4. Create `frontend/src/api/client.ts` with axios instance + typed functions
5. Create `frontend/src/store/index.ts` with Zustand store skeleton
6. Create CSS token files: tokens.css, globals.css, components.css
7. Create Layout components: TopBar, Sidebar, Workspace (shell only)
8. Wire App.tsx to render Layout shell
9. Verify `npm run dev` starts without errors
