# Dashboard Epic/Phase View — Phase 2: Backend API + SSE

Part of Epic **`dashboard-epic-phase-view`** (Phase B of the [Epic/Phase pipeline design](../../superpowers/specs/2026-05-29-epic-phase-pipeline-design.md)).
Phase 2 of 4 · branch `css/dashboard-epic-phase-view/p2` (base `css/dashboard-epic-phase-view/p1`, **stacked**).

## What this Phase adds

Exposes the Epic→Phase hierarchy (parsed in Phase 1) over HTTP and SSE.

1. **`services/epic_flow.py`** — `build_epic_flow(EpicGroup) -> {epic, nodes, edges}`:
   - `nodes`: one per child Phase — `phase_index`, `phase_label`, `current_stage`,
     `pr_status` (`"open"` when a PR artifact exists, else the stage status), `pr_url`.
   - `edges`: `{from, to}` from each Phase's `depends_on`.
   - Legacy single-Phase Epics → one synthetic node; orphan groups → `epic=None`.

2. **`GET /api/sessions/epics`** — one entry per Epic with `repo_root`/`repo_name`
   and a `flow` graph. Declared **before** `/{slug}` so the literal path isn't
   captured as a slug. The flat `GET /api/sessions` now also carries
   `kind/parent_slug/phase_index/phase_label/depends_on` (flat-with-parent-ref).

3. **`GET /api/projects/epics`** — the same grouping scoped per project
   (filesystem-backed; the DB `projects` table and its `GET`/`PATCH` endpoints are untouched).

4. **Phase SSE events** — `diff_phase_events(prev_state, parsed)` (pure) derives
   `phase_started` / `phase_pr_opened` / `phase_completed` from a phase session's
   `execute`/`pr` stage transitions; each fires at most once. Wired into the
   watcher next to the existing `gate_reached` logic.

5. **Bridge** — a locking test confirms a per-Phase `session_id` (`…-pN`) round-trips
   through the bridge callbacks verbatim (no code change; spec "no structural change").

## Files

| File | Change |
|------|--------|
| `dashboard/backend/services/epic_flow.py` | new — flow graph assembly |
| `dashboard/backend/routers/sessions.py` | `GET /api/sessions/epics` + hierarchy fields on the flat list |
| `dashboard/backend/routers/projects.py` | `GET /api/projects/epics` |
| `dashboard/backend/watcher.py` | `diff_phase_events` + watcher wiring |
| `dashboard/bridge/tests/test_bridge.py` | per-Phase session_id round-trip lock |

## Tests

Run from `dashboard/`:

```bash
python -m pytest backend/tests/test_epic_flow.py backend/tests/test_router_sessions.py \
  backend/tests/test_router_projects.py backend/tests/test_sse.py \
  backend/tests/test_watcher.py bridge/tests/test_bridge.py -q
```

All Phase-2 logic is **DB-free testable**: `epic_flow` + `diff_phase_events` are pure
unit tests; the `/epics` routes are exercised via httpx `ASGITransport` against
filesystem `projects.json`. Full suite: **46 passed, 17 skipped** (live-DB tests, no
local Postgres), 1 pre-existing failure (`test_approve_pending_gate`, needs a live DB —
fails identically on the base branch).

## Consumed by

- **Phase 3** — frontend `EpicFlow`/`Phase` TS types are pinned to these response shapes.
- **Phase 4** — `EpicFlowView` renders `nodes`/`edges`; the store consumes the new SSE events.
