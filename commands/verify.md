---
description: Test + coverage + code review + security review (CSS pipeline stage 5)
argument-hint: "[--session <name>] [--exec-log <path>]"
---

# /css:verify

Run the test suite, coverage, criteria mapping, code-quality review, and security review; merge into one verdict. Wraps `css-verifier`.

## Steps

1. **Parse arguments**: `--session`, `--exec-log`.

2. **Resolve session**.

3. **Retry counter**: if `session.retry_counters.verify >= 3`, escalate to user with options.

4. **Acquire lock** on `verify`. Lock key = `locks/{slug}-verify.lock` (for `kind:"phase"`, `slug` is the child slug — distinct per sibling Phase). Update `_active.json` with `active_epic` and `active_phase`.

5. **Echo header**: `[css:verify @ slug={slug}, attempt={n+1}/3]`.

6. **Determine verify scope**:
   - `kind:"phase"` session → scope to criteria tagged `Phase: {phase_index}` in the rich-spec blocks. Worktree and branch come from the Phase session (`phases.execute.worktree`, `phases.execute.branch`).
   - Legacy single-Phase session → full criteria set (existing behavior).

7. **Dispatch the verifier**:

   ```
   Task(
     subagent_type="css-verifier",
     description="css verify: {slug}",
     prompt="""
     <inputs>
     worktree: {session.phases.execute.worktree}
     branch: {session.phases.execute.branch}
     language_profile: {profile}
     spec: {session.phases.interview.artifact}
     plan: {session.phases.plan.artifact}
     phase_index: {phase_index or null}
     </inputs>
     <task>
     Run tests + coverage in the worktree using language_profile commands; map every acceptance criterion in the spec (scoped to phase_index when set — criteria whose rich-spec block carries Phase: {phase_index}) to concrete code/test evidence (file:line citations); dispatch css-code-reviewer and css-security-reviewer in parallel via Task; merge findings; decide verdict. Any CRITICAL or HIGH from either reviewer, OR tests fail, OR coverage < threshold, OR criterion unmapped → LOOPBACK_TO_EXECUTE (if attempts < 3) else ESCALATE.
     </task>
     <output_contract>
     Write aggregate report to: <project>/.claude/css/verifies/verify-{slug}-{ts}.md
     Sections: Verdict, Test Summary, Coverage Table, Acceptance Criteria Matrix, Code-quality Findings (link), Security Findings (link), Loopback Recommendation, Retry Counter.
     Final line: VERDICT=PASS | VERDICT=LOOPBACK_TO_EXECUTE | VERDICT=ESCALATE
     </output_contract>
     """
   )
   ```

8. **Parse verdict**:
   - `PASS` → next.
   - `LOOPBACK_TO_EXECUTE` → increment counter. If `< 3`, automatically invoke `/css:execute --session <slug> --resume` (for `kind:"phase"`, `<slug>` is the child slug, not the Epic) then re-run verify. If `>= 3`, escalate.
   - `ESCALATE` → stop.

9. **Release lock**.

<self_check>
- [ ] verify-{slug}-{ts}.md exists
- [ ] code-review-{slug}-{ts}.md exists
- [ ] security-review-{slug}-{ts}.md exists
- [ ] retry_counters.verify updated on loopback
</self_check>

$ARGUMENTS
