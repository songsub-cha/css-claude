<!-- css:updated: 079b623 2026-07-04 -->

# ADR-0005: GitHub Issues/Projects 파이프라인 추적

- **상태**: accepted
- **날짜**: 2026-06-15
- **출처**: `docs/superpowers/specs/2026-06-15-github-pipeline-tracking-design.md:215-220` (합의된 결정)

## 배경 (Context)

파이프라인 진행 상황을 사람이 터미널 밖에서도 확인·승인할 수 있어야 했다. 상주 서버나 웹훅 없이, 개인 설치 전제(ADR-0001)를 지키면서 GitHub만으로 이슈 추적 + 승인 게이트 원격 응답을 구현해야 했다.

## 결정 (Decision)

- 게이트 대기는 **인라인 폴링(서버 없음)** — 이전에 검토되었던 대시보드는 전면 삭제.
- 게이트 채널은 **터미널 우선 + 이슈 기록** — "원격" 선택 시에만 이슈 폴링으로 전환.
- 보드는 **유저 단위 통합 Projects 보드 1개**.
- 크로스플랫폼을 위해 `gh_sync.sh` bash 헬퍼 채택.
- Epic/Phase v1(서브이슈 중첩)을 포함.
- PR 본문의 `Closes #`로 이슈 자동 종료.
- interview/plan/document 코멘트는 산출 문서 전문을 첨부(청크 분할).
- 게이트 대기 알림은 9분 간격.
- 테스트는 순수 bash assert 하네스(pytest/외부 프레임워크 없음).

## 결과 (Consequences)

- `lib/gh_sync.sh` 하나가 Issues/Projects/PR/Wiki 네 가지 GitHub 연동을 모두 담당하는 단일 진입점이 되었다.
- **정본은 로컬** 원칙이 확립되었다 — GitHub는 항상 사람용 미러이고 세션 JSON이 상태의 정본이므로, `gh` 장애 시에도 파이프라인 자체는 항상 동작한다(graceful degradation).
- 트레이드오프: 원격 게이트 폴링은 호출당 최대 9분까지 블로킹되며, 응답이 없으면 재폴링해야 한다(서버 웹훅 대비 지연 있음).
- 이 결정은 이후 [ADR-0007](ADR-0007-project-docs-curation.md)의 Wiki 미러 기능이 같은 `gh` 가용성 폴백 철학을 그대로 재사용하는 토대가 되었다.
