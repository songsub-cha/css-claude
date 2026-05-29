# Dashboard Epic/Phase View — Phase 1: Backend foundation

Part of Epic **`dashboard-epic-phase-view`** (Phase B of the [Epic/Phase pipeline design](../../superpowers/specs/2026-05-29-epic-phase-pipeline-design.md)).
Phase 1 of 4 · branch `css/dashboard-epic-phase-view/p1` (base `css/epic-phase-pipeline`).

## What this Phase adds

The persistence + read foundation the rest of the dashboard Epic/Phase view builds on:

1. **DB schema** — migration `0002_phase_hierarchy` extends `sessions_history` (D2: extend, no separate `epics` table) with five columns:

   | Column | Type | Notes |
   |--------|------|-------|
   | `kind` | `text NOT NULL DEFAULT 'epic'` | `CHECK (kind IN ('epic','phase'))` |
   | `parent_slug` | `text NULL` | self-reference by slug within a project |
   | `phase_index` | `integer NULL` | 1-based; null for epics |
   | `phase_label` | `text NULL` | human label |
   | `depends_on` | `jsonb NOT NULL DEFAULT '[]'` | list of `phase_index` |

   Plus index `idx_history_project_parent (project_id, parent_slug)`. Legacy rows
   backfill to `kind='epic'`, `parent_slug=NULL`, `depends_on=[]` automatically via
   the column defaults — they render as single-Phase Epics (**D9** backward-compat).

2. **ORM model** — `SessionHistory` mirrors the new columns, the `kind` CHECK, and the index.

3. **Session reader** — `ParsedSession` parses the hierarchy fields with a legacy
   fallback (`kind`-less → epic) and exposes `is_phase`. New
   `group_sessions_by_epic(sessions) -> {slug: EpicGroup}` groups child Phases under
   their Epic, orders them by `phase_index`, and tolerates orphan phases (missing
   parent → `EpicGroup(epic=None)`).

## Files

| File | Change |
|------|--------|
| `dashboard/alembic/versions/0002_phase_hierarchy.py` | new migration (up/down) |
| `dashboard/backend/models.py` | `SessionHistory` hierarchy columns + CHECK + index |
| `dashboard/backend/services/session_reader.py` | parse fields + `EpicGroup` + `group_sessions_by_epic` |

## Tests

Run from `dashboard/`:

```bash
python -m pytest backend/tests/test_session_reader.py backend/tests/test_models.py backend/tests/test_migration.py -q
```

- `test_session_reader.py` — 8/8: hierarchy parse (T3), legacy fallback (D9), Epic
  grouping + ordering + orphan tolerance (T4).
- `test_models.py::test_session_history_hierarchy_columns_metadata` — ORM metadata
  (no DB) asserts the columns/constraint/index.
- `test_migration.py::test_0002_revision_chains_onto_0001` and
  `::test_0002_upgrade_emits_hierarchy_ddl` — verify the revision chain and emitted
  DDL **without** a live database (via a stubbed `op.execute`).

Live-DB tests (full migration up/down, ORM CRUD) **skip** unless `TEST_DATABASE_URL`
points at a Postgres instance (or Docker is available for testcontainers).

## Consumed by

- **Phase 2** — `epic_flow` graph + routers + SSE read `group_sessions_by_epic`.
- **Phase 4** — the frontend `EpicFlowView` / swimlanes render the grouped shape.
