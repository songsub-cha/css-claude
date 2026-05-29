# Dashboard Epic/Phase View — Phase 4: Frontend Epic flow view

Part of Epic **`dashboard-epic-phase-view`** (Phase B of the [Epic/Phase pipeline design](../../superpowers/specs/2026-05-29-epic-phase-pipeline-design.md)).
Phase 4 of 4 (final) · branch `css/dashboard-epic-phase-view/p4` (base `css/dashboard-epic-phase-view/p3`, **stacked**).

## What this Phase adds

The user-facing Epic → Phase flow view and the per-Phase affordances — the visible payoff of Phase B.

1. **`lib/epicFlow.ts`** (pure) — `groupByEpic(sessions)` + `toEpicFlow(group)` mirror the
   backend `epic_flow.py`, so the UI derives the flow graph from the flat session list
   (no extra fetch). Live SSE `session_updated` keeps the store fresh → the view re-renders.

2. **`EpicFlowView.tsx`** (core deliverable) — renders an `EpicFlow`: one node per Phase
   (label, current Stage badge, PR status/link) with incoming-edge `← p{n}` "stacked on"
   indicators.

3. **`SessionCard`** — for `kind="phase"`: `p{index} · {label}`, a PR link, and a
   `stacked` marker when `dependsOn` is non-empty.

4. **`KanbanBoard`** — Epic swimlanes (one per Epic with child Phases, each an
   `EpicFlowView`) rendered **above** the untouched 7-Stage grid. Resolves the spec's
   open "column set" question additively: Stages stay the per-session columns; Phases
   live in the swimlane flow. Legacy/childless Epics stay as ordinary stage cards (D9).

5. **`HistoryView`** — archived rows with a `parent_slug` group under an Epic header;
   legacy rows stay flat (D9).

6. **`DetailSlideOver`** — for a Phase session: `Phase {n}: {label}`, its `dependsOn`,
   and a stacked-PR note.

## Files

| File | Change |
|------|--------|
| `src/lib/epicFlow.ts` | new — `groupByEpic` + `toEpicFlow` |
| `src/components/EpicFlowView.tsx` | new — flow graph view |
| `src/components/SessionCard.tsx` | phase index/label, PR link, stacked marker |
| `src/components/KanbanBoard.tsx` | Epic swimlanes above the stage grid |
| `src/components/HistoryView.tsx` | group archived Phases by Epic |
| `src/components/DetailSlideOver.tsx` | Phase deps + stacked note |

## Tests

Run from `dashboard/frontend` (`npm ci` first):

```bash
npx tsc --noEmit && npm test
```

- `tsc --noEmit` clean.
- vitest **37 passed** (15 files): new `test_epicFlow` (4), `test_EpicFlowView` (4),
  extended `test_SessionCard` / `test_KanbanBoard` / `test_HistoryView` / `test_DetailSlideOver`.
  The 3 pre-existing KanbanBoard tests (7 columns + drag-to-approve) stay green.

## Epic complete

With p1 (schema/reader) → p2 (API/SSE) → p3 (types/rename) → **p4 (this view)**, the
dashboard now renders the Epic→Phase hierarchy with dependency edges, per-Phase
Stage/PR status, swimlanes, and live SSE updates (AC6). Backward-compat (D9) holds:
legacy `kind`-less sessions render as single-Phase Epics throughout.
