# 005 — Implementation Plan

1. Create each `use{Name}.ts` hook file in `frontend/src/hooks/` using `@tanstack/react-query`
2. Hooks call typed functions from `frontend/src/api/client.ts`
3. Create `frontend/src/store/index.ts` with Zustand slices
4. Create `frontend/src/hooks/useWebSocket.ts` with auto-reconnect + exponential backoff
5. Wire hooks into chart and component files from Phases 3–4
6. Verify full data flow: API → hook → component renders
