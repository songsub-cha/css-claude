---
description: Turn the spec into a structured plan via superpowers:writing-plans (CSS pipeline stage 2)
argument-hint: "[--session <name>] [--from <spec-path>]"
---

# /css:plan

Translate the spec into a step-by-step plan. Wraps `superpowers:writing-plans`.

## Steps

1. **Parse arguments**: extract `--session` and `--from`.

2. **Resolve session**:
   - `--session` → load `<project>/.claude/css/sessions/<slug>.json`.
   - No `--session` → read `<project>/.claude/css/sessions/_active.json` for `latest_slug`.
   - If neither resolves → ask: "어떤 슬러그의 plan을 작성할까요? `/css:plan --session <name>` 또는 `--from <spec path>` 로 다시 시도해주세요." and exit.

3. **Resolve spec path**:
   - `--from <path>` if provided.
   - Else `session.phases.interview.artifact`.
   - If missing → ask: "spec 이 아직 없습니다. `/css:interview` 를 먼저 실행하거나 `--from <path>` 로 spec 경로를 지정해주세요." and exit.

4. **Acquire phase lock** on `plan` for this slug.

5. **Echo header**: `[css:plan @ slug={slug}]`.

6. **Verify superpowers** (same check as `/css:interview`).

7. **Invoke writing-plans**:
   ```
   Skill("superpowers:writing-plans")
   ```
   Pass the spec path as context. Remind writing-plans that the next CSS stage (`/css:review`) will audit each task for the Single-Specialist Task Rule: every task should map to exactly one domain specialist (or executor-direct glue). Multi-domain tasks will trigger `LOOPBACK_TO_PLAN` — better to decompose pre-emptively.

8. **On writing-plans completion**:
   - Locate the plan file (typically `docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md`).
   - Update session: `phases.plan.status = completed`, `phases.plan.artifact = <plan path>`, `phases.plan.task_count = <int>`, `phases.plan.completed_at = <ISO>`.

9. **Release lock** and announce:
   "Plan 작성 완료: `<plan path>`. 다음 단계: `/css:review` 또는 `/css:ship --session <slug>`로 진행."

<self_check>
- [ ] Plan file exists at the path recorded in session
- [ ] session file phase status updated
- [ ] Final line contains NEXT=review or ARTIFACT=<plan path>
</self_check>

$ARGUMENTS
