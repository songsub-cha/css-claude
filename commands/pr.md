---
description: Push css/<slug> and open a PR via gh (CSS pipeline stage 7)
argument-hint: "[--session <name>] [--draft]"
---

# /css:pr

Push the worktree branch and create a PR. Wraps `css-pr-creator`.

## Steps

1. **Parse arguments**: `--session`, `--draft`, `--base <branch>` (default `main`). Pass `base_branch` to the PR creator.

2. **Resolve session**.

3. **Master-flow gate guard** (NEW):
   - If `session.master_flow == true` and `session.gates.gate3_pre_pr.state != "approved"`, abort:
     "Gate 3가 승인되지 않았습니다. `/css:ship --session <name>`을 통해 진행하세요."
   - If `session.master_flow == true` and `session.gates.gate3_pre_pr.draft == true`, set `--draft` automatically.
   - If `master_flow == true` and gate3_pre_pr.state is "approved", skip the Gate 3 AskUserQuestion in step 4.

4. **Pre-check**:
   - `session.phases.document.status` must be `completed`.
   - `gh auth status` must succeed.
   - Working directory must be inside the worktree OR allow the agent to `cd` into it.

4. **AskUserQuestion (master-flow Gate 3)** ONLY if invoked as part of `/css:ship` (i.e., `session.master_flow == true`):
   "구현 + 문서 완료. 브랜치 `css/<slug>` 를 origin 에 push 하고 PR 을 생성합니다. 진행할까요? [Yes / Draft PR / Cancel]"

5. **Acquire lock**. Lock key = `locks/{slug}-pr.lock` (for `kind:"phase"`, `slug` is the child slug — distinct per sibling Phase, no collision). Update `_active.json` with `active_epic` and `active_phase`.

6. **Echo header**: `[css:pr @ slug={slug}]`.

7. **Dispatch the PR creator**:

   ```
   Task(
     subagent_type="css-pr-creator",
     description="css pr: {slug}",
     prompt="""
     <inputs>
     worktree: {session.phases.execute.worktree}
     branch: {session.phases.execute.branch}
     base_branch: {--base arg, default main}
     epic: {parent_slug or slug}
     phase_index: {phase_index or null}
     spec: {session.phases.interview.artifact}
     plan: {session.phases.plan.artifact}
     verify: {session.phases.verify.artifact}
     docs: {session.phases.document.artifact}
     sibling_pr_urls: {[child_session.phases.pr.artifact for completed sibling Phases]}
     coverage_percent: {from verify report}
     issue_number: {session.github.issue_number or null}
     auto_close_issue: {config.github.auto_close_issue, default true}
     draft: {true if --draft else false}
     </inputs>
     <task>
     Push the branch (no force) after explicit user confirmation; create the PR via gh. If a PR template exists under the repo (`.github/PULL_REQUEST_TEMPLATE.md`, `.github/pull_request_template.md`, `.github/PULL_REQUEST_TEMPLATE/*.md`, root `PULL_REQUEST_TEMPLATE.md`, or `docs/PULL_REQUEST_TEMPLATE.md`), build the PR description ON that template — preserve its sections and fill CSS content into them; otherwise use the default CSS body. Either way the body must link spec/plan/verify/docs, list acceptance criteria as a Test Plan checklist, and show coverage %. When `issue_number` is set, include `Closes #<issue_number>` (or `Refs #<issue_number>` when `auto_close_issue` is false) so the PR links/closes the tracking issue. Never add Claude/AI attribution ("🤖 Generated with [Claude Code]", "Co-Authored-By: Claude") to the PR description. Honor --draft.
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
