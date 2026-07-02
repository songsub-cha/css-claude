---
description: Push css/<slug> and open a PR via gh (CSS pipeline stage 7)
argument-hint: "[--session <name>] [--draft]"
---

# /css:pr

Push the worktree branch and create a PR. Wraps `css-pr-creator`.

## Steps

1. **Parse arguments**: `--session`, `--draft`, `--base <branch>` (default `session.base_branch` — the stacking base for a child Phase, the captured start branch otherwise; then `session.config.pr.default_base_branch`; then `main`). Honor `session.config.pr.default_draft`. Pass `base_branch` to the PR creator.

2. **Resolve session**.

3. **Master-flow gate guard**:
   - If `session.master_flow == true` and `session.gates.gate3_pre_pr.state != "approved"`, abort:
     "Gate 3가 승인되지 않았습니다. `/css:ship --session <name>`을 통해 진행하세요."
   - If `session.master_flow == true` and `session.gates.gate3_pre_pr.draft == true`, set `--draft` automatically.
   - When `master_flow == true`, the persisted Gate 3 approval IS the push confirmation — skip step 5.

4. **Pre-check**:
   - `session.phases.document.status` must be `completed`.
   - `gh auth status` must succeed.
   - Working directory must be inside the worktree OR allow the agent to `cd` into it.

5. **Standalone push confirmation** ONLY when `session.master_flow != true` (a standalone `/css:pr` run has no Gate 3, and the dispatched pr-creator is a subagent that cannot prompt the user — the confirmation must happen here):
   AskUserQuestion: "구현 + 문서 완료. 브랜치 `{branch}` 를 `{base_branch}` 기반으로 origin 에 push 하고 PR 을 생성합니다. 진행할까요? [Yes / Draft PR / Cancel]"
   - Yes → `push_confirmed = true`. Draft PR → `push_confirmed = true` and set `--draft`. Cancel → exit without dispatching.

6. **Acquire lock**. Lock key = `locks/{slug}-pr.lock` (for `kind:"phase"`, `slug` is the child slug — distinct per sibling Phase, no collision; stale after 60 min → replace with a note; a fresh lock from another run → abort with guidance). Update `_active.json` with `active_epic` and `active_phase`.

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
     base_branch: {--base arg, else session.base_branch, else config.pr.default_base_branch, else main}
     epic: {parent_slug or slug}
     phase_index: {phase_index or null}
     spec: {session.phases.interview.artifact or parent_session.phases.interview.artifact}
     plan: {session.phases.plan.artifact}
     verify: {session.phases.verify.artifact}
     docs: {session.phases.document.artifact}
     sibling_pr_urls: {[child_session.phases.pr.artifact for completed sibling Phases]}
     coverage_percent: {from verify report}
     issue_number: {session.github.issue_number or null}
     auto_close_issue: {config.github.auto_close_issue, default true}
     draft: {true if --draft else false}
     gate3_approved: {true when master-flow Gate 3 is already approved}
     push_confirmed: {true when the step-5 standalone confirmation was obtained}
     </inputs>
     <task>
     Push the branch (no force) only with prior user confirmation. A persisted master-flow Gate 3 approval counts as that confirmation; do not ask again when gate3_approved is true. A standalone confirmation collected by /css:pr arrives as push_confirmed. When neither is true, abort with guidance — you are a subagent and cannot prompt the user. Create the PR via gh. If a PR template exists under the repo (`.github/PULL_REQUEST_TEMPLATE.md`, `.github/pull_request_template.md`, `.github/PULL_REQUEST_TEMPLATE/*.md`, root `PULL_REQUEST_TEMPLATE.md`, or `docs/PULL_REQUEST_TEMPLATE.md`), build the PR description ON that template — preserve its sections and fill CSS content into them; otherwise use the default CSS body. Either way the body must link spec/plan/verify/docs, list acceptance criteria as a Test Plan checklist, and show coverage %. When `issue_number` is set, include `Closes #<issue_number>` (or `Refs #<issue_number>` when `auto_close_issue` is false) so the PR links/closes the tracking issue. Never add Claude/AI attribution ("🤖 Generated with [Claude Code]", "Co-Authored-By: Claude") to the PR description. Honor --draft.
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
