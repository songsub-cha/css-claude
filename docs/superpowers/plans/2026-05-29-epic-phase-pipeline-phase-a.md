# Epic/Phase Pipeline — Phase A (Pipeline) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the CSS pipeline decompose a large idea into an Epic (interview/plan/phasing/review once) plus per-Phase build sessions (execute/verify/document/pr), each producing its own stacked PR.

**Architecture:** Introduce an executable schema contract (`tools/css_schema/`) that defines and validates the new Epic/Phase session JSON + `phase_manifest`, plus pure derivation helpers (slug/branch/base/threshold). The command + agent markdown prompts are then edited to produce/consume that contract; their behavior is verified against the validator and fixtures rather than classic unit tests.

**Tech Stack:** Python 3 stdlib (`unittest`, `json`) for the contract; Markdown for command/agent prompts. No new third-party dependencies.

**Scope:** Phase A only. The dashboard (Phase B) consumes this schema and is planned in a separate session after the dashboard PR #1 merges.

---

## File Structure

**New (executable contract + fixtures):**
- `tools/css_schema/__init__.py` — package exports
- `tools/css_schema/derive.py` — pure functions: `should_phase`, `phase_slug`, `phase_branch`, `base_branch_for`
- `tools/css_schema/schema.py` — `validate_session`, `validate_manifest`, `validate_active`, `SchemaError`
- `tools/css_schema/test_derive.py` — tests for derive.py
- `tools/css_schema/test_schema.py` — tests for schema.py
- `tools/css_schema/fixtures/valid_manifest.json`
- `tools/css_schema/fixtures/epic_session.json`
- `tools/css_schema/fixtures/phase_session.json`

**New (pipeline stage):**
- `commands/phase.md` — phasing stage (`/css:phase`)

**Modified (commands):** `commands/{ship,plan,review,execute,verify,document,pr}.md`
**Modified (agents):** `agents/{reviewer,executor,pr-creator}.md`

**Test runner (from repo root):** `python -m unittest discover -s tools -t tools -v`

> Convention locked here: `phase_slug = "<epic>-p<idx>"`, `phase_branch = "css/<epic>/p<idx>"`, epic base defaults to `main`.

---

## Task 1: Phasing threshold + slug/branch derivation

**Files:**
- Create: `tools/css_schema/__init__.py`
- Create: `tools/css_schema/derive.py`
- Test: `tools/css_schema/test_derive.py`

- [ ] **Step 1: Write the failing test**

```python
# tools/css_schema/test_derive.py
import unittest
from css_schema.derive import should_phase, phase_slug, phase_branch, base_branch_for

MANIFEST = [
    {"idx": 1, "label": "foundation", "batches": [1, 2], "depends_on": []},
    {"idx": 2, "label": "api",        "batches": [3],    "depends_on": [1]},
    {"idx": 3, "label": "ui",         "batches": [4, 5], "depends_on": [2]},
]

class TestDerive(unittest.TestCase):
    def test_should_phase_threshold(self):
        self.assertFalse(should_phase(20, 4))   # at limit -> single session
        self.assertTrue(should_phase(21, 1))    # task_count > 20
        self.assertTrue(should_phase(5, 5))     # batch_count > 4

    def test_phase_slug_and_branch(self):
        self.assertEqual(phase_slug("epic-x", 2), "epic-x-p2")
        self.assertEqual(phase_branch("epic-x", 2), "css/epic-x/p2")

    def test_base_branch_independent_phase_uses_epic_base(self):
        self.assertEqual(base_branch_for(MANIFEST, 1, "epic-x"), "main")

    def test_base_branch_dependent_phase_stacks_on_latest_dep(self):
        self.assertEqual(base_branch_for(MANIFEST, 3, "epic-x"), "css/epic-x/p2")

    def test_base_branch_custom_epic_base(self):
        self.assertEqual(base_branch_for(MANIFEST, 1, "epic-x", epic_base="develop"), "develop")

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest discover -s tools -t tools -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'css_schema.derive'`

- [ ] **Step 3: Write minimal implementation**

```python
# tools/css_schema/__init__.py
"""CSS pipeline schema contract: validation + derivation helpers."""
```

```python
# tools/css_schema/derive.py
"""Pure derivation helpers for Epic/Phase slugs, branches, and the phasing trigger."""
from __future__ import annotations


def should_phase(task_count: int, batch_count: int) -> bool:
    """True when an idea is large enough to split into Phases (D7)."""
    return task_count > 20 or batch_count > 4


def phase_slug(epic_slug: str, idx: int) -> str:
    return f"{epic_slug}-p{idx}"


def phase_branch(epic_slug: str, idx: int) -> str:
    return f"css/{epic_slug}/p{idx}"


def _find_phase(manifest: list[dict], idx: int) -> dict:
    for p in manifest:
        if p["idx"] == idx:
            return p
    raise KeyError(f"phase idx {idx} not in manifest")


def base_branch_for(manifest: list[dict], idx: int, epic_slug: str,
                    epic_base: str = "main") -> str:
    """Branch a Phase forks from. Independent (depends_on=[]) -> epic_base;
    otherwise stack on the highest-indexed dependency (linear stack)."""
    deps = _find_phase(manifest, idx).get("depends_on", [])
    if not deps:
        return epic_base
    return phase_branch(epic_slug, max(deps))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest discover -s tools -t tools -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add tools/css_schema/__init__.py tools/css_schema/derive.py tools/css_schema/test_derive.py
git commit -m "feat(css-schema): add phasing threshold + slug/branch derivation"
```

---

## Task 2: `phase_manifest` validator (DAG invariant)

**Files:**
- Create: `tools/css_schema/schema.py`
- Test: `tools/css_schema/test_schema.py` (manifest portion)

- [ ] **Step 1: Write the failing test**

```python
# tools/css_schema/test_schema.py
import unittest
from css_schema.schema import validate_manifest, SchemaError

VALID = [
    {"idx": 1, "label": "foundation", "batches": [1, 2], "depends_on": []},
    {"idx": 2, "label": "api",        "batches": [3],    "depends_on": [1]},
]

class TestManifest(unittest.TestCase):
    def test_valid_manifest_passes(self):
        validate_manifest(VALID)  # should not raise

    def test_empty_manifest_rejected(self):
        with self.assertRaises(SchemaError):
            validate_manifest([])

    def test_duplicate_idx_rejected(self):
        bad = [dict(VALID[0]), dict(VALID[0])]
        with self.assertRaises(SchemaError):
            validate_manifest(bad)

    def test_empty_batches_rejected(self):
        bad = [{"idx": 1, "label": "x", "batches": [], "depends_on": []}]
        with self.assertRaises(SchemaError):
            validate_manifest(bad)

    def test_forward_dependency_rejected(self):
        # depends_on must reference a smaller idx (acyclic + topological)
        bad = [{"idx": 1, "label": "x", "batches": [1], "depends_on": [2]},
               {"idx": 2, "label": "y", "batches": [2], "depends_on": []}]
        with self.assertRaises(SchemaError):
            validate_manifest(bad)

    def test_unknown_dependency_rejected(self):
        bad = [{"idx": 1, "label": "x", "batches": [1], "depends_on": [9]}]
        with self.assertRaises(SchemaError):
            validate_manifest(bad)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest discover -s tools -t tools -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'css_schema.schema'`

- [ ] **Step 3: Write minimal implementation**

```python
# tools/css_schema/schema.py
"""Validation for Epic/Phase session JSON, phase_manifest, and _active.json."""
from __future__ import annotations


class SchemaError(ValueError):
    """Raised when a CSS session/manifest artifact violates the contract."""


def validate_manifest(manifest: object) -> None:
    if not isinstance(manifest, list) or not manifest:
        raise SchemaError("phase_manifest must be a non-empty list")
    seen: set[int] = set()
    for p in manifest:
        if not isinstance(p, dict):
            raise SchemaError("each phase must be an object")
        idx = p.get("idx")
        if not isinstance(idx, int) or idx < 1:
            raise SchemaError(f"phase idx must be int >= 1, got {idx!r}")
        if idx in seen:
            raise SchemaError(f"duplicate phase idx {idx}")
        seen.add(idx)
        if not isinstance(p.get("label"), str) or not p["label"].strip():
            raise SchemaError(f"phase {idx} needs a non-empty label")
        if not isinstance(p.get("batches"), list) or not p["batches"]:
            raise SchemaError(f"phase {idx} needs a non-empty batches list")
        deps = p.get("depends_on", [])
        if not isinstance(deps, list):
            raise SchemaError(f"phase {idx} depends_on must be a list")
        for d in deps:
            if d not in seen or d >= idx:
                # must reference an already-seen, strictly-smaller idx -> acyclic
                raise SchemaError(
                    f"phase {idx} depends_on {d}: must be an existing smaller idx")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest discover -s tools -t tools -v`
Expected: PASS (5 derive + 6 manifest tests)

- [ ] **Step 5: Commit**

```bash
git add tools/css_schema/schema.py tools/css_schema/test_schema.py
git commit -m "feat(css-schema): validate phase_manifest as a DAG with topological idx order"
```

---

## Task 3: Session validator (Epic + Phase) with backward compat

**Files:**
- Modify: `tools/css_schema/schema.py`
- Test: `tools/css_schema/test_schema.py` (add session cases)

- [ ] **Step 1: Write the failing test (append to test_schema.py)**

```python
from css_schema.schema import validate_session

class TestSession(unittest.TestCase):
    def test_epic_session_ok(self):
        validate_session({"slug": "e", "kind": "epic",
                          "phases": {"interview": {"status": "completed"}}})

    def test_phase_session_ok(self):
        validate_session({"slug": "e-p1", "kind": "phase", "parent_slug": "e",
                          "phase_index": 1, "depends_on": [], "base_branch": "main",
                          "phases": {"execute": {"status": "pending"}}})

    def test_legacy_session_without_kind_treated_as_epic(self):
        # backward compat (D9): no 'kind' -> valid single-Phase epic
        validate_session({"slug": "old", "phases": {"interview": {"status": "completed"}}})

    def test_phase_session_missing_parent_rejected(self):
        with self.assertRaises(SchemaError):
            validate_session({"slug": "e-p1", "kind": "phase",
                              "phase_index": 1, "base_branch": "main", "phases": {}})

    def test_bad_kind_rejected(self):
        with self.assertRaises(SchemaError):
            validate_session({"slug": "e", "kind": "nonsense", "phases": {}})

    def test_missing_slug_rejected(self):
        with self.assertRaises(SchemaError):
            validate_session({"kind": "epic", "phases": {}})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest discover -s tools -t tools -v`
Expected: FAIL — `ImportError: cannot import name 'validate_session'`

- [ ] **Step 3: Write minimal implementation (append to schema.py)**

```python
_VALID_KINDS = {"epic", "phase"}
_PHASE_REQUIRED = ("parent_slug", "phase_index", "base_branch")


def validate_session(obj: dict) -> None:
    if not isinstance(obj, dict):
        raise SchemaError("session must be an object")
    if not obj.get("slug"):
        raise SchemaError("session requires a non-empty slug")
    kind = obj.get("kind", "epic")  # D9: legacy (no kind) -> epic
    if kind not in _VALID_KINDS:
        raise SchemaError(f"kind must be one of {_VALID_KINDS}, got {kind!r}")
    if "phases" not in obj or not isinstance(obj["phases"], dict):
        raise SchemaError("session requires a 'phases' object")
    if "phase_manifest" in obj:
        validate_manifest(obj["phase_manifest"])
    if kind == "phase":
        for f in _PHASE_REQUIRED:
            if f not in obj:
                raise SchemaError(f"phase session missing required field {f!r}")
        if not isinstance(obj["phase_index"], int) or obj["phase_index"] < 1:
            raise SchemaError("phase_index must be int >= 1")
        if not isinstance(obj.get("depends_on", []), list):
            raise SchemaError("depends_on must be a list")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest discover -s tools -t tools -v`
Expected: PASS (all prior + 6 session tests)

- [ ] **Step 5: Commit**

```bash
git add tools/css_schema/schema.py tools/css_schema/test_schema.py
git commit -m "feat(css-schema): validate epic/phase sessions with legacy backward-compat"
```

---

## Task 4: `_active.json` + fixtures (executable examples)

**Files:**
- Modify: `tools/css_schema/schema.py` (add `validate_active`)
- Create: `tools/css_schema/fixtures/{valid_manifest,epic_session,phase_session}.json`
- Test: `tools/css_schema/test_schema.py` (active + fixture round-trip)

- [ ] **Step 1: Write the failing test (append)**

```python
import json, pathlib
from css_schema.schema import validate_active

FX = pathlib.Path(__file__).parent / "fixtures"

class TestActiveAndFixtures(unittest.TestCase):
    def test_active_minimal(self):
        validate_active({"latest_slug": "e"})

    def test_active_with_epic_and_phase(self):
        validate_active({"latest_slug": "e-p1", "active_epic": "e", "active_phase": 1})

    def test_active_requires_latest_slug(self):
        with self.assertRaises(SchemaError):
            validate_active({})

    def test_fixtures_are_valid(self):
        validate_manifest(json.loads((FX / "valid_manifest.json").read_text()))
        validate_session(json.loads((FX / "epic_session.json").read_text()))
        validate_session(json.loads((FX / "phase_session.json").read_text()))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest discover -s tools -t tools -v`
Expected: FAIL — `ImportError: cannot import name 'validate_active'` (and missing fixture files)

- [ ] **Step 3: Write implementation + fixtures**

```python
# append to schema.py
def validate_active(obj: dict) -> None:
    if not isinstance(obj, dict) or not obj.get("latest_slug"):
        raise SchemaError("_active.json requires a non-empty latest_slug")
    if "active_phase" in obj and not isinstance(obj["active_phase"], int):
        raise SchemaError("active_phase must be an int when present")
```

```json
// tools/css_schema/fixtures/valid_manifest.json
[
  {"idx": 1, "label": "DB + bridge foundation", "batches": [1, 2], "depends_on": []},
  {"idx": 2, "label": "API layer",              "batches": [3, 4], "depends_on": [1]},
  {"idx": 3, "label": "UI",                     "batches": [5, 6], "depends_on": [2]}
]
```

```json
// tools/css_schema/fixtures/epic_session.json
{
  "slug": "epic-phase-pipeline",
  "kind": "epic",
  "idea": "example epic",
  "phases": {
    "interview": {"status": "completed", "artifact": "docs/superpowers/specs/x.md"},
    "plan": {"status": "completed", "level": "skeleton", "task_count": 47, "batch_count": 7},
    "phasing": {"status": "completed", "artifact": ".claude/css/plans/phase-manifest-epic-phase-pipeline.json"},
    "review": {"status": "completed", "level": "architecture", "verdict": "PASS"}
  },
  "phase_manifest": [
    {"idx": 1, "label": "DB + bridge foundation", "batches": [1, 2], "depends_on": []},
    {"idx": 2, "label": "API layer",              "batches": [3, 4], "depends_on": [1]},
    {"idx": 3, "label": "UI",                     "batches": [5, 6], "depends_on": [2]}
  ],
  "child_slugs": ["epic-phase-pipeline-p1", "epic-phase-pipeline-p2", "epic-phase-pipeline-p3"]
}
```

```json
// tools/css_schema/fixtures/phase_session.json
{
  "slug": "epic-phase-pipeline-p2",
  "kind": "phase",
  "parent_slug": "epic-phase-pipeline",
  "phase_index": 2,
  "phase_label": "API layer",
  "depends_on": [1],
  "base_branch": "css/epic-phase-pipeline/p1",
  "phases": {
    "plan": {"status": "completed", "level": "detailed", "artifact": "docs/superpowers/plans/epic-phase-pipeline-p2.md", "task_count": 9},
    "review": {"status": "completed", "level": "rich-spec", "verdict": "PASS", "rich_specs": [".claude/css/plans/epic-phase-pipeline-p2-T01.md"]},
    "execute": {"status": "pending", "worktree": "../repo-css-epic-phase-pipeline-p2", "branch": "css/epic-phase-pipeline/p2"},
    "verify": {"status": "pending"},
    "document": {"status": "pending", "artifact": "docs/epic-phase-pipeline/p2/README.md"},
    "pr": {"status": "pending"}
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest discover -s tools -t tools -v`
Expected: PASS (all)

- [ ] **Step 5: Commit**

```bash
git add tools/css_schema/schema.py tools/css_schema/fixtures/ tools/css_schema/test_schema.py
git commit -m "feat(css-schema): add _active validator and canonical epic/phase/manifest fixtures"
```

---

## Task 5: New stage `commands/phase.md`

**Files:**
- Create: `commands/phase.md`

Reference existing command shape: `commands/plan.md` (frontmatter, Steps, `<self_check>`, trailing `$ARGUMENTS`).

- [ ] **Step 1: Write the command file**

````markdown
---
description: Group plan batches into dependency-ordered Phases and create child Phase sessions (CSS pipeline stage 2.5)
argument-hint: "[--slug <name>]"
---

# /css:phase

Decide the Phase decomposition for an Epic. Runs between `/css:plan` and `/css:review`.

## Steps

1. **Parse arguments**: `--slug` (the Epic slug). Default from `_active.json.latest_slug`.

2. **Resolve session**; require `phases.plan.status == completed`. Read `task_count` and `batch_count`.

3. **Threshold gate** (uses `tools/css_schema/derive.py:should_phase`):
   - If `should_phase(task_count, batch_count)` is **false** → write a single-Phase manifest
     `[{"idx":1,"label":"<idea>","batches":[1..batch_count],"depends_on":[]}]`, mark
     `kind:"epic"` minimal, set `child_slugs:[]` (legacy single-session path), and announce
     "단일 세션 경로 (임계치 미만)". Skip to step 7.
   - Else continue.

4. **Propose `phase_manifest`**: group batches into 2–5 Phases with `depends_on` edges
   (vertical slices ordered; independent slices `depends_on:[]`). Present the proposed
   manifest to the user via AskUserQuestion: "[승인 / 수정 / 취소]". On 수정, take edits and re-present.

5. **Validate** the approved manifest with `python -c "import json,sys; from css_schema.schema import validate_manifest; validate_manifest(json.load(open(sys.argv[1])))" <manifest.json>` (run from `tools/`). Abort on SchemaError.

6. **Persist**:
   - Write `.claude/css/plans/phase-manifest-{slug}.json`.
   - Update Epic session: `kind:"epic"`, `phases.phasing = {status: completed, artifact: <manifest path>}`,
     `phase_manifest = <manifest>`, `child_slugs = [phase_slug(slug, idx) for each]`.
   - For each Phase, create child session `sessions/{phase_slug}.json` with
     `kind:"phase"`, `parent_slug`, `phase_index`, `phase_label`, `depends_on`,
     `base_branch = base_branch_for(manifest, idx, slug)`, and empty execute/verify/document/pr stages.

7. **Release lock** and announce: "Phasing 완료: {N} Phases. 다음 단계: `/css:review --slug {slug}`. NEXT=review".

<self_check>
- [ ] phase-manifest-{slug}.json exists and passes validate_manifest
- [ ] Epic session has phase_manifest + child_slugs
- [ ] One child session file per Phase, each passing validate_session
- [ ] Final line contains NEXT=review
</self_check>

$ARGUMENTS
````

- [ ] **Step 2: Verify behavior against the contract**

Run (from `tools/`): `python -c "from css_schema.schema import validate_manifest; import json; validate_manifest(json.load(open('css_schema/fixtures/valid_manifest.json')))"`
Expected: no output, exit 0 (the manifest shape the command must emit is valid).

- [ ] **Step 3: Behavioral checklist (manual review of the prompt)**

- [ ] Threshold gate references `should_phase` with the exact D7 numbers.
- [ ] Sub-threshold path produces a single-Phase manifest (legacy behavior preserved).
- [ ] Child session fields match `tools/css_schema/fixtures/phase_session.json`.

- [ ] **Step 4: Commit**

```bash
git add commands/phase.md
git commit -m "feat(css): add /css:phase phasing stage with threshold gate"
```

---

## Task 6: `commands/ship.md` — multi-Phase orchestrator

**Files:**
- Modify: `commands/ship.md` (insert phasing stage; per-Phase build loop)

- [ ] **Step 1: Edit the Steps section**

Insert a new stage after "Stage 2 — plan (skeleton)" and before "Stage 3 — review":

```markdown
5b. **Stage 2.5 — phasing**:
   - Invoke `/css:phase --slug <slug>` (creates child Phase sessions from the approved manifest).
   - If the Epic stays single-Phase (sub-threshold), continue exactly as the legacy linear flow (one session, one PR).
   - If multi-Phase: run the Epic **architecture review** once (`/css:review --slug <epic>`, kind=epic → coarse, no rich-specs), then run the per-child loop below.
```

Replace Stages 4–7 (execute…pr) handling with a per-Phase loop that now includes detailed plan + rich-spec review:

```markdown
8. **Stages plan→pr per Phase** (multi-Phase Epics):
   For each child slug in topological order (by `phase_index`, respecting `depends_on`):
   a. `/css:plan --slug <child>` (kind=phase → detailed) → `/css:review --slug <child>` (kind=phase → rich-specs for this Phase).
   b. **Gate 2 (per Phase)** — AskUserQuestion: "Phase {idx} '{label}' execute 시작. base=`{base_branch}`. [Yes / Show / Skip / Cancel]".
   c. `/css:execute --slug <child>` → `/css:verify --slug <child>` → `/css:document --slug <child>`.
   d. **Gate 3 (per Phase)** — AskUserQuestion: "Phase {idx} PR 생성 (base=`{base_branch}`). [Yes / Draft / Cancel]".
   e. `/css:pr --slug <child> --base <base_branch>`.
   Independent Phases (disjoint `depends_on`) MAY be dispatched in separate sessions for parallel runs.
```

Keep the single-Phase path identical to today (skeleton + detailed collapse into one plan/review pass).

- [ ] **Step 2: Verify** — re-read the edited `commands/ship.md`; confirm the legacy single-Phase path is byte-for-byte unchanged in behavior and the multi-Phase loop references child slugs + `base_branch`.

- [ ] **Step 3: Behavioral checklist**

- [ ] Gate 2/Gate 3 now fire per Phase.
- [ ] `--base` is passed to `/css:pr`.
- [ ] Topological ordering uses `phase_index` + `depends_on`.

- [ ] **Step 4: Commit**

```bash
git add commands/ship.md
git commit -m "feat(css): ship orchestrates per-Phase execute/verify/document/pr with stacked PRs"
```

---

## Task 7: Two-level `plan` + `review` (Epic coarse / Phase detail)

**Files:**
- Modify: `commands/plan.md`
- Modify: `commands/review.md`
- Modify: `agents/reviewer.md`

Specialist domain: prompt-engineer (single specialist — all three are prompt artifacts), satisfying the Single-Specialist Task Rule.

- [ ] **Step 1: Make `commands/plan.md` level-aware**

Branch on session `kind`:
- `kind == "epic"` → **skeleton plan**: coarse task titles grouped into batches with rough file targets, **no per-step code**. Record `phases.plan.level = "skeleton"`, `task_count`, `batch_count`.
- `kind == "phase"` → **detailed plan**: full bite-sized TDD steps (complete code) for **only this Phase's batches**, written to `docs/superpowers/plans/{epic}-p{n}.md`. Record `phases.plan.level = "detailed"`.

- [ ] **Step 2: Make `commands/review.md` + `agents/reviewer.md` level-aware**

- `kind == "epic"` → **architecture/coverage review**: audit the skeleton plan vs spec; build the coverage matrix with a **Phase column** (tag every skeleton task with its `phase_index` from `phase_manifest`); decide coarse Single-Specialist routing per Phase. **Produce NO rich-specs.** Write report to `.claude/css/reviews/review-{epic}-arch-{ts}.md`.
- `kind == "phase"` → **rich-spec dispatch** (existing behavior): specialists author per-task RED scaffold + GREEN template for **this Phase's tasks only**, written to `.claude/css/plans/{epic}-p{n}-T*.md`; each block carries a `Phase: {n}` line.

In `agents/reviewer.md`, gate the rich-spec dispatch on `kind == "phase"`; for `kind == "epic"` emit only the architecture/coverage report + Phase-tagged matrix.

- [ ] **Step 3: Verify** — the two-level shapes round-trip through the contract:

Run (from `tools/`): `python -c "from css_schema.schema import validate_session; import json; [validate_session(json.load(open(f'css_schema/fixtures/{p}'))) for p in ('epic_session.json','phase_session.json')]"`
Expected: exit 0 (epic carries `plan.level=skeleton` + `review.level=architecture`; phase carries `plan.level=detailed` + `review.level=rich-spec` — the shapes these commands must emit).

- [ ] **Step 4: Behavioral checklist**

- [ ] Epic `plan` emits no code; Epic `review` emits no rich-specs (cost isolation, AC8).
- [ ] Phase `plan` is scoped to that Phase's batches only; Phase `review` rich-specs land at `.claude/css/plans/{epic}-p{n}-T*.md`.
- [ ] Single-Phase Epic: skeleton+detailed collapse into one pass; all tasks tagged `Phase: 1` (no behavior change vs today).

- [ ] **Step 5: Commit**

```bash
git add commands/plan.md commands/review.md agents/reviewer.md
git commit -m "feat(css): two-level plan/review — skeleton+architecture at Epic, detail+rich-spec at Phase"
```

---

## Task 8: `commands/execute.md` + `agents/executor.md` — per-Phase scope

**Files:**
- Modify: `commands/execute.md`
- Modify: `agents/executor.md`

- [ ] **Step 1: Edit execute command**

- Add arg `--phase <n>` (optional; when the resolved session is `kind:"phase"`, infer `n` from `phase_index`).
- Task list source: the **Phase's detailed plan** (`phases.plan.artifact`); rich-specs come from this Phase's own `review` stage (`.claude/css/plans/{epic}-p{n}-T*.md`), not the Epic.
- Worktree path: `../{repo}-css-{epic}-p{n}`; branch `css/{epic}/p{n}`; created from `base_branch` (read from the Phase session) instead of the current branch.
- Pre-flight rich-spec readiness check: filter to tasks whose `Phase:` equals `n`.
- exec-log filename: `exec-log-{epic}-p{n}-{ts}.md`.

In `agents/executor.md`, add to `<inputs>`: `phase_index`, `base_branch`, and "implement ONLY the tasks tagged `Phase: {phase_index}`".

- [ ] **Step 2: Verify** — derive expected worktree/branch using the helpers:

Run (from `tools/`): `python -c "from css_schema.derive import phase_branch, base_branch_for; import json; m=json.load(open('css_schema/fixtures/valid_manifest.json')); print(phase_branch('epic-phase-pipeline',2), base_branch_for(m,2,'epic-phase-pipeline'))"`
Expected: `css/epic-phase-pipeline/p2 css/epic-phase-pipeline/p1`

- [ ] **Step 3: Behavioral checklist**

- [ ] `kind:"phase"` session → worktree/branch derived from `phase_index` + `base_branch`.
- [ ] Legacy single-Phase (`kind:"epic"`, no children) → unchanged `css/{slug}` worktree.

- [ ] **Step 4: Commit**

```bash
git add commands/execute.md agents/executor.md
git commit -m "feat(css): execute a single Phase in a per-Phase worktree off its base_branch"
```

---

## Task 9: `commands/verify.md` — per-Phase criteria subset

**Files:**
- Modify: `commands/verify.md`

- [ ] **Step 1: Edit** — when session `kind:"phase"`, the verifier maps only the acceptance criteria assigned to `phase_index` (those whose rich-spec block is tagged `Phase: {n}`); worktree/branch come from the Phase session.

- [ ] **Step 2: Verify** — confirm `<inputs>` to `css-verifier` now include `phase_index`, and the criteria-matrix instruction scopes to that Phase.

- [ ] **Step 3: Behavioral checklist**

- [ ] LOOPBACK_TO_EXECUTE re-enters `/css:execute --slug <child> --resume` (the same Phase), not the whole Epic.

- [ ] **Step 4: Commit**

```bash
git add commands/verify.md
git commit -m "feat(css): scope verify to a single Phase's criteria and worktree"
```

---

## Task 10: `commands/document.md` — per-Phase docs path

**Files:**
- Modify: `commands/document.md`

- [ ] **Step 1: Edit** — docs output path becomes `docs/{epic}/p{n}/README.md` for Phase sessions (D3 per-Phase). For legacy single-Phase Epics keep `docs/{slug}/README.md`. Commit message stays `docs(css): add docs for {epic}-p{n}`.

- [ ] **Step 2: Verify** — confirm the documenter `<inputs>` carry `epic` + `phase_index` and the path template uses them.

- [ ] **Step 3: Behavioral checklist**

- [ ] No Epic-level aggregate README is produced (deferred per D3 open question).

- [ ] **Step 4: Commit**

```bash
git add commands/document.md
git commit -m "feat(css): write per-Phase documentation under docs/<epic>/p<n>/"
```

---

## Task 11: `commands/pr.md` + `agents/pr-creator.md` — stacked PRs

**Files:**
- Modify: `commands/pr.md`
- Modify: `agents/pr-creator.md`

- [ ] **Step 1: Edit pr command**

- Add arg `--base <branch>` (default `main`). Pass to the PR creator.
- `<inputs>` add `base_branch`, `phase_index`, `epic`, and sibling Phase PR URLs (from sibling child sessions' `phases.pr.artifact`).

In `agents/pr-creator.md`: create the PR with `gh pr create --base <base_branch> ...`; body must note `Stacked on #<N>` when `base_branch != main`, link the Epic spec, and cross-link sibling Phase PRs.

- [ ] **Step 2: Verify** — confirm the `gh pr create` invocation includes `--base` and the body template includes the stacked-on note.

- [ ] **Step 3: Behavioral checklist**

- [ ] Independent Phase (`base_branch == main`) → PR targets `main`, no stacked note.
- [ ] Dependent Phase → PR targets predecessor branch + stacked note.

- [ ] **Step 4: Commit**

```bash
git add commands/pr.md agents/pr-creator.md
git commit -m "feat(css): open per-Phase stacked PRs with --base and sibling cross-links"
```

---

## Task 12: Per-Phase locking + `_active.json` fields

**Files:**
- Modify: `commands/{phase,execute,verify,document,pr}.md` (lock naming)

- [ ] **Step 1: Edit** — change the lock convention from `locks/{slug}.lock` (or `{slug}-{phase}.lock`) to be keyed by the **child slug** so sibling Phases never block each other: `locks/{child_slug}-{stage}.lock`. Where commands write `_active.json`, also set `active_epic` (parent_slug or self) and `active_phase` (phase_index or null).

- [ ] **Step 2: Verify** — `_active.json` produced matches `validate_active`:

Run (from `tools/`): `python -c "from css_schema.schema import validate_active; validate_active({'latest_slug':'e-p1','active_epic':'e','active_phase':1})"`
Expected: no output, exit 0.

- [ ] **Step 3: Behavioral checklist**

- [ ] Two sibling Phases acquiring locks concurrently do not collide (distinct lock filenames).

- [ ] **Step 4: Commit**

```bash
git add commands/phase.md commands/execute.md commands/verify.md commands/document.md commands/pr.md
git commit -m "feat(css): per-Phase lock keys and active_epic/active_phase tracking"
```

---

## Task 13: README + cross-link the spec

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Edit** — add an "Epic / Phase decomposition" subsection to the pipeline overview: define Project/Epic/Phase/Stage, the threshold, and the stacked-PR flow. Link `docs/superpowers/specs/2026-05-29-epic-phase-pipeline-design.md`.

- [ ] **Step 2: Verify** — `grep -n "Epic" README.md` shows the new section; Mermaid pipeline diagram (if present) notes the new `phasing` stage.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: document Epic/Phase decomposition in pipeline overview"
```

---

## Self-Review (completed by plan author)

**Spec coverage** (against `2026-05-29-...-design.md`):
- A1 session schema → Tasks 3, 4, 5 (validator + phase.md persistence). ✓
- A2 phasing stage → Task 5. ✓
- A3 ship orchestrator → Task 6. ✓
- A4 two-level plan + review (D4/D8/D10), Phase tagging → Task 7. ✓
- A5 execute per-Phase → Task 8. ✓
- A6 verify/document → Tasks 9, 10. ✓
- A7 stacked PR → Task 11. ✓
- A8 locking/_active → Tasks 4, 12. ✓
- Threshold D7 → Tasks 1, 5. ✓  Backward compat D9 → Task 3. ✓

**Placeholder scan:** Code steps contain full code; prompt-edit tasks specify exact files, insertion points, and behavioral checks (markdown prompt edits are verified via the validator + checklists, not unit tests — by design, since the pipeline has no prompt-unit-test harness). No TBD/TODO.

**Type consistency:** `should_phase`, `phase_slug`, `phase_branch`, `base_branch_for`, `validate_session`, `validate_manifest`, `validate_active`, `SchemaError` are defined in Tasks 1–4 and referenced consistently in Tasks 5–12. Slug/branch conventions (`<epic>-p<idx>`, `css/<epic>/p<idx>`) are uniform throughout.

**Note on TDD applicability:** Tasks 1–4 are strict TDD (real Python + tests). Tasks 5–13 edit prompt markdown; their "test" is contract-conformance via `tools/css_schema` + a behavioral checklist + (deferred) E2E run against a `tests/fixtures/toy-*` project — consistent with how this repo verifies the pipeline today.
