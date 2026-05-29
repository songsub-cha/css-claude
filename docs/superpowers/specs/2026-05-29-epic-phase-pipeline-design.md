# CSS Pipeline — Epic / Phase Decomposition Design Spec

## Metadata

| Field | Value |
|-------|-------|
| Slug | `epic-phase-pipeline` |
| Date | 2026-05-29 |
| Author | brainstorming session (sub1904) |
| Status | Draft — pending user review |
| Affects | CSS pipeline (`commands/`, `agents/`, session schema) + Dashboard (`dashboard/`) |
| Supersedes | n/a (extends `2026-05-28-pipeline-dashboard-design.md`) |

## Overview

### Problem

`/css:ship` runs the whole pipeline (interview → plan → review → execute → verify → document → pr) as **one session = one branch = one PR**. For a large idea, plan explodes (the dashboard run produced 47 tasks / 7 batches), and execute runs all batches in a single session. Result: a ~1M-token session and a 51-commit mega-PR that is hard to review and hard to track on the dashboard.

**Root cause of the token blowup:** the two stages that expand to *full detail* — `plan` (bite-sized steps with complete code) and `review` (rich-specs: per-task RED scaffold + GREEN template) — both run at **Epic scope**. Splitting only `execute` per Phase does not help if `plan` and `review` still materialize the whole Epic's detail up front. The fix must defer detail expansion itself, not just the build.

The user's primary need is **observability**: seeing the work flow of a large feature as discrete, trackable units on the dashboard. PR-per-unit is the means to that end.

### Goals

1. Decompose a large idea into **Phases** that each ship as their own PR and appear as their own trackable unit on the dashboard.
2. **Keep the Epic session cheap**: only interview, a *skeleton* plan, phasing, and an *architecture* review run at Epic scope. The expensive full-detail stages — *detailed* plan and *rich-spec* review — plus all build stages run per Phase.
3. Support **dependency-ordered** Phase execution, and **parallel** execution of independent Phases across separate sessions/worktrees.
4. Give the dashboard an **Epic → Phase flow view** (nodes + dependency edges + per-Phase Stage/PR status).
5. Keep small ideas on the **existing single-session path** (no forced ceremony).

### Non-Goals (v0.1)

- Auto-detecting Phase boundaries with no human approval (phasing is user-approved).
- Cross-repo Epics (an Epic lives in one repo).
- Automatic conflict resolution between stacked Phase branches.
- Re-planning a Phase mid-flight without going back through the phasing gate.

## Terminology (resolves naming collisions)

The dashboard already uses "phase" for the 7 pipeline stages and "project" for a repo. We adopt a **4-level vocabulary** and rename accordingly:

| Term | Meaning | Was called | Lives in |
|------|---------|-----------|----------|
| **Project** | A repo (registered workspace) | `projects` table (unchanged) | `projects` table |
| **Epic** | One feature/idea = container of Phases | *(new)* | `sessions_history` rows tagged `kind=epic` |
| **Phase** | A shippable increment = 1 PR = 1 child session | *(new)* | `sessions_history` rows tagged `kind=phase` |
| **Stage** | A pipeline step within a session (interview, plan, phasing, review, execute, verify, document, pr); `plan`/`review` run at both Epic (coarse) and Phase (detailed) scope, and `phasing` is new | **"phase"** in code today | `phases` map inside a session JSON |

**Rename required:** in the dashboard, the type/field/column currently named `phase`/`PhaseName`/`currentPhase` (= the 7 steps) becomes **`stage`/`StageName`/`currentStage`**. The new feature-level unit takes the name **Phase**.

## Decisions Summary

| # | Decision | Choice |
|---|----------|--------|
| D1 | Vocabulary | Project / Epic / Phase / Stage (4 levels) — **locked** |
| D2 | DB shape | Add columns to `sessions_history`, **no separate `epics` table** — **locked** |
| D3 | document stage | **Per-Phase** docs (Epic-level aggregate README is optional, deferred) — **locked** |
| D4 | Plan granularity (two-level) | Epic runs a **skeleton plan** (coarse tasks grouped into batches, *no full code*); each Phase runs its **detailed bite-sized plan** in its own session |
| D5 | Where build stages run | detailed-plan / rich-spec-review / execute / verify / document / pr **per Phase (child session)** |
| D6 | Branch/PR strategy | One PR per Phase; dependent Phases use **stacked branches** (`--base <prev phase branch>`); independent Phases branch from the Epic base |
| D7 | When phasing triggers | Only when `task_count > 20` OR `batch_count > 4`; else legacy single-session path |
| D8 | Review granularity (two-level) | Epic runs an **architecture/coverage review** (skeleton vs spec + coarse Single-Specialist routing); **rich-specs (RED/GREEN) are authored per Phase** in the Phase session |
| D9 | Backward compat | A pre-existing session with no `kind` renders as a single-Phase Epic |
| D10 | Defer detail to Phase (cost) | The full-detail expansions (detailed plan + rich-specs) run **per Phase**, never at Epic scope — the primary fix for the ~1M-token blowup |

## Architecture

### Epic / Phase session model

```
Epic session  (kind=epic, slug=<epic>)  — cheap: no full-detail expansion
├─ Stage: interview       → spec
├─ Stage: plan (skeleton) → coarse tasks grouped into batches (NO code)
├─ Stage: phasing         → phase_manifest (NEW)        ← user-approved gate
├─ Stage: review (arch)   → architecture/coverage audit + coarse specialist routing
└─ child_slugs: [<epic>-p1, <epic>-p2, ...]

Phase session (kind=phase, slug=<epic>-p1, parent_slug=<epic>, depends_on=[])
├─ Stage: plan (detailed) → bite-sized full-code plan for THIS Phase's batches
├─ Stage: review (rich)   → rich-specs (RED/GREEN) for THIS Phase only
├─ Stage: execute         → worktree css/<epic>/p1, commits
├─ Stage: verify          → tests/coverage/review for this Phase
├─ Stage: document        → docs/<epic>/p1/...
└─ Stage: pr              → PR (base = epic base or prev phase branch)
```

- **Epic session** owns interview, *skeleton* plan, phasing, and *architecture* review. It never expands full detail and never builds.
- **Phase session** owns *detailed* plan → *rich-spec* review → execute → verify → document → pr — all scoped to this Phase's batches. It inherits the spec + skeleton plan + `phase_manifest` from the parent (cache-first), then expands detail only for its own slice.
- A Phase's `depends_on` lists the `phase_index`es it stacks on. Topological order = execution order. Phases with disjoint `depends_on` and no shared files can run in parallel.

### Design-coarse-at-Epic, expand-detail-per-Phase data flow

```
interview ────┐
plan(skeleton)┤ (Epic, once — cheap, no code)
phasing ──────┤  → phase_manifest: [{idx, label, batches:[...], depends_on:[...]}]
review(arch) ─┘  → architecture/coverage audit (coarse specialist routing)
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                     ▼
   Phase p1 session     Phase p2 session      Phase p3 session
   plan(detail)→        plan(detail)→          plan(detail)→
   review(rich)→        review(rich)→          review(rich)→
   execute→verify→      execute→verify→        execute→verify→
   document→pr (PR#a)   document→pr (PR#b)      document→pr (PR#c)
   base=epic-base       base=p1 (if dep)        base=p2 (if dep)
```

### Why detail is deferred to Phases

The ~1M-token blowup came from materializing the whole Epic's **detail** up front — `plan`'s full-code steps and `review`'s rich-specs (RED/GREEN per task). Deferring both to per-Phase sessions caps each session's working set to one Phase's slice. What stays at Epic scope is only the **coarse, coherence-critical** work: one spec, one skeleton plan, one phasing decision, and one architecture review (so Phases don't contradict each other). The detailed plan + rich-specs are then authored inside each Phase session, cache-fed by the Epic's skeleton + manifest.

## Session JSON Schema Changes

### Epic session (new `kind`)

```jsonc
{
  "slug": "epic-phase-pipeline",
  "kind": "epic",                       // NEW
  "idea": "...",
  "master_flow": true,
  "phases": {                           // = Epic-scope Stages: interview / plan(skeleton) / phasing / review(arch)
    "interview": { "status": "completed", "artifact": "..." },
    "plan":      { "status": "completed", "level": "skeleton", "artifact": "...", "task_count": 47, "batch_count": 7 },
    "phasing":   { "status": "completed", "artifact": ".../phase-manifest-<epic>.json" }, // NEW stage
    "review":    { "status": "completed", "level": "architecture", "verdict": "PASS" } // NO rich-specs at Epic
  },
  "phase_manifest": [                   // NEW
    { "idx": 1, "label": "DB + bridge foundation", "batches": [1,2], "depends_on": [] },
    { "idx": 2, "label": "API layer",              "batches": [3,4], "depends_on": [1] },
    { "idx": 3, "label": "UI",                     "batches": [5,6], "depends_on": [2] }
  ],
  "child_slugs": ["epic-phase-pipeline-p1", "epic-phase-pipeline-p2", "epic-phase-pipeline-p3"] // NEW
}
```

### Phase (child) session (new `kind`)

```jsonc
{
  "slug": "epic-phase-pipeline-p1",
  "kind": "phase",                      // NEW
  "parent_slug": "epic-phase-pipeline", // NEW
  "phase_index": 1,                     // NEW
  "phase_label": "DB + bridge foundation", // NEW
  "depends_on": [],                     // NEW (phase_index list)
  "base_branch": "main",                // NEW: branch this Phase forks from.
                                        // depends_on=[] → the branch ship launched from (e.g. main);
                                        // depends_on=[k] → css/<epic>/p<k> (stacked)
  "phases": {                           // = Phase-scope Stages: plan(detail) / review(rich) / execute / verify / document / pr
    "plan":     { "status": "...", "level": "detailed", "artifact": "docs/superpowers/plans/<epic>-p1.md", "task_count": 13 },
    "review":   { "status": "...", "level": "rich-spec", "verdict": "...", "rich_specs": [".claude/css/plans/<epic>-p1-T*.md"] },
    "execute":  { "status": "...", "worktree": "../<repo>-css-<epic>-p1", "branch": "css/<epic>/p1" },
    "verify":   { "status": "...", "verdict": "..." },
    "document": { "status": "...", "artifact": "docs/<epic>/p1/README.md" },
    "pr":       { "status": "...", "artifact": "<PR URL>" }
  }
}
```

- `_active.json` gains `active_epic` and `active_phase` alongside `latest_slug`.
- Backward compat: a legacy session (no `kind`) is treated as `kind=epic` with an implicit single Phase.

## CSS Pipeline Command Modifications

### `commands/plan.md` (two-level)

- Detects level from session `kind`: **Epic** (`kind=epic`) → produce a **skeleton plan** (coarse task titles grouped into batches with rough file targets, *no per-step code* — this is the cheap artifact phasing consumes). **Phase** (`kind=phase`) → produce a **detailed bite-sized plan** (full code per step) scoped to that Phase's batches only, written to `docs/superpowers/plans/<epic>-p<n>.md`.
- Records `phases.plan.level = "skeleton" | "detailed"`.

### NEW `commands/phase.md` (phasing stage)

- Input: plan + batches from the Epic session.
- Groups batches into Phases with `depends_on` edges; presents the proposed `phase_manifest` and asks for approval (**new gate**).
- Trigger guard: only runs when `task_count > 20 OR batch_count > 4`. Below threshold → writes a single-Phase manifest automatically and proceeds (legacy behavior).
- Output: `.claude/css/plans/phase-manifest-<epic>.json`; updates Epic session `phases.phasing` + `phase_manifest` + `child_slugs`.

### `commands/ship.md` (orchestrator rework)

- Epic-level (once): interview → plan(skeleton) → phasing. If multi-Phase:
  1. Run the Epic **architecture review** (coarse routing, **no rich-specs**).
  2. Create child Phase sessions from `phase_manifest`.
  3. Walk Phases in topological order. For each child: plan(detailed) → review(rich-spec) → execute → verify → document → pr (its own PR).
  4. Gate 2 (pre-execute) and Gate 3 (pre-pr) become **per-Phase** (batched approval option in dashboard).
  5. Independent Phases may be dispatched to separate sessions/worktrees for parallel runs.
- Single-Phase Epics keep the current linear flow (skeleton + detailed collapse into one plan/review pass).

### `commands/review.md` + `agents/reviewer.md` (two-level)

- **Epic level** (`kind=epic`): an **architecture/coverage review** — audit the skeleton plan against the spec, build the coverage matrix with a **Phase column** (every skeleton task tagged with its `phase_index` from `phase_manifest`), and decide **coarse** Single-Specialist routing per Phase. **No rich-specs produced here.**
- **Phase level** (`kind=phase`): the existing rich-spec dispatch — specialists author per-task RED scaffold + GREEN template for **this Phase's tasks only**, written to `.claude/css/plans/<epic>-p<n>-T*.md`. This is the cache `/css:execute` reads.

### `commands/execute.md` + `agents/executor.md`

- New arg `--phase <n>` (or operate on a child slug directly).
- Reads the **Phase's detailed plan** (`phases.plan.artifact`) and the **Phase's rich-specs** (produced by that Phase's own `review` stage — not the Epic).
- Worktree `../<repo>-css-<epic>-p<n>`, branch `css/<epic>/p<n>`, created from `base_branch`.
- rich-spec readiness check filtered to the Phase's tasks.
- exec-log keyed by Phase.

### `commands/verify.md` / `commands/document.md`

- Operate on the Phase's worktree/branch.
- verify maps only the acceptance criteria assigned to this Phase.
- document writes `docs/<epic>/p<n>/` (per-Phase, D3). Optional Epic aggregate README is deferred.

### `commands/pr.md` + `agents/pr-creator.md`

- Per-Phase PR. New `--base <branch>`: dependent Phase PRs target the previous Phase branch (**stacked PR**); independent Phases target the Epic base.
- PR body links the Epic spec, lists this Phase's acceptance criteria, notes `Stacked on #<N>` and cross-links sibling Phase PRs.

### Locking / `_active.json`

- Lock granularity moves from per-slug to **per-Phase** so sibling Phases don't block each other.
- `_active.json` tracks `active_epic` + `active_phase`.

### Branch & PR strategy (stacked)

```
main
 └─ css/<epic>/p1            → PR #a  (base: main/epic-base)
     └─ css/<epic>/p2        → PR #b  (base: css/<epic>/p1)   depends_on [1]
         └─ css/<epic>/p3    → PR #c  (base: css/<epic>/p2)   depends_on [2]
```

Merge order follows the stack. Independent Phases (`depends_on: []`) branch from the Epic base and open PRs against `main` directly.

## Dashboard Data Model (PostgreSQL)

Per D2, **extend `sessions_history`** (migration `alembic/versions/0002_phase_hierarchy.py`):

| Column | Type | Notes |
|--------|------|-------|
| `kind` | `text` | `'epic' \| 'phase'`; default `'epic'` for backfill (legacy rows) |
| `parent_slug` | `text NULL` | self-reference by slug within a project |
| `phase_index` | `integer NULL` | 1-based; null for epics |
| `phase_label` | `text NULL` | human label |
| `depends_on` | `jsonb` default `[]` | list of phase_index |

- Add `CHECK (kind IN ('epic','phase'))` and an index on `(project_id, parent_slug)`.
- `ParsedSession` (live reader) gains the same fields; live sessions are grouped by `parent_slug`.
- Legacy rows backfill to `kind='epic'`, `parent_slug=NULL` → render as single-Phase Epics (D9).

## Dashboard Backend Changes

| File | Change |
|------|--------|
| `services/session_reader.py` | Parse `kind`, `parent_slug`, `phase_index`, `phase_label`, `depends_on`; group children under parent |
| `services/` (new) `epic_flow.py` | Assemble Epic → Phase graph: nodes (Phase + current Stage + PR status) + dependency edges |
| `routers/sessions.py` | Return hierarchical (Epic + child Phases) or flat-with-parent-ref |
| `routers/projects.py` | Epic grouping endpoint per project |
| `sse.py` / `routers/sse_router.py` | New events: `phase_started`, `phase_completed`, `phase_pr_opened` |
| `bridge.py` | Minimal: queue event `command`/`session_id` carry the Phase slug; no structural change |

## Dashboard Frontend Changes

| File | Change |
|------|--------|
| `types.ts` | Rename `PhaseName`→`StageName`, `currentPhase`→`currentStage`. Add `Phase`, `EpicFlow` types; `Session` gains `kind`, `parentSlug`, `phaseIndex`, `dependsOn`. New SSE variants |
| `components/KanbanBoard.tsx` | Group cards into **Epic swimlanes**; cards = Phases. **Column model needs rework** (Phase B): Epics traverse interview/plan/phasing/review; Phases traverse plan/review/execute/verify/document/pr — `phasing` is a new column and `plan`/`review` now appear at two scopes. Resolve the exact column set in Phase B |
| `components/` (new) `EpicFlowView.tsx` | **Core deliverable**: Phase nodes + dependency edges + per-Phase Stage/PR status (the "work flow" view) |
| `components/SessionCard.tsx` | Show phase label/index, PR link, `stacked on` indicator |
| `stores/sessionsStore.ts`, `projectsStore.ts` | Group by `parentSlug`; derive the Phase graph |
| `components/HistoryView.tsx` | Group archived sessions by Epic |
| `components/DetailSlideOver.tsx` | Show Phase deps, sibling Phases, stacked-PR chain |

## Data Flow (end-to-end)

1. `/css:ship "<big idea>"` → Epic session created.
2. interview → plan **(skeleton: 47 coarse tasks / 7 batches, no code)**.
3. phasing → user approves 3 Phases with deps → `phase_manifest` + 3 child sessions written.
4. review **(Epic, architecture)** → coverage matrix tags each skeleton task with its Phase; coarse specialist routing. **No rich-specs yet.**
5. Per Phase (topological): plan **(detailed, this Phase only)** → review **(rich-specs, this Phase only)** → execute (own worktree/branch) → verify → document (`docs/<epic>/p<n>`) → pr (stacked).
6. Each session JSON write is picked up by the dashboard watcher → SSE → Epic Flow view updates live; each Phase shows its current Stage and PR.

## Error Handling

- **Phasing rejected** by user → loop back to plan or edit manifest; no children created until approved.
- **Phase verify fails** → loops within that Phase (existing `retry_counters.verify`), does not block sibling independent Phases.
- **Stacked base not merged yet** → PR opens against the predecessor branch; a warning records "depends on unmerged #N".
- **Parallel file conflict** → out of scope for auto-resolution (D Non-Goal); phasing should avoid assigning the same files to parallel Phases (reviewer flags overlap).
- **Corrupt/partial child session** → `parse_session_file` already returns None and logs; Epic still renders with available Phases.

## Testing Strategy

- **Pipeline**: unit-test the phasing trigger threshold, manifest generation, topological ordering, and slug/branch derivation. Fixture: a plan with >20 tasks producing a 3-Phase manifest with a dependency chain.
- **Schema**: migration up/down test for `0002`; backfill correctness (legacy → single-Phase Epic).
- **Backend**: `session_reader` grouping; `epic_flow` graph assembly (edges match `depends_on`); SSE emission for new events.
- **Frontend**: `EpicFlowView` renders nodes/edges from a mocked Epic; swimlane grouping; backward-compat render of a legacy `kind`-less session.
- **E2E (deferred, like dashboard v0.1)**: full ship of a multi-Phase Epic.

## Acceptance Criteria

1. A `/css:ship` with `task_count > 20` produces an Epic session + a user-approved `phase_manifest` + N child Phase sessions.
2. Each Phase produces its own worktree, branch `css/<epic>/p<n>`, and PR; dependent Phases stack via `--base`.
3. At Epic scope, interview + skeleton-plan + phasing + architecture-review run exactly once and produce **no** full-code plan and **no** rich-specs. At Phase scope, detailed-plan + rich-spec-review + execute + verify + document + pr run once per Phase.
4. document writes `docs/<epic>/p<n>/` per Phase.
5. `sessions_history` carries `kind/parent_slug/phase_index/phase_label/depends_on`; migration backfills legacy rows to single-Phase Epics with no UI breakage.
6. Dashboard shows an Epic → Phase flow view with dependency edges and per-Phase Stage/PR status, updating live via SSE.
7. A small idea (`task_count ≤ 20`) still ships via the single-session path unchanged.
8. **Cost isolation**: an Epic session's artifacts contain no Phase's detailed plan or rich-specs; a Phase session's working set is limited to its own slice (skeleton + manifest + its own detail).

## Build Order / Decomposition Note

This design itself decomposes cleanly into two build Phases (dogfooding):

- **Phase A — Pipeline**: schema, `commands/phase.md`, **two-level `plan` + `review`** (skeleton/architecture at Epic; detailed/rich-spec at Phase), ship orchestration, execute/verify/document/pr + agents, locking. (Produces the new session JSON shape.)
- **Phase B — Dashboard**: migration `0002`, backend reader/flow/routers/SSE, frontend rename + `EpicFlowView` + swimlanes. (Consumes the new shape; depends on Phase A.)

`writing-plans` should split along this boundary.

## Risks & Open Questions

- **Stacked-PR friction**: rebasing a lower Phase after review churns the stack. Mitigation: keep Phases small; document merge order.
- **Phasing quality**: bad Phase boundaries (cross-cutting deps) reduce the benefit. Mitigation: reviewer flags file-overlap between parallel Phases.
- **Dashboard rename blast radius**: `phase→stage` rename touches many files; do it as a mechanical first commit in Phase B.
- **Open**: Should the Epic get an aggregate README at the end (currently deferred under D3)? Revisit after first real multi-Phase run.

## References

- `2026-05-28-pipeline-dashboard-design.md` (dashboard v0.1)
- `commands/*.md`, `agents/css/*.md`
- `dashboard/backend/models.py`, `dashboard/frontend/src/types.ts`
