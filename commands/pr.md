---
description: Push css/<slug> and open a PR via gh (CSS pipeline stage 7)
argument-hint: "[--slug <name>] [--draft]"
---

# /css:pr

Push the worktree branch and create a PR. Wraps `css-pr-creator`.

## Steps

1. **Parse arguments**: `--slug`, `--draft`.

2. **Resolve session**.

3. **Pre-check**:
   - `session.phases.document.status` must be `completed`.
   - `gh auth status` must succeed.
   - Working directory must be inside the worktree OR allow the agent to `cd` into it.

4. **AskUserQuestion (master-flow Gate 3)** ONLY if invoked as part of `/css:ship` (i.e., `session.master_flow == true`):
   "구현 + 문서 완료. 브랜치 `css/<slug>` 를 origin 에 push 하고 PR 을 생성합니다. 진행할까요? [Yes / Draft PR / Cancel]"

5. **Acquire lock**.

6. **Echo header**: `[css:pr @ slug={slug}]`.

7. **Dispatch the PR creator**:

   ```
   Task(
     subagent_type="css-pr-creator",
     description="css pr: {slug}",
     prompt="""
     <inputs>
     worktree: {session.phases.execute.worktree}
     branch: css/{slug}
     spec: {session.phases.interview.artifact}
     plan: {session.phases.plan.artifact}
     verify: {session.phases.verify.artifact}
     docs: {session.phases.document.artifact}
     coverage_percent: {from verify report}
     draft: {true if --draft else false}
     </inputs>
     <task>
     Push the branch (no force) after explicit user confirmation; create the PR via gh with a body that links spec/plan/verify/docs, lists acceptance criteria as a Test Plan checklist, and shows coverage %. Honor --draft.
     </task>
     <output_contract>
     Final line: ARTIFACT=<PR URL>
     </output_contract>
     """
   )
   ```

8. **Update session**: `phases.pr.status = completed`, `phases.pr.artifact = <PR URL>`.

9. **Release lock**. Print the PR URL.

<self_check>
- [ ] PR URL captured in session
- [ ] No force-push performed
</self_check>

$ARGUMENTS
