<!-- css:updated: 079b623 2026-07-04 -->

# 트러블슈팅

이 페이지는 `docs/troubleshooting.md`를 근거로 증상별 원인/진단/조치 형식으로 재구성한 것입니다. 원문이 갱신되면 이 페이지도 함께 병합됩니다.

## "CSS requires the superpowers plugin"

- **원인**: `/css:interview`와 `/css:plan`은 `superpowers` 플러그인에 의존하는데 비활성 상태 (`docs/troubleshooting.md:3-5`).
- **진단**: `~/.claude/settings.json`의 `enabledPlugins["superpowers@claude-plugins-official"]`가 `true`인지 확인.
- **조치**: `/plugin enable superpowers@claude-plugins-official` 실행, 또는 `~/.claude/settings.json`에 직접 `{"enabledPlugins": {"superpowers@claude-plugins-official": true}}` 추가 (`docs/troubleshooting.md:7-19`).
- **관련**: [features/pipeline-orchestration.md](../features/pipeline-orchestration.md).

## "gh not found" (during /css:pr)

- **원인**: GitHub CLI 미설치.
- **진단**: `gh --version` 실패.
- **조치**: https://cli.github.com/manual/installation 에서 설치 후 `gh auth login` (`docs/troubleshooting.md:21-23`).
- **관련**: [features/github-tracking.md](../features/github-tracking.md), [operations/configuration.md](configuration.md).

## "Worktree already exists for slug X"

- **원인**: 동일 슬러그의 이전 execute 실행이 worktree를 정리하지 않고 남김.
- **진단**: CSS가 재사용 여부를 프롬프트로 물어봄.
- **조치**: 기존 worktree를 재사용하거나 `git worktree remove ../<repo>-css-<slug>` 후 재시작 (`docs/troubleshooting.md:25-27`).
- **관련**: [features/pipeline-orchestration.md](../features/pipeline-orchestration.md), [operations/runbook.md](runbook.md) §5.

## "Same-slug collision: another session is in phase Y"

- **원인**: 두 터미널이 동일 슬러그로 동시에 실행.
- **진단**: 락 파일(`locks/{slug}-{stage}.lock`)의 `acquired_at`을 확인.
- **조치**: 대기하거나 다른 아이디어/슬러그 사용. 락이 30분 이상 stale이면 CSS가 경고와 함께 자동 해제 (`docs/troubleshooting.md:29-31`). (주: `docs/session-schema.md:85-88`은 커맨드별 stale 기준을 60분으로 명시 — 두 문서 간 수치 차이가 있어 **미확인**으로 표기하고 원문을 정본으로 우선함.)
- **관련**: [architecture.md 횡단 관심사 — 락 규약](../architecture.md#6-횡단-관심사).

## "RED failed: tests did not fail"

- **원인**: TDD RED 단계는 구현 전에 테스트가 실패해야 하는데 실패하지 않음 — plan의 테스트가 이미 참인 것을 assert하거나, 이전 태스크가 이미 구현을 추가함.
- **진단**: 해당 태스크의 RED scaffold/명령을 직접 재실행.
- **조치**: `/css:review --session <slug>`로 plan을 재감사 (`docs/troubleshooting.md:33-39`).
- **관련**: [features/pipeline-orchestration.md](../features/pipeline-orchestration.md).

## "Coverage below 85% after self-heal"

- **원인**: `css-test-engineer`가 2회 호출되었지만 임계치(기본 85%)에 도달하지 못함.
- **진단**: verify 로그의 커버리지 리포트 경로 확인.
- **조치**: 수동으로 테스트 추가, 또는 `<project>/.claude/css/config.json`에서 프로젝트별로 `verify.coverage_threshold`를 낮춤 (`docs/troubleshooting.md:41-43`).
- **관련**: [operations/configuration.md](configuration.md) §2.1.

## "session.json schema mismatch"

- **원인**: 새 CSS 버전이 더 새로운 세션 스키마를 기대함.
- **진단**: `tools/css_schema/schema.py`의 `validate_session`이 기대하는 필드와 실제 세션 파일을 비교.
- **조치**: 기존 버전으로 현재 세션을 마무리한 뒤 업그레이드하거나, `<project>/.claude/css/sessions/<slug>.json.bak.<ts>`로 백업 후 새 버전으로 세션을 재시작 (`docs/troubleshooting.md:45-49`).
- **관련**: [data/schema.md](../data/schema.md).

## Old Codex `/css-*` prompts still appear

- **원인**: 구버전 Codex 설치가 `~/.codex/prompts/css-*.md`에 커스텀 프롬프트 파일을 생성했고, 현재 설치(스킬 기반, `~/.agents/skills/css-*/SKILL.md`)는 이를 자동 제거하지 않음.
- **진단**: `~/.codex/prompts/css-*.md` 존재 여부 확인.
- **조치**: `rm ~/.codex/prompts/css-*.md` (Windows: `Remove-Item "$env:USERPROFILE\.codex\prompts\css-*.md"`) (`docs/troubleshooting.md:51-63`).
- **관련**: [features/codex-compatibility.md](../features/codex-compatibility.md).

## 실패한 세션 정리

- **원인**: 세션이 중단되었거나 더 이상 필요 없음.
- **진단**: `<project>/.claude/css/sessions/<slug>.json` 존재 및 worktree/브랜치 잔존 여부.
- **조치**:
  ```bash
  rm <project>/.claude/css/sessions/<slug>.json
  git worktree remove ../<repo>-css-<slug>
  git branch -D css/<slug>   # 푸시되지 않았을 때만
  ```
  (`docs/troubleshooting.md:65-76`)
- **관련**: [operations/runbook.md](runbook.md) §5, `/css:clean`([features/pipeline-orchestration.md](../features/pipeline-orchestration.md)).
