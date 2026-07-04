<!-- css:updated: 079b623 2026-07-04 -->

# Epic/Phase 분해

## 1. 현재 동작

대형 아이디어는 `plan`(완전 코드) + `review`(태스크별 RED/GREEN)가 Epic 전체 범위에서 한 번에 펼쳐지면 세션 토큰이 ~1M을 초과할 수 있습니다. 이를 막기 위해 상세 전개를 Phase로 연기합니다: **Epic 세션**은 interview + skeleton plan + phasing + 아키텍처 review만 실행하고 코드를 생성하지 않으며, **Phase 세션**은 자신의 배치만을 위한 detailed plan + rich-spec review + execute + verify + document + pr을 실행해 독립 PR을 만듭니다 (출처: `docs/epic-phase-pipeline/README.md:5-13`).

4레벨 용어: Project(레포지터리) > Epic(피처/아이디어=Phase들의 컨테이너) > Phase(배포 가능한 증분=PR 1개) > Stage(세션 내부 파이프라인 단계) (`docs/epic-phase-pipeline/README.md:16-23`).

**분해 트리거**: `/css:phase`가 `task_count > 20` OR `batch_count > 4`일 때만 다중 Phase로 분해를 제안하고, 그 미만이면 기존 단일 세션 경로를 그대로 유지합니다 (`commands/phase.md:14`, `tools/css_schema/derive.py`의 `should_phase` — `docs/epic-phase-pipeline/README.md:64-73`).

## 2. 인터페이스

`/css:phase [--session <name>] [--slug <legacy-name>]` — Epic 세션에서 매니페스트를 승인 게이트로 제안하고, 승인되면 자식 Phase 세션들을 생성합니다 (`commands/phase.md:1-27`).

- 임계치 미만: 단일 세션에 `single_phase:true`를 세팅하고 `/css:plan`을 detailed로 재실행 (`commands/phase.md:16-19`).
- 임계치 이상: 매니페스트(`idx`/`label`/`batches`/`depends_on`) 제안 → 사용자 승인 → `.claude/css/plans/phase-manifest-{slug}.json`에 영속화, 자식 세션 생성 (`commands/phase.md:20-27`).

브랜치/워크트리/문서 경로 명명 규칙 (`docs/epic-phase-pipeline/README.md:239-248`):

| 항목 | 패턴 | 예시 |
|---|---|---|
| Phase 슬러그 | `<epic>-p<idx>` | `my-epic-p2` |
| Phase 브랜치 | `css/<epic>/p<idx>` | `css/my-epic/p2` |
| 워크트리 경로 | `../<repo>-css-<epic>-p<idx>` | `../my-repo-css-my-epic-p2` |
| 문서 경로 | `docs/<epic>/p<idx>/README.md` | `docs/my-epic/p2/README.md` |
| 잠금 키 | `locks/<child-slug>-<stage>.lock` | `locks/my-epic-p2-execute.lock` |

세부 파생 함수(`should_phase`, `phase_slug`, `phase_branch`, `base_branch_for`)는 `docs/epic-phase-pipeline/README.md:62-103`에 실행 예시가 있습니다 (근거: `tools/css_schema/test_derive.py:12-28`).

## 3. 내부 설계 요점

- **2레벨 plan+review**: Multi-Phase Epic은 스켈레톤 plan(코드 없음) + 아키텍처 review(rich-spec 없음)만; Single-Phase Epic과 Phase는 detailed plan + rich-spec review (`docs/epic-phase-pipeline/README.md:181-189`, `commands/plan.md:16-17`, `commands/review.md:15-17`).
- **스택 PR 전략**: 독립 Phase(`depends_on:[]`)는 Epic 베이스에서 분기, 의존 Phase는 선행 Phase 브랜치에 스택 (`docs/epic-phase-pipeline/README.md:191-201`).
- **락/`_active.json` 단위 이동**: Epic 수준이 아니라 자식 슬러그 단위(`<child_slug>-<stage>.lock`)로 잠겨 형제 Phase가 서로 차단하지 않음; `_active.json`에 `active_epic`/`active_phase` 추가 (`docs/epic-phase-pipeline/README.md:250-263`).
- **레거시 호환(D9)**: `kind` 필드가 없는 기존 세션은 단일-Phase Epic으로 렌더링 (`tools/css_schema/schema.py:71`, `docs/epic-phase-pipeline/README.md:126-134`).
- 매니페스트 유효성 검사 규칙(고유 증가 `idx`, 비어있지 않은 `batches`, 순방향/미존재 `depends_on` 거부)은 `tools/css_schema/schema.py:9-38`.

## 4. 데이터

Epic/Phase 세션 필드(`kind`, `parent_slug`, `phase_index`, `depends_on`, `phase_manifest`, `child_slugs`)는 [data/schema.md](../data/schema.md#session)에 정리되어 있습니다.

## 5. 제약·알려진 한계

- 병렬 Phase 실행(독립 `depends_on`)은 `commands/ship.md:159`에서 "MAY be dispatched"로만 명시되어 있고, 자동 오케스트레이션은 아직 구현되지 않았다 (`docs/epic-phase-pipeline/README.md:320-322`, Phase B 대상).
- 병렬 Phase가 같은 파일을 수정하면 수동 해결이 필요하며, 아키텍처 review에서 파일 겹침 경고는 아직 없다 (`docs/epic-phase-pipeline/README.md:324-326`).
- Epic 수준의 집계 README(여러 Phase를 하나로 묶는 문서)는 의도적으로 보류 중 (`docs/epic-phase-pipeline/README.md:316-318`, D3).
- 대시보드(Phase B: `sessions_history` DB 마이그레이션, `EpicFlowView.tsx` 등)는 설계만 되어 있고 구현되지 않았으며, 이후 계획 문서(`docs/superpowers/plans/2026-06-15-github-pipeline-tracking-p3-dashboard-removal.md`)에 따라 오히려 **제거 대상**이 되었을 가능성이 있다 — 코드베이스에 대시보드 관련 잔재는 확인되지 않음(`sessions_history`/`alembic`/`EpicFlowView` 등 검색 결과 없음, 미확인 처리).

## 6. 변경 이력

| 날짜 | slug | 요약 | PR |
|---|---|---|---|
| 2026-05-29 | `epic-phase-pipeline` | Epic/Phase 분해 Phase A 구현 — 21개 테스트 통과, 커버리지 92% | 미확인 |
| 2026-07-04 | (bootstrap) | `docs/project/` 최초 생성 — 이 페이지 신설, 스냅샷(`docs/epic-phase-pipeline/`)에서 현재판 승격 | — |
