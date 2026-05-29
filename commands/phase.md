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
