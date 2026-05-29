---
description: Audit the plan, enforce Single-Specialist Task Rule, dispatch domain specialists to author rich specs (CSS pipeline stage 3)
argument-hint: "[--slug <name>] [--plan <plan-path>]"
---

# /css:review

Audit the plan against the spec, dispatch domain specialists to produce RICH specs (per-task RED scaffold + GREEN template), decide loopback. Wraps `css-reviewer`.

## Steps

1. **Parse arguments**: `--slug`, `--plan`.

2. **Resolve session** (same rules as `/css:plan`).

3. **Resolve plan path**: `--plan <path>` > `session.phases.plan.artifact` > error.

4. **Check retry counter**: if `session.retry_counters.review >= 2`, set `verdict = ESCALATE` and ask user: "review 자동 재시도 한도(2회) 초과. 어떻게 진행할까요? [한 번 더 시도 / 현재 plan으로 진행 / 중단]". Apply user choice and stop.

5. **Acquire lock** on `review` for this slug.

6. **Echo header**: `[css:review @ slug={slug}, attempt={n+1}/2]`.

7. **Determine review level** from session `kind`:
   - `kind == "epic"` (or absent) → **architecture review**: audit the skeleton plan vs spec; build coverage matrix with a **Phase column** (tag every skeleton task with its `phase_index` from `phase_manifest`); decide coarse Single-Specialist routing per Phase. **Produce NO rich-specs.** Write report to `.claude/css/reviews/review-{slug}-arch-{ts}.md`.
   - `kind == "phase"` → **rich-spec dispatch** (existing behavior): dispatch domain specialists to produce per-task RED scaffolds + GREEN templates for **this Phase's tasks only**, written to `.claude/css/plans/{parent_slug}-p{phase_index}-T*.md`; each block carries a `Phase: {phase_index}` line.

8. **Dispatch the reviewer**:

   ```
   Task(
     subagent_type="css-reviewer",
     description="css review: {slug}",
     prompt="""
     <inputs>
     spec: {spec path}
     plan: {plan path}
     session: <project>/.claude/css/sessions/{slug}.json
     project_root: <cwd>
     review_level: {architecture | rich-spec}
     phase_index: {phase_index or null}
     </inputs>
     <task>
     Audit the plan against the spec. Build the coverage matrix.
     - architecture level (kind=epic): add Phase column tagging each task with its phase_index from phase_manifest. Coarse Single-Specialist routing per Phase. NO rich-specs. Report to .claude/css/reviews/review-{slug}-arch-{ts}.md.
     - rich-spec level (kind=phase): run the Single-Specialist Task Rule audit per task (multi-domain → LOOPBACK_TO_PLAN). Detect domains and dispatch matching specialists in parallel via Task — each specialist MUST produce a RICH spec artifact with per-task RED scaffolds + GREEN templates tagged with Phase: {phase_index}.
     Emit the final verdict.
     </task>
     <output_contract>
     Write the report to: <project>/.claude/css/reviews/review-{slug}-{ts}.md
     Sections in order: Verdict, Coverage Matrix (with Phase column for architecture reviews), Single-Specialist Audit table, Findings, Domain Specialist Dispatch summary (with rich-spec artifact paths), Retry Counter.
     Final line: VERDICT=PASS | VERDICT=LOOPBACK_TO_PLAN | VERDICT=LOOPBACK_TO_INTERVIEW
     </output_contract>
     """
   )
   ```

8. **Parse verdict from the agent's final line**:
   - `PASS` → update session: `phases.review.status = completed`, `phases.review.verdict = PASS`; increment nothing. Announce next step.
   - `LOOPBACK_TO_PLAN` → increment `retry_counters.review`. If `< 2`, automatically invoke `/css:plan --slug <slug>` then re-run `/css:review`. If `>= 2`, escalate to user.
   - `LOOPBACK_TO_INTERVIEW` → ask user "interview 단계로 되돌아가시겠습니까?". On confirm, invoke `/css:interview --slug <slug>` then `/css:plan` then `/css:review`.
   - `ESCALATE` → stop and surface to user.

9. **Release lock**.

<self_check>
- [ ] Report file exists
- [ ] session.phases.review.verdict set
- [ ] Every routed task has a populated per-task block in its rich-spec artifact
- [ ] retry_counters.review updated on loopback
- [ ] Final line contains VERDICT=...
</self_check>

$ARGUMENTS
