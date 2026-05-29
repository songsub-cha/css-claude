---
description: Master pipeline — runs interview → plan → review → execute → verify → document → pr with three approval gates
argument-hint: "[--slug <name>] <idea>"
---

# /css:ship

Run the full CSS pipeline. Three approval gates: Gate 1 is implicit (brainstorming's own user-review step); Gates 2 (pre-execute) and 3 (pre-pr) use AskUserQuestion.

## Steps

1. **Parse arguments**: extract `--slug` if present; remainder is the idea.

2. **Resolve or initialize session**:
   - `--slug` provided + existing `<project>/.claude/css/sessions/<slug>.json` → AskUserQuestion: "기존 세션 발견 (phase=`<current>`). 어떻게 진행할까요? [Resume / Restart / Cancel]".
   - `--slug` provided + no file → init.
   - No `--slug` → derive slug from idea (kebab-case, collision-suffixed if needed), init session, update `_active.json`.
   - Set `session.master_flow = true`.

3. **Acquire lock**.

4. **Stage 1 — interview**:
   - Invoke `/css:interview <idea>` (or resume) inheriting the slug.
   - Gate 1 is implicit: brainstorming's own "user reviews spec" step.

5. **Stage 2 — plan (skeleton)**:
   - Invoke `/css:plan --slug <slug>`.

5b. **Stage 2.5 — phasing**:
   - Invoke `/css:phase --slug <slug>` (creates child Phase sessions from the approved manifest).
   - If the Epic stays single-Phase (sub-threshold), continue exactly as the legacy linear flow (one session, one PR).
   - If multi-Phase: run the Epic **architecture review** once (`/css:review --slug <epic>`, kind=epic → coarse, no rich-specs), then run the per-child loop below.

6. **Stage 3 — review (loop)** *(single-Phase / legacy path)*:
   - Invoke `/css:review --slug <slug>`.
   - On `LOOPBACK_TO_PLAN`, the review command itself loops back to plan up to 2 attempts.
   - On `LOOPBACK_TO_INTERVIEW`, ask user to confirm before re-entering interview.
   - On `ESCALATE`, stop and surface options.
   - *Multi-Phase Epics: the Epic architecture review was already run in step 5b. Skip to step 8.*

7. **Gate 2 — pre-execute** *(single-Phase / legacy path)*:
   - AskUserQuestion: "Plan 검증 완료. worktree '`../<repo>-css-<slug>`' 생성 후 execute 를 시작합니다. 배치 N개, 작업 M개. 진행할까요? [Yes / Show plan / Cancel]".

8. **Stages plan→pr per Phase** *(multi-Phase Epics)*:
   For each child slug in topological order (by `phase_index`, respecting `depends_on`):
   a. `/css:plan --slug <child>` (kind=phase → detailed) → `/css:review --slug <child>` (kind=phase → rich-specs for this Phase).
   b. **Gate 2 (per Phase)** — AskUserQuestion: "Phase {idx} '{label}' execute 시작. base=`{base_branch}`. [Yes / Show / Skip / Cancel]".
   c. `/css:execute --slug <child>` → `/css:verify --slug <child>` → `/css:document --slug <child>`.
   d. **Gate 3 (per Phase)** — AskUserQuestion: "Phase {idx} PR 생성 (base=`{base_branch}`). [Yes / Draft / Cancel]".
   e. `/css:pr --slug <child> --base <base_branch>`.
   Independent Phases (disjoint `depends_on`) MAY be dispatched in separate sessions for parallel runs.
   *Single-Phase Epics: skip this step — use steps 7, 9–13 below.*

9. **Stage 4 — execute** *(single-Phase / legacy path)*: invoke `/css:execute --slug <slug>`. The `master_flow` flag tells `/css:execute` not to ask Gate 2 again (it inherits the answer from this step).

10. **Stage 5 — verify (loop)** *(single-Phase / legacy path)*:
    - Invoke `/css:verify --slug <slug>`.
    - On `LOOPBACK_TO_EXECUTE`, the verify command itself loops back to execute up to 3 attempts.
    - On `ESCALATE`, stop with options.

11. **Stage 6 — document** *(single-Phase / legacy path)*: invoke `/css:document --slug <slug>`.

12. **Gate 3 — pre-pr** *(single-Phase / legacy path)*:
    - AskUserQuestion: "구현 + 문서 완료. 브랜치 `css/<slug>` 를 origin 에 push 하고 PR 을 생성합니다. 진행할까요? [Yes / Draft PR / Cancel]".

13. **Stage 7 — pr** *(single-Phase / legacy path)*: invoke `/css:pr --slug <slug>` (with `--draft` if user chose). The `master_flow` flag tells `/css:pr` not to ask Gate 3 again.

14. **Finalize**: mark all phases completed, release lock, print summary:
    "Pipeline 완료. PR: `<URL>`. 산출물: `<paths>`."

<self_check>
- [ ] All 7 phases recorded as completed in session
- [ ] Each gate prompt was shown when applicable
- [ ] PR URL captured
- [ ] Lock released
</self_check>

$ARGUMENTS
