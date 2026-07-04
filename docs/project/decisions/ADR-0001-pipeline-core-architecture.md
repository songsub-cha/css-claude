<!-- css:updated: 079b623 2026-07-04 -->

# ADR-0001: CSS 파이프라인 핵심 아키텍처

- **상태**: accepted
- **날짜**: 2026-05-27
- **출처**: `docs/specs/2026-05-27-css-pipeline-design.md:37-53` (Decisions Summary)

## 배경 (Context)

개인용 아이디어→PR 자동화 파이프라인을 Claude Code 위에 구축해야 했다. 요구사항은: OMC(oh-my-claudecode) 없이 독립적으로 동작할 것, 고비용 결정 지점에는 사람의 승인이 개입할 것, 여러 언어 생태계를 자동 감지할 것, 실패 시 무한 루프 없이 사용자에게 에스컬레이션할 것.

## 결정 (Decision)

- 설치 위치는 `~/.claude/commands/css/` 전역 커맨드, `/css:command` 네임스페이스.
- OMC 의존성 없음 — 완전 독립.
- 마스터 커맨드(`/css:ship`)는 3개 사용자 승인 게이트를 가진다: interview 스펙 승인, execute 전, PR 전.
- 언어 자동 감지: JS/TS, Python, Go, Rust, Java(Maven), Java/Kotlin(Gradle, Android 포함).
- 산출물 저장 위치는 `<project>/.claude/css/` (휘발성 부분만 gitignore).
- 루프백 제어는 AI 자동 판단, review 최대 2회·verify 최대 3회 시도 후 사용자 에스컬레이션.
- interview는 `superpowers:brainstorming`을 통한 1회 1질문 방식, plan은 `superpowers:writing-plans`를 통함.
- 아키텍처는 모듈형: 커맨드=얇은 오케스트레이터, 에이전트=실작업자.
- 에이전트 시스템 프롬프트는 영어(정책 정밀성), 사용자 대면 메시지/산출물은 한국어.
- 배포 범위는 2단계: private GitHub 저장소 + 수동/스크립트 설치(Windows PowerShell + Ubuntu 22.04 Bash).

## 결과 (Consequences)

- 모든 하위 기능(Epic/Phase 분해, GitHub 추적, Codex 호환, 플러그인 배포, docs/project 큐레이션)은 이 골격 위에 증분으로 추가되었다 — 커맨드는 항상 얇고, 실제 읽기/쓰기는 에이전트가 담당하는 경계가 유지되었다.
- 3-게이트 구조는 이후 GitHub 추적(ADR-0005)에서 원격 이슈 승인으로 확장되었을 때도 그대로 재사용되었다.
- 루프백 한도(review 2회/verify 3회)는 `config/default-config.json`의 기본값으로 그대로 굳어졌다.
- 트레이드오프: 개인 설치 전제이므로 멀티테넌시·권한 분리는 설계에 없다.
