---
description: css/<slug> 를 push 하고 gh 로 PR 생성 (CSS 파이프라인 7단계)
argument-hint: "[--session <name>] [--draft]"
---

# /css:pr

worktree 브랜치를 push 하고 PR 을 생성한다. `css-pr-creator` 를 감싼다(wrap).

## 단계

1. **인자 파싱**: `--session`, `--draft`, `--base <branch>` (기본값 `session.base_branch` — 자식 Phase 는 스태킹 base, 그 외에는 캡처된 시작 브랜치; 그다음 `session.config.pr.default_base_branch`; 그다음 `main`). `session.config.pr.default_draft` 를 존중한다. `base_branch` 를 PR creator 에 전달한다.

2. **세션 해석**.

3. **마스터 플로우 게이트 가드**:
   - `session.master_flow == true` 이고 `session.gates.gate3_pre_pr.state != "approved"` 이면 중단한다:
     "Gate 3가 승인되지 않았습니다. `/css:ship --session <name>`을 통해 진행하세요."
   - `session.master_flow == true` 이고 `session.gates.gate3_pre_pr.draft == true` 이면 `--draft` 를 자동으로 설정한다.
   - `master_flow == true` 일 때는 영속화된 Gate 3 승인이 곧 push 확인이다 — 5단계를 건너뛴다.

4. **사전 점검**:
   - `session.phases.document.status` 가 반드시 `completed` 여야 한다.
   - `gh auth status` 가 성공해야 한다.
   - 작업 디렉토리가 worktree 내부에 있거나, 에이전트가 그 안으로 `cd` 할 수 있어야 한다.

5. **단독 push 확인** — `session.master_flow != true` 일 때만(단독 `/css:pr` 실행은 Gate 3 가 없고, 디스패치되는 pr-creator 는 사용자에게 프롬프트를 띄울 수 없는 서브에이전트이므로 확인은 여기서 이루어져야 한다):
   AskUserQuestion: "구현 + 문서 완료. 브랜치 `{branch}` 를 `{base_branch}` 기반으로 origin 에 push 하고 PR 을 생성합니다. 진행할까요? [Yes / Draft PR / Cancel]"
   - Yes → `push_confirmed = true`. Draft PR → `push_confirmed = true` 로 설정하고 `--draft` 설정. Cancel → 디스패치 없이 종료.

6. **락 획득**. 락 키 = `locks/{slug}-pr.lock` (`kind:"phase"` 인 경우 `slug` 는 자식 슬러그 — 형제 Phase 마다 구분되며 충돌 없음; 60분 경과 시 stale → 안내와 함께 교체; 다른 실행의 신선한 락 → 안내와 함께 중단). `_active.json` 을 `active_epic` 과 `active_phase` 로 갱신한다.

7. **헤더 출력**: `[css:pr @ slug={slug}]`.

8. **PR creator 디스패치**:

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

9. **세션 갱신**: `phases.pr.status = completed`, `phases.pr.artifact = <PR URL>`.

10. **락 해제**. PR URL 을 출력한다.

<self_check>
- [ ] PR URL captured in session
- [ ] No force-push performed
</self_check>

$ARGUMENTS
