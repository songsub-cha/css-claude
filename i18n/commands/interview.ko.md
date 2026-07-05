---
description: 아이디어를 superpowers:brainstorming 으로 spec 으로 구체화 (CSS 파이프라인 1단계)
argument-hint: "[--session <name>] <idea>"
---

# /css:interview

깊이 있는 소크라테스식 브레인스토밍 세션을 진행해 아이디어를 CSS spec 으로 전환한다. `superpowers:brainstorming` 을 감싼다(wrap).

## 단계

1. **인자 파싱**: `--session` 이 있으면 추출하고, 나머지는 아이디어 텍스트로 처리한다.

2. **세션 해석(resolve)**:
   - `--session <name>` 이 주어졌고 `<project>/.claude/css/sessions/<name>.json` 이 존재하면 → 이어서 진행(resume).
   - 그렇지 않으면 아이디어로부터 새 kebab-case 슬러그를 생성한다(예: "JWT auth middleware" → `jwt-auth-middleware`). 생성된 슬러그가 기존 세션 파일과 충돌하면 숫자 접미사를 붙인다.
   - 새 세션이면 `<project>/.claude/css/sessions/<slug>.json` 을 초기화하고, 이어서 진행하는 경우면 로드한다.
   - 새 세션은 반드시 `kind:"epic"` 과 `single_phase:false` 로 시작해 첫 plan 이 `/css:phase` 대상인 스켈레톤이 되게 한다. kind 없는 레거시 세션을 단순히 resume 할 때는 이 필드들을 추가하지 않는다; 레거시 세션은 상세 단일 세션 호환 경로를 유지한다.
   - **저장소(repo) 메타데이터 수집** (필드가 없을 때마다 — 새 세션과 resume 되는 레거시 세션 모두):
     - `repo_root = git -C <project> rev-parse --show-toplevel`
     - `repo_name = basename(repo_root)`
     - `base_branch = git -C <project> rev-parse --abbrev-ref HEAD`(detached 이거나 git 저장소가 아니면 폴백 `main`) — 이후 worktree 생성과 PR base 의 기본값이 된다.
     - 세션 JSON 에 기록: `session.repo_root`, `session.repo_name`, `session.base_branch`.
     - `git rev-parse` 가 실패하면(git 저장소가 아님) `repo_root = <project>`, `repo_name = basename(<project>)` 을 사용하고 계속 진행한다.
   - **파이프라인 config 로드** (`session.config` 이 없을 때): 사용자 config `~/.claude/css/config.json`(있으면)을 번들 `config/default-config.json`(플러그인 모드에서는 플러그인 디렉토리 아래, 스크립트 모드에서는 `~/.claude/css/`) 위에 deep-merge 한다. 둘 다 읽을 수 없으면 문서화된 기본값을 사용한다: `verify.coverage_threshold` 85, `review.max_loopback_attempts` 2, `verify.max_loopback_attempts` 3, `execute.tdd_self_heal_max` 2. 병합된 객체를 `session.config` 로 저장하고 `session.retries = {review: 0, verify: 0}` 을 초기화한다 — 다운스트림 단계가 둘 다 읽는다.
   - `<project>/.claude/css/sessions/_active.json` 을 `{"latest_slug": "<slug>", "active_epic": "<slug>", "active_phase": null}` 로 갱신한다(새 세션은 이 시점에 항상 Epic 이므로 `active_epic` 은 자기 자신).
   - interview 락을 획득한다: `<project>/.claude/css/locks/{slug}-interview.lock` 에 `{acquired_at}` 을 담는다(60분 경과 시 stale → 안내와 함께 교체; 다른 실행의 신선한 락 → 안내와 함께 중단).

3. **superpowers 활성화 여부 확인**: `~/.claude/settings.json` 을 읽는다. `enabledPlugins["superpowers@claude-plugins-official"]` 이 true 가 아니면 다음 메시지로 중단한다: "CSS requires the superpowers plugin. Enable via /plugin and retry."

4. **헤더 출력**: 응답의 첫 줄에 `[css:interview @ slug={slug}]` 을 출력한다.

5. **brainstorming 호출**:
   ```
   Skill("superpowers:brainstorming")
   ```
   호출된 스킬의 컨텍스트 안에서 아이디어 텍스트를 사용자의 최초 요청으로 전달한다. **중요 오버라이드**: brainstorming 이 종료 단계인 "Invoke writing-plans skill" 에 도달하더라도 writing-plans 를 자동 호출하지 **않는다**. CSS 는 각 명령을 독립적으로 실행 가능하게 유지하기 위해 `/css:plan` 을 별도 단계로 호출한다. brainstorming 에게 다음과 같이 지시한다: "Stop after the user-approves-spec gate; CSS will continue from there."

   **최소 질문 깊이**: brainstorming 에게 요구사항, 범위, 엣지 케이스, 설계 트레이드오프를 아이디어가 구체화될 때까지 계속 파고들도록 지시한다 — feature/Epic 규모 아이디어는 일반적으로 **최소 10개 이상**의 실질적인 질문, 정말로 작고 이미 구체적인 변경이라도 **최소 3개 미만은 절대 안 됨**. 범위, 엣지 케이스, 트레이드오프가 열려 있는 한 spec 으로 절대 건너뛰지 않는다.

6. **brainstorming 완료 시**:
   - brainstorming 이 작성한 spec 파일을 찾는다(일반적으로 `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`).
   - 세션 파일 갱신: `phases.interview.status = "completed"`, `phases.interview.artifact = "<spec path>"`, `phases.interview.completed_at = <ISO timestamp>`.
   - `_active.json` 을 새로고침한다.

7. **락 해제** 후 다음 단계를 안내한다:
   "Spec 작성 완료: `<spec path>`. 다음 단계: `/css:plan` 또는 `/css:ship --session <slug>`로 진행."
   마지막 줄(단독 줄, 정확한 접두사): `ARTIFACT=<spec path>`.

<self_check>
- [ ] Artifact written by brainstorming (spec markdown file exists)
- [ ] session file (sessions/{slug}.json) phase status updated to completed
- [ ] _active.json.latest_slug updated
- [ ] Final line is `ARTIFACT=<spec path>`
- [ ] No policy violations
</self_check>

$ARGUMENTS
