# Dashboard Epic/Phase View — Phase 3: Frontend rename + types

Part of Epic **`dashboard-epic-phase-view`** (Phase B of the [Epic/Phase pipeline design](../../superpowers/specs/2026-05-29-epic-phase-pipeline-design.md)).
Phase 3 of 4 · branch `css/dashboard-epic-phase-view/p3` (base `css/dashboard-epic-phase-view/p2`, **stacked**).

## What this Phase adds

The spec's "mechanical first commit": resolve the **naming collision** and lay the TS
contract p4's view consumes.

1. **Vocabulary rename (D1)** — the 7 pipeline steps are now **Stage** (`StageName`,
   was `PhaseName`); the new feature-level unit is **Phase**. `Session.currentPhase`
   → `currentStage`. Renamed across `KanbanBoard` / `Column` / `DetailSlideOver` /
   `App`, with test fixtures updated.

2. **New types** in `types.ts`:
   - `Session` gains `kind` / `parentSlug` / `phaseIndex` / `phaseLabel?` / `dependsOn`.
   - `PhaseNode` + `EpicFlow` — match the p2 `GET /api/sessions/epics` response.
   - `Phase` — camelCase view of a child Phase session.
   - SSE variants `phase_started` / `phase_completed` / `phase_pr_opened`; `api/sse.ts`
     subscribes to them.

3. **Contract safety** — the SSE `session_updated` **wire** field stays `phase`
   (the backend/p2 emits `phase`); only the TS type and the `Session` property are
   renamed. `App.tsx` maps `d.phase → currentStage`.

## Files

| File | Change |
|------|--------|
| `src/types.ts` | rename + `PhaseNode`/`EpicFlow`/`Phase`/`SessionKind` + new SSE variants |
| `src/components/{KanbanBoard,Column,DetailSlideOver}.tsx` | `StageName` / `currentStage` |
| `src/App.tsx` | SSE map target `currentStage` |
| `src/api/sse.ts` | subscribe to `phase_*` events |
| `tests/test_{types,KanbanBoard,SessionCard,DetailSlideOver,stores}.*` | fixtures + new type tests |

## Tests

Run from `dashboard/frontend` (`npm ci` first):

```bash
npx tsc --noEmit   # type contract
npm test           # vitest
```

- `tsc --noEmit` — clean (the rename is type-consistent; no leftover `PhaseName`/`currentPhase` in `src/` except the explanatory comment in `types.ts`).
- vitest — **24 passed** (13 files), including 3 new `test_types` cases for `Session` hierarchy fields, `EpicFlow`/`PhaseNode`, and `Phase`.

## Consumed by

- **Phase 4** — `EpicFlowView` renders `EpicFlow`/`PhaseNode`; `SessionCard` uses the
  `Phase` hierarchy fields; the store reacts to the `phase_*` SSE events.
