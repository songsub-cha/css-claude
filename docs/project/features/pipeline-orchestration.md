<!-- css:updated: 079b623 2026-07-04 -->

# 파이프라인 오케스트레이션

## 1. 현재 동작

`/css:ship "<아이디어>"`는 8단계 파이프라인을 순차 실행합니다: interview → plan → phase → review → execute → verify → document → pr, 그 사이 3개의 사람 승인 게이트(Gate 1은 브레인스토밍 자체의 스펙 승인, Gate 2는 실행 전, Gate 3는 PR 전)가 개입합니다 (`commands/ship.md:6-8`). 각 단계는 독립 슬래시 커맨드로도 실행 가능하며 `--session <slug>`로 중단 지점부터 재개합니다 (`docs/usage.md:15-32`).

세션은 `<project>/.claude/css/sessions/<slug>.json`에 저장되고, `_active.json`이 가장 최근 슬러그를 가리키는 last-writer-wins 편의 포인터 역할을 합니다 (`docs/session-schema.md:76-81`). 두 터미널에서 서로 다른 아이디어를 동시에 진행해도 슬러그별로 완전히 격리됩니다 (`docs/usage.md:45-57`).

머지 후 정리는 `/css:clean`이 담당하며, dirty·미푸시·미머지 상태를 사람 확인 없이 삭제하지 않습니다 (`commands/clean.md:8, 15-19`).

## 2. 인터페이스

### CLI (슬래시 커맨드)

| 커맨드 | 설명 | 산출물 |
|---|---|---|
| `/css:ship [--session <name>] <idea>` | 전체 파이프라인 실행, 3-게이트 | 완료된 PR | 
| `/css:interview [--session <name>] <idea>` | `superpowers:brainstorming` 래핑 | `docs/superpowers/specs/YYYY-MM-DD-*.md` |
| `/css:plan [--session <name>] [--from <path>]` | `superpowers:writing-plans` 래핑, skeleton/detailed 분기 | `docs/superpowers/plans/YYYY-MM-DD-*.md` |
| `/css:review [--session <name>] [--plan <path>]` | Single-Specialist Task Rule 감사 + Rich Spec dispatch | `.claude/css/plans/{slug}-T{id}.md` |
| `/css:execute [--session <name>] [--resume]` | 격리 worktree에서 RED→GREEN→REFACTOR TDD | `css/<slug>` 브랜치 |
| `/css:verify [--session <name>] [--exec-log <path>]` | 테스트/커버리지/기준/코드·보안 리뷰 재검증 | 검증 리포트 |
| `/css:document [--session <name>]` | 사용자 대면 문서 생성 | `docs/<slug>/README.md` |
| `/css:pr [--session <name>] [--draft]` | 브랜치 push + PR 생성 | PR URL |
| `/css:clean [--session <name>] [--keep-branch] [--force]` | 머지 후 worktree/브랜치 정리 | — |

상세 계약(파라미터, 세션 필드)은 각 `commands/*.md`를 참조하세요. 개별 커맨드 명세는 `docs/<slug>/api.md` 성격의 문서가 아직 없어 커맨드 소스가 곧 계약입니다.

## 3. 내부 설계 요점

(모듈 구조와 다이어그램은 [architecture.md](../architecture.md)를 참조 — 여기서는 architecture.md와 중복하지 않는 이 영역 고유 규칙만 기술합니다.)

- **락**: 스테이지별 `locks/{slug}-{stage}.lock`, 60분 stale 자동 교체, 모든 종료 경로에서 해제 (`docs/session-schema.md:83-88`).
- **루프백 한도**: review는 `config.review.max_loopback_attempts`(기본 2), verify는 `config.verify.max_loopback_attempts`(기본 3) — 초과 시 `ESCALATE` (`commands/review.md:13`, `commands/verify.md:12`).
- **`master_flow` 플래그**: `/css:ship`가 세팅하면 하위 스테이지 커맨드는 자체 게이트 질문을 생략하고 세션에 저장된 게이트 승인을 그대로 신뢰합니다 (`docs/session-schema.md:39`).
- **언어 프로파일 자동 감지**: `pyproject.toml`/`uv.lock`→Python, `package.json`→Node, `pom.xml`→Maven, `build.gradle[.kts]`→Gradle, `go.mod`→Go, 그 외는 사용자에게 질의 (`commands/execute.md:13-19`).

## 4. 데이터

이 영역은 세션 JSON(`phases.*`, `gates.*`, `retries`, `language_profile`)을 직접 소유합니다. 필드별 소유자·소비자는 [data/schema.md](../data/schema.md#session)를 참조하세요.

## 5. 제약·알려진 한계

- `_active.json`은 last-writer-wins이므로 동시에 2개 이상의 세션이 활성일 때 병렬 Phase 실행 시 반드시 `--session`을 명시해야 한다 (`docs/usage.md:45-57`, `commands/ship.md:159`).
- 표준 loopback 실패 시나리오(RED이 실패하지 않음, 커버리지 미달)는 [operations/troubleshooting.md](../operations/troubleshooting.md)에 별도 정리.

## 6. 변경 이력

| 날짜 | slug | 요약 | PR |
|---|---|---|---|
| 2026-05-27 | (초기 설계) | 커맨드=오케스트레이터/에이전트=워커 3-게이트 파이프라인 초안 | 미확인 |
| 2026-07-04 | (bootstrap) | `docs/project/` 최초 생성 — 이 페이지 신설 | — |
