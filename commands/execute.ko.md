---
description: 격리된 worktree 에서 엄격한 TDD 로 plan 구현, rich spec 기반 cache-first (CSS 파이프라인 4단계)
argument-hint: "[--session <name>] [--plan <plan-path>] [--resume]"
---

# /css:execute

git worktree 를 생성하거나 연결한 뒤, executor 를 배치 단위로 TDD 로 구동한다. GREEN 은 `/css:review` 에서 생성된 rich-spec 산출물을 활용한다(cache-first); 전문가는 제한된 폴백(fallback)으로만 재호출된다.

## 단계

1. **인자 파싱**: `--session`, `--plan`, `--resume`, `--phase <n>` (선택; 해석된 세션이 `kind:"phase"` 이면 `phase_index` 에서 `n` 을 추론).

2. **세션 해석**. `--session` 이 없으면 `_active.json` 에서 기본값을 가져온다.

3. **plan 경로 해석** (`/css:review` 와 동일한 규칙).

4. `session.language_profile` 이 설정되어 있지 않으면 **언어 프로파일 감지**. spec(섹션: Language Detection Logic)의 감지 로직을 실행한다. 해석된 프로파일을 세션에 기록한다.

5. **사전 점검(Pre-flight): rich-spec 준비 상태 확인**:
   - `kind:"phase"` 세션: `<project>/.claude/css/plans/{parent_slug}-p{phase_index}-T*.md` 를 나열한다.
   - 레거시 세션: `<project>/.claude/css/plans/*-spec-{slug}-*.md` 를 나열한다.
   - 전문가에게 라우팅된 모든 plan 태스크에 대해, 해당 산출물에 `RED scaffold:` + `GREEN template:` 을 가진 `## Task {id}` 섹션이 있고 `Phase: {phase_index}` 로 태그되어 있는지 확인한다.
   - 누락된 것이 있으면 → "rich-spec 누락. `/css:review` 를 먼저 통과시켜주세요 (verdict=PASS)." 로 중단한다.

6. **worktree 설정** (`--resume` 가 아닌 경우):
   - 저장소 이름 계산: `basename $(git rev-parse --show-toplevel)`.
   - `kind:"phase"` 세션: worktree 경로 = `../{repo}-css-{parent_slug}-p{phase_index}`; 브랜치 = `css/{parent_slug}/p{phase_index}`; Phase 세션에서 읽은 `base_branch` 로부터 생성.
   - 레거시 세션: worktree 경로 = `../{repo}-css-{slug}`; 브랜치 = `css/{slug}`; base = 현재 브랜치.
   - 경로가 이미 존재하면: 사용자에게 질문 "기존 worktree 가 있습니다. [재사용 / 새로 만들기 / 취소]".
   - 새로 만드는 경우: `git worktree add <path> -b <branch> <base_branch>`.
   - 세션에 `phases.execute.worktree = <path>`, `phases.execute.branch = <branch>`, `phases.execute.base_branch = <base_branch>` 를 기록한다.

7. **마스터 플로우 가드** + **Gate 2 확인**:
   - **마스터 플로우 가드** (NEW):
     - `session.master_flow == true` 이고 `session.gates.gate2_pre_execute.state != "approved"` 이면 중단한다:
       "Gate 2가 승인되지 않았습니다. `/css:ship --session <name>`을 통해 진행하세요."
     - `master_flow == true` 이고 승인된 상태이면 프롬프트 없이 진행한다.
   - **AskUserQuestion (마스터 플로우 Gate 2)** — `/css:ship` 의 일부로 호출되었고(즉 `session.master_flow == true`) gate2_pre_execute.state 가 아직 "approved" 가 아닌 경우에만:
     "Plan 검증 완료. worktree '`<path>`' 생성 후 execute 를 시작합니다. 배치 N개, 작업 M개. 진행할까요? [Yes / Show plan / Cancel]"

8. **헤더 출력**: `[css:execute @ slug={slug}]`.

9. **executor 디스패치**:

   ```
   Task(
     subagent_type="css-executor",
     description="css execute: {slug}",
     prompt="""
     <inputs>
     plan: {plan path}
     worktree: {worktree path}
     branch: {branch}
     base_branch: {base_branch}
     phase_index: {phase_index or null}
     language_profile: {profile object}
     session: <project>/.claude/css/sessions/{slug}.json
     rich_specs_dir: <project>/.claude/css/plans/
     </inputs>
     <task>
     첫 번째 동작 — 파일 읽기 전: `cd {worktree path} && pwd`.
     디렉토리 진입 실패 시 VERDICT=ESCALATE로 중단.
     이후 모든 파일 경로는 {worktree path} 기준 상대 경로다.
     절대 경로가 {worktree path}로 시작하지 않는 파일은 쓰거나 편집하거나 삭제하지 않는다.

     Implement the plan task-by-task using strict Red-Green-Refactor TDD with the cache-first protocol:
       - RED: copy the matching rich-spec section's RED scaffold to the worktree, run, must fail.
       - GREEN: copy the matching rich-spec section's GREEN template, run tests.
       - On failure: css-debugger × 2 → specialist fallback × 1 → abort.
       - REFACTOR: css-code-simplifier (read-only suggestions).
       - COMMIT: per-task, on css/{slug}, with CSS-Slug / CSS-Task / CSS-Specialist-Spec / CSS-Specialist-Fallback trailers as applicable. No Claude/AI attribution in the message — no "Co-Authored-By: Claude" trailer, no "🤖 Generated with [Claude Code]" line.
     Per-batch user checkpoints via AskUserQuestion. Coverage measured after each batch; below threshold → css-test-engineer (max 2 rounds).
     Index all rich-spec artifacts under rich_specs_dir before starting (build task_id → (spec_path, anchor) map).
     </task>
     <output_contract>
     Write exec log to: <project>/.claude/css/executions/exec-log-{slug}-{ts}.md (for kind:"phase", use exec-log-{parent_slug}-p{phase_index}-{ts}.md)
     Log MUST record cache_miss_count per slug.
     Final line: VERDICT=PASS | VERDICT=ESCALATE | VERDICT=PAUSE
     </output_contract>
     """
   )
   ```

9b. **락 및 active 추적**: 락 키 = `locks/{slug}-execute.lock` (`kind:"phase"` 인 경우 `slug` 는 자식 슬러그 — 형제 Phase 마다 구분되며 충돌 없음). `_active.json` 갱신 시 `active_epic`(`parent_slug` 또는 자신)과 `active_phase`(`phase_index` 또는 null)도 함께 설정한다.

10. **판정 파싱**:
    - `PASS` → 세션: `phases.execute.status = completed`. 다음 단계를 안내한다.
    - `ESCALATE` → 사용자에게 사유를 노출하고 옵션 제시 [배치 재시도 / 수용하고 계속 / 중단].
    - `PAUSE` → 사용자가 취소함. `--resume` 를 위해 상태를 보존한다.

11. **락 해제**.

<self_check>
- [ ] Worktree path recorded in session
- [ ] Branch css/{slug} created and contains task commits
- [ ] exec-log file exists with cache_miss_count recorded
- [ ] Coverage measured and recorded
- [ ] `git -C <main-project-root> status` 에 예상치 못한 수정 사항 없음
</self_check>

$ARGUMENTS
