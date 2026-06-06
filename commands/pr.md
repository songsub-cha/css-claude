---
description: Push css/<slug> and open a PR via gh (CSS pipeline stage 7)
argument-hint: "[--session <name>] [--draft]"
---

# /css:pr

Push the worktree branch and create a PR. Wraps `css-pr-creator`.

## Steps

1. **Parse arguments**: `--session`, `--draft`, `--base <branch>` (default `session.base_branch` for a child Phase, otherwise `main`). Pass `base_branch` to the PR creator.

2. **Resolve session**.

3. **Master-flow gate guard** (NEW):
   - If `session.master_flow == true` and `session.gates.gate3_pre_pr.state != "approved"`, abort:
     "Gate 3가 승인되지 않았습니다. `/css:ship --session <name>`을 통해 진행하세요."
   - If `session.master_flow == true` and `session.gates.gate3_pre_pr.draft == true`, set `--draft` automatically.
   - If `master_flow == true` and gate3_pre_pr.state is "approved", skip the Gate 3 AskUserQuestion in step 5.

4. **Pre-check**:
   - `session.phases.document.status` must be `completed`.
   - `gh auth status` must succeed.
   - Working directory must be inside the worktree OR allow the agent to `cd` into it.

5. **AskUserQuestion (master-flow Gate 3)** ONLY if invoked as part of `/css:ship` (i.e., `session.master_flow == true`):
   "구현 + 문서 완료. 브랜치 `css/<slug>` 를 origin 에 push 하고 PR 을 생성합니다. 진행할까요? [Yes / Draft PR / Cancel]"

6. **Acquire lock**. Lock key = `locks/{slug}-pr.lock` (for `kind:"phase"`, `slug` is the child slug — distinct per sibling Phase, no collision). Update `_active.json` with `active_epic` and `active_phase`.

7. **Echo header**: `[css:pr @ slug={slug}]`.

8. **Dispatch the PR creator**:

   ```
   Task(
     subagent_type="css-pr-creator",
     description="css pr: {slug}",
     prompt="""
     <inputs>
     worktree: {session.phases.execute.worktree}
     branch: {session.phases.execute.branch}
     base_branch: {--base arg, else session.base_branch, else main}
     epic: {parent_slug or slug}
     phase_index: {phase_index or null}
     spec: {session.phases.interview.artifact or parent_session.phases.interview.artifact}
     plan: {session.phases.plan.artifact}
     verify: {session.phases.verify.artifact}
     docs: {session.phases.document.artifact}
     sibling_pr_urls: {[child_session.phases.pr.artifact for completed sibling Phases]}
     coverage_percent: {from verify report}
     draft: {true if --draft else false}
     gate3_approved: {true when master-flow Gate 3 is already approved}
     </inputs>
     <task>
     Push the branch (no force) after explicit user confirmation. A persisted master-flow Gate 3 approval counts as that confirmation; do not ask again when gate3_approved is true. Create the PR via gh with a body that links spec/plan/verify/docs, lists acceptance criteria as a Test Plan checklist, and shows coverage %. Honor --draft.
     </task>
     <output_contract>
     Final line: ARTIFACT=<PR URL>
     </output_contract>
     """
   )
   ```

9. **Update session**: `phases.pr.status = completed`, `phases.pr.artifact = <PR URL>`.

10. **Release lock**. Print the PR URL.

<self_check>
- [ ] PR URL captured in session
- [ ] No force-push performed
</self_check>

$ARGUMENTS
