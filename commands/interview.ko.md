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
   - **저장소(repo) 메타데이터 수집** (NEW):
     - `repo_root = git -C <project> rev-parse --show-toplevel`
     - `repo_name = basename(repo_root)`
     - 세션 JSON 에 기록: `session.repo_root`, `session.repo_name`.
     - `git rev-parse` 가 실패하면(git 저장소가 아님) `repo_root = <project>`, `repo_name = basename(<project>)` 을 사용하고 계속 진행한다.
   - `<project>/.claude/css/sessions/_active.json` 을 `{"latest_slug": "<slug>"}` 로 갱신한다.
   - phase 락(lock)을 획득한다.

3. **superpowers 활성화 여부 확인**: `~/.claude/settings.json` 을 읽는다. `enabledPlugins["superpowers@claude-plugins-official"]` 이 true 가 아니면 다음 메시지로 중단한다: "CSS requires the superpowers plugin. Enable via /plugin and retry."

4. **헤더 출력**: 응답의 첫 줄에 `[css:interview @ slug={slug}]` 을 출력한다.

5. **brainstorming 호출**:
   ```
   Skill("superpowers:brainstorming")
   ```
   호출된 스킬의 컨텍스트 안에서 아이디어 텍스트를 사용자의 최초 요청으로 전달한다. **중요 오버라이드**: brainstorming 이 종료 단계인 "Invoke writing-plans skill" 에 도달하더라도 writing-plans 를 자동 호출하지 **않는다**. CSS 는 각 명령을 독립적으로 실행 가능하게 유지하기 위해 `/css:plan` 을 별도 단계로 호출한다. brainstorming 에게 다음과 같이 지시한다: "Stop after the user-approves-spec gate; CSS will continue from there."

   **최소 질문 깊이**: brainstorming 에게 spec 초안을 작성하기 전에 아이디어를 충분히 구체화하기 위해 **최소 10개 이상**의 실질적인 질문을 하도록 지시한다. 더 적은 질문으로 spec 으로 건너뛰지 말 것 — 요구사항, 범위, 엣지 케이스, 설계 트레이드오프를 아이디어가 구체화될 때까지 계속 파고든다.

6. **brainstorming 완료 시**:
   - brainstorming 이 작성한 spec 파일을 찾는다(일반적으로 `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`).
   - 세션 파일 갱신: `phases.interview.status = "completed"`, `phases.interview.artifact = "<spec path>"`, `phases.interview.completed_at = <ISO timestamp>`.
   - `_active.json` 을 새로고침한다.

7. **락 해제** 후 다음 단계를 안내한다:
   "Spec 작성 완료: `<spec path>`. 다음 단계: `/css:plan` 또는 `/css:ship --session <slug>`로 진행."

<self_check>
- [ ] Artifact written by brainstorming (spec markdown file exists)
- [ ] session file (sessions/{slug}.json) phase status updated to completed
- [ ] _active.json.latest_slug updated
- [ ] Final line contains NEXT=plan or ARTIFACT=<spec path>
- [ ] No policy violations
</self_check>

$ARGUMENTS
