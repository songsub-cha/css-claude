# CSS Session Schema — canonical reference

Single source of truth for the runtime state the CSS pipeline keeps under
`<project>/.claude/css/`. Machine validation lives in
`tools/css_schema/schema.py` (+ `tools/css_schema/fixtures/`); this document is
the human-readable companion that names **every field, who writes it, and who
reads it**. Commands stay self-contained (each states the fields it touches);
consult this file when a field name or owner is ambiguous, and update it in the
same change that adds or renames a field.

## Files

| Path (under `<project>/.claude/css/`) | Purpose |
|---|---|
| `sessions/<slug>.json` | One pipeline session (Epic, child Phase, or kind-less legacy single-session) |
| `sessions/_active.json` | Convenience pointer to the most recent session (see below) |
| `plans/` | Rich Spec task artifacts (`{slug}-T{id}.md`, `{parent}-p{n}-T{id}.md`) and `phase-manifest-{slug}.json` |
| `reviews/` | Review reports + persisted advisory reports |
| `executions/` | Execution logs (`exec-log-{slug}-{ts}.md`) |
| `verifies/` | Verify aggregate + persisted code/security review reports |
| `locks/{slug}-{stage}.lock` | Stage locks (see Locking) |

`/css:wiki` is session-independent: it **reads** session files (ADR backfill) but never
writes them and never updates `_active.json`. Its lock is `locks/_project-wiki.lock`.

## Session fields

| Field | Written by | Notes |
|---|---|---|
| `slug` | interview / ship | kebab-case session id |
| `kind` | interview / ship / phase | `"epic"` or `"phase"`; **absent** = legacy single-session (detailed linear flow) |
| `single_phase` | phase | `true` → sub-threshold Epic runs the detailed linear flow |
| `idea` | interview / ship | original idea text (gh_sync issue title/body reads it) |
| `repo_root`, `repo_name` | interview | captured whenever absent |
| `base_branch` | interview (Epic/single) / phase (children) | worktree cut point and PR base default; children: stacking base |
| `config` | interview | merged user-over-bundled config (keys below) |
| `retries` | interview init; review/verify increment | `{review: n, verify: n}` loopback counters |
| `language_profile` | execute | `{language, test_command, coverage_command}` |
| `master_flow` | ship | `true` → stage commands skip their own gate prompts |
| `gates.gate2_pre_execute` | ship (incl. per-Phase step 13b) | `{state, source, reached_at, approved_at, approved_by}`; `/css:execute` requires `state == "approved"` under master flow |
| `gates.gate3_pre_pr` | ship (incl. per-Phase step 13d) | same shape + `draft`; `/css:pr` requires it under master flow |
| `github` | lib/gh_sync.sh | `{issue_number, issue_url, repo, project_item_id, adrs[], gate2, gate3}` |
| `parent_slug`, `parent_session`, `phase_index`, `phase_label`, `depends_on` | phase | child Phase identity; `parent_session` is the spec-resolution fallback |
| `child_slugs`, `phase_manifest` | phase | Epic-side fan-out record |

### `phases.<stage>`

Every stage records at least `{status, artifact, completed_at}`. Stage-specific
extras and their consumers:

| Stage | Extra fields | Read by |
|---|---|---|
| `interview` | — | plan/review/verify/document (spec resolution, incl. `parent_session` fallback) |
| `plan` | `level`, `task_count`, `batch_count` | phase threshold; review level gate |
| `phasing` | — | review pre-check for multi-Phase candidates |
| `review` | `verdict`, `level`, `rich_specs[]`, `advisories[]`, `findings {critical, high, medium, low}` | execute/verify consume the exact `rich_specs` list; gh_sync review summary reads `findings` |
| `execute` | `worktree`, `branch`, `base_branch`, `commit_count`, `test_summary {tests, passed, coverage_pct}` | verify/document/pr (worktree+branch); gh_sync execute summary |
| `verify` | `verdict`, `test_summary {tests, passed, coverage_pct}` | document requires `verdict == "PASS"`; gh_sync verify summary |
| `document` | — | pr body links the artifact |
| `pr` | artifact = PR URL | ship finalize; `/css:clean` merge check |
| `clean` | `removed_worktree`, `removed_branch` | housekeeping record (`/css:clean`) |

## Config keys (`session.config`)

Merged at interview: `~/.claude/css/config.json` (user) over the bundled
`config/default-config.json`. Defaults in parentheses.

- `review.max_loopback_attempts` (2) — review→plan loopback budget
- `verify.max_loopback_attempts` (3), `verify.coverage_threshold` (85)
- `execute.tdd_self_heal_max` (2) — debugger attempts per task
- `execute.worktree_parent` (null → `..`) — set `.worktrees` for an in-repo worktree
- `pr.default_base_branch` (null), `pr.default_draft` (false)
- `github.*` — read directly by `lib/gh_sync.sh` via its own config resolution
  (`$CSS_CONFIG` → user config → bundled), not through the session

## `_active.json`

`{latest_slug, active_epic, active_phase}` — a **convenience pointer with
last-writer-wins semantics**. Every stage command overwrites it. Parallel Phase
runs must pass `--session` explicitly and must not rely on `_active.json`
resolution while more than one run is active.

## Locking

`<project>/.claude/css/locks/{slug}-{stage}.lock` containing `{acquired_at}`.
A lock older than 60 minutes is stale — replace it and note the takeover. A
fresh lock from another run → abort with guidance. Locks are released on every
exit path, including loopbacks and cancels.
