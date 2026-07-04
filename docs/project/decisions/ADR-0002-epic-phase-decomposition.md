<!-- css:updated: 079b623 2026-07-04 -->

# ADR-0002: Epic/Phase 세션 분해

- **상태**: accepted
- **날짜**: 2026-05-29
- **출처**: `docs/superpowers/specs/2026-05-29-epic-phase-pipeline-design.md:54-67` (Decisions Summary, D1–D10 "locked")

## 배경 (Context)

대형 피처는 `plan` 단계에서 수십 개 태스크/여러 배치를 완전한 코드로 생성하고, `review` 단계에서 모든 태스크의 RED/GREEN을 한꺼번에 만들어 세션 토큰이 ~1M을 초과하고 하나의 거대한 PR로 뭉쳐지는 문제가 있었다. 근본 원인은 `plan`과 `review`가 Epic 전체 범위에서 한 번에 실행되는 것이었다.

## 결정 (Decision)

- 용어를 Project/Epic/Phase/Stage 4레벨로 고정(D1).
- DB는 별도 `epics` 테이블 없이 `sessions_history`에 컬럼만 추가(D2, 대시보드 레이어 계획 — 미구현).
- document 단계는 Phase별로 실행하고 Epic 집계 README는 선택사항으로 보류(D3).
- 2단계 plan: Epic은 skeleton(코드 없는 거친 태스크+배치), Phase는 detailed(완전 코드)(D4).
- detailed-plan/rich-spec-review/execute/verify/document/pr은 전부 Phase(자식 세션) 단위로 실행(D5).
- 브랜치/PR 전략: Phase당 PR 1개, 의존 Phase는 스택 브랜치, 독립 Phase는 Epic 베이스에서 분기(D6).
- 분해 트리거: `task_count > 20` OR `batch_count > 4`일 때만(D7).
- 2단계 review: Epic은 아키텍처/커버리지 감사만, rich-spec(RED/GREEN)은 Phase에서만 저작(D8).
- 하위 호환: `kind` 필드가 없는 기존 세션은 단일-Phase Epic으로 렌더링(D9).
- 상세 전개(detailed plan + rich-spec)는 항상 Phase 스코프에서만 실행 — 토큰 폭증의 근본 해결책(D10).

## 결과 (Consequences)

- Epic 세션은 저비용(코드 생성 없음)이 되고, Phase 세션만 격리된 worktree+브랜치+PR을 생성한다.
- 락과 `_active.json`의 단위가 Epic에서 Phase(자식 슬러그)로 이동해 형제 Phase가 서로 차단하지 않게 되었다.
- 트레이드오프: 병렬 Phase 실행의 자동 오케스트레이션과 파일 충돌 감지는 범위 밖으로 남았다(Phase B 대상, 미구현) — [features/epic-phase-decomposition.md](../features/epic-phase-decomposition.md) §5 참조.
- 대시보드(DB 마이그레이션 + 프론트엔드)로 이어질 Phase B는 계획만 되었고, 이후 계획 문서명(`...-p3-dashboard-removal.md`)이 시사하듯 오히려 제거 방향으로 재논의된 것으로 보이나 코드베이스에 구현 흔적이 없어 미확인.
