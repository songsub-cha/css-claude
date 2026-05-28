---
description: Master pipeline — runs interview → plan → review → execute → verify → document → pr with three approval gates
argument-hint: "[--session <name>] <idea>"
---

# /css:ship

Run the full CSS pipeline. Three approval gates: Gate 1 is implicit (brainstorming's own user-review step); Gates 2 (pre-execute) and 3 (pre-pr) use AskUserQuestion.

## Steps

1. **Parse arguments**: extract `--session` if present; remainder is the idea.

2. **Resolve or initialize session**:
   - `--session` provided + existing `<project>/.claude/css/sessions/<slug>.json` → AskUserQuestion: "기존 세션 발견 (phase=`<current>`). 어떻게 진행할까요? [Resume / Restart / Cancel]".
   - `--session` provided + no file → init.
   - No `--session` → derive slug from idea (kebab-case, collision-suffixed if needed), init session, update `_active.json`.
   - Set `session.master_flow = true`.

3. **Acquire lock**.

4. **Stage 1 — interview**:
   - Invoke `/css:interview <idea>` (or resume) inheriting the slug.
   - Gate 1 is implicit: brainstorming's own "user reviews spec" step.

5. **Stage 2 — plan**:
   - Invoke `/css:plan --session <slug>`.

6. **Stage 3 — review (loop)**:
   - Invoke `/css:review --session <slug>`.
   - On `LOOPBACK_TO_PLAN`, the review command itself loops back to plan up to 2 attempts.
   - On `LOOPBACK_TO_INTERVIEW`, ask user to confirm before re-entering interview.
   - On `ESCALATE`, stop and surface options.

7. **Gate 2 — pre-execute**:
   - AskUserQuestion: "Plan 검증 완료. worktree '`../<repo>-css-<slug>`' 생성 후 execute 를 시작합니다. 배치 N개, 작업 M개. 진행할까요? [Yes / Show plan / Cancel]".

8. **Stage 4 — execute**: invoke `/css:execute --session <slug>`. The `master_flow` flag tells `/css:execute` not to ask Gate 2 again (it inherits the answer from this step).

9. **Stage 5 — verify (loop)**:
   - Invoke `/css:verify --session <slug>`.
   - On `LOOPBACK_TO_EXECUTE`, the verify command itself loops back to execute up to 3 attempts.
   - On `ESCALATE`, stop with options.

10. **Stage 6 — document**: invoke `/css:document --session <slug>`.

11. **Gate 3 — pre-pr**:
    - AskUserQuestion: "구현 + 문서 완료. 브랜치 `css/<slug>` 를 origin 에 push 하고 PR 을 생성합니다. 진행할까요? [Yes / Draft PR / Cancel]".

12. **Stage 7 — pr**: invoke `/css:pr --session <slug>` (with `--draft` if user chose). The `master_flow` flag tells `/css:pr` not to ask Gate 3 again.

13. **Finalize**: mark all phases completed, release lock, print summary:
    "Pipeline 완료. PR: `<URL>`. 산출물: `<paths>`."

<self_check>
- [ ] All 7 phases recorded as completed in session
- [ ] Each gate prompt was shown when applicable
- [ ] PR URL captured
- [ ] Lock released
</self_check>

$ARGUMENTS
