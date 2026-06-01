> [English](2026-05-29-epic-phase-pipeline-design.md) · **한국어**

# CSS 파이프라인 — Epic / Phase 분해 설계 Spec

## 메타데이터

| 항목 | 값 |
|-------|-------|
| Slug | `epic-phase-pipeline` |
| 날짜 | 2026-05-29 |
| 작성자 | brainstorming 세션 (sub1904) |
| 상태 | Draft — 사용자 검토 대기 |
| 영향 범위 | CSS 파이프라인 (`commands/`, `agents/`, 세션 스키마) + 대시보드 (`dashboard/`) |
| 대체 | n/a (`2026-05-28-pipeline-dashboard-design.md`를 확장) |

## 개요

### 문제

`/css:ship`은 전체 파이프라인(interview → plan → review → execute → verify → document → pr)을 **하나의 세션 = 하나의 브랜치 = 하나의 PR**로 실행합니다. 대규모 아이디어의 경우 plan이 폭발하고(대시보드 실행에서는 47개 태스크 / 7개 배치가 생성됨), execute가 모든 배치를 단일 세션에서 처리합니다. 그 결과 ~1M 토큰 세션과 51개 커밋짜리 메가 PR이 만들어져 리뷰도, 대시보드 추적도 어려워집니다.

**토큰 폭발의 근본 원인:** *완전 상세*까지 펼쳐지는 두 단계 — `plan`(완전한 코드를 포함한 잘게 쪼갠 스텝)과 `review`(rich-spec: 태스크별 RED scaffold + GREEN 템플릿) — 가 모두 **Epic 범위**에서 실행됩니다. `execute`만 Phase 단위로 분할해도 `plan`과 `review`가 여전히 Epic 전체의 상세를 미리 구체화한다면 도움이 되지 않습니다. 해결책은 빌드뿐 아니라 상세 전개 자체를 지연시켜야 합니다.

사용자의 핵심 니즈는 **관측 가능성(observability)** 입니다. 대규모 기능의 작업 흐름을 대시보드 상에서 개별적이고 추적 가능한 단위로 보는 것입니다. 단위별 PR은 그 목적을 위한 수단입니다.

### 목표

1. 대규모 아이디어를 각자 자기 PR로 출하되고 대시보드에서 자기 추적 단위로 나타나는 **Phase**로 분해합니다.
2. **Epic 세션을 저렴하게 유지**: Epic 범위에서는 interview, *스켈레톤* plan, phasing, *아키텍처* review만 실행합니다. 비싼 완전-상세 단계 — *상세* plan과 *rich-spec* review — 와 모든 빌드 단계는 Phase 단위로 실행됩니다.
3. **의존성 순서대로의** Phase 실행과, 독립적인 Phase의 **병렬** 실행(별도 세션/워크트리)을 지원합니다.
4. 대시보드에 **Epic → Phase 흐름 뷰**(노드 + 의존성 엣지 + Phase별 Stage/PR 상태)를 제공합니다.
5. 소규모 아이디어는 **기존 단일 세션 경로**를 유지합니다(불필요한 절차 강제 없음).

### 비목표 (v0.1)

- 사람 승인 없이 Phase 경계를 자동 감지하는 것(phasing은 사용자 승인 방식).
- 저장소를 넘나드는 Epic(Epic은 하나의 저장소 안에 존재).
- 스택된 Phase 브랜치 간 자동 충돌 해소.
- phasing 게이트를 거치지 않고 Phase를 도중에 재계획하는 것.

## 용어 (이름 충돌 해소)

대시보드는 이미 7개 파이프라인 단계를 "phase"로, 저장소를 "project"로 부르고 있습니다. 우리는 **4단계 어휘**를 채택하고 그에 맞춰 이름을 변경합니다:

| 용어 | 의미 | 기존 명칭 | 위치 |
|------|---------|-----------|----------|
| **Project** | 저장소(등록된 워크스페이스) | `projects` 테이블 (변경 없음) | `projects` 테이블 |
| **Epic** | 하나의 기능/아이디어 = Phase의 컨테이너 | *(신규)* | `kind=epic`으로 태깅된 `sessions_history` 행 |
| **Phase** | 출하 가능한 증분 = PR 1개 = 자식 세션 1개 | *(신규)* | `kind=phase`로 태깅된 `sessions_history` 행 |
| **Stage** | 세션 내 파이프라인 스텝(interview, plan, phasing, review, execute, verify, document, pr); `plan`/`review`는 Epic(개략) 범위와 Phase(상세) 범위 양쪽에서 실행되고, `phasing`은 신규 | 현재 코드에서 **"phase"** | 세션 JSON 안의 `phases` 맵 |

**필요한 이름 변경:** 대시보드에서 현재 `phase`/`PhaseName`/`currentPhase`(= 7개 스텝)로 불리는 타입/필드/컬럼을 **`stage`/`StageName`/`currentStage`** 로 변경합니다. 새 기능 수준 단위가 **Phase**라는 이름을 가져갑니다.

## 결정 요약

| # | 결정 | 선택 |
|---|----------|--------|
| D1 | 어휘 | Project / Epic / Phase / Stage (4단계) — **확정** |
| D2 | DB 형태 | `sessions_history`에 컬럼 추가, **별도 `epics` 테이블 없음** — **확정** |
| D3 | document 단계 | **Phase별** 문서(Epic 수준 집계 README는 선택, 보류) — **확정** |
| D4 | Plan 세분도(2단계) | Epic은 **스켈레톤 plan**(배치로 묶인 개략 태스크, *완전 코드 없음*) 실행; 각 Phase는 자기 세션에서 **상세 잘게-쪼갠 plan** 실행 |
| D5 | 빌드 단계 실행 위치 | 상세-plan / rich-spec-review / execute / verify / document / pr 는 **Phase별(자식 세션)** |
| D6 | 브랜치/PR 전략 | Phase당 PR 1개; 의존 Phase는 **스택 브랜치**(`--base <이전 phase 브랜치>`) 사용; 독립 Phase는 Epic base에서 분기 |
| D7 | phasing 발동 조건 | `task_count > 20` OR `batch_count > 4`일 때만; 그 외에는 레거시 단일 세션 경로 |
| D8 | Review 세분도(2단계) | Epic은 **아키텍처/커버리지 review**(스켈레톤 vs spec + 개략 Single-Specialist 라우팅) 실행; **rich-spec(RED/GREEN)은 Phase 세션에서 Phase별로 작성** |
| D9 | 하위 호환 | `kind`가 없는 기존 세션은 단일 Phase Epic으로 렌더링 |
| D10 | 상세를 Phase로 지연(비용) | 완전-상세 전개(상세 plan + rich-spec)는 **Phase별** 실행, Epic 범위에서는 절대 실행 안 함 — ~1M 토큰 폭발의 핵심 해결책 |

## 아키텍처

### Epic / Phase 세션 모델

```
Epic session  (kind=epic, slug=<epic>)  — 저렴: 완전-상세 전개 없음
├─ Stage: interview       → spec
├─ Stage: plan (skeleton) → 배치로 묶인 개략 태스크 (코드 없음)
├─ Stage: phasing         → phase_manifest (신규)        ← 사용자 승인 게이트
├─ Stage: review (arch)   → 아키텍처/커버리지 감사 + 개략 전문가 라우팅
└─ child_slugs: [<epic>-p1, <epic>-p2, ...]

Phase session (kind=phase, slug=<epic>-p1, parent_slug=<epic>, depends_on=[])
├─ Stage: plan (detailed) → 이 Phase의 배치에 대한 잘게-쪼갠 완전-코드 plan
├─ Stage: review (rich)   → 이 Phase에 한정한 rich-spec (RED/GREEN)
├─ Stage: execute         → 워크트리 css/<epic>/p1, 커밋
├─ Stage: verify          → 이 Phase의 테스트/커버리지/리뷰
├─ Stage: document        → docs/<epic>/p1/...
└─ Stage: pr              → PR (base = epic base 또는 이전 phase 브랜치)
```

- **Epic 세션**은 interview, *스켈레톤* plan, phasing, *아키텍처* review를 소유합니다. 완전 상세를 전개하지도, 빌드하지도 않습니다.
- **Phase 세션**은 *상세* plan → *rich-spec* review → execute → verify → document → pr 를 소유하며, 모두 이 Phase의 배치로 범위가 한정됩니다. 부모로부터 spec + 스켈레톤 plan + `phase_manifest`를 상속하고(캐시 우선), 그다음 자기 슬라이스에 대해서만 상세를 전개합니다.
- Phase의 `depends_on`은 스택되는 `phase_index` 목록을 나열합니다. 위상 정렬 순서 = 실행 순서. `depends_on`이 서로 겹치지 않고 공유 파일이 없는 Phase는 병렬 실행 가능합니다.

### Epic에서는 개략 설계, Phase별로 상세 전개하는 데이터 흐름

```
interview ────┐
plan(skeleton)┤ (Epic, 한 번 — 저렴, 코드 없음)
phasing ──────┤  → phase_manifest: [{idx, label, batches:[...], depends_on:[...]}]
review(arch) ─┘  → 아키텍처/커버리지 감사 (개략 전문가 라우팅)
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                     ▼
   Phase p1 session     Phase p2 session      Phase p3 session
   plan(detail)→        plan(detail)→          plan(detail)→
   review(rich)→        review(rich)→          review(rich)→
   execute→verify→      execute→verify→        execute→verify→
   document→pr (PR#a)   document→pr (PR#b)      document→pr (PR#c)
   base=epic-base       base=p1 (의존 시)       base=p2 (의존 시)
```

### 왜 상세를 Phase로 지연하는가

~1M 토큰 폭발은 Epic 전체의 **상세** — `plan`의 완전-코드 스텝과 `review`의 rich-spec(태스크별 RED/GREEN) — 를 미리 구체화한 데서 비롯됐습니다. 둘 다 Phase별 세션으로 지연하면 각 세션의 작업 집합이 하나의 Phase 슬라이스로 제한됩니다. Epic 범위에 남는 것은 **개략적이고 일관성에 결정적인** 작업뿐입니다 — spec 하나, 스켈레톤 plan 하나, phasing 결정 하나, 아키텍처 review 하나(Phase끼리 서로 모순되지 않도록). 상세 plan + rich-spec은 그다음 각 Phase 세션 안에서 작성되며, Epic의 스켈레톤 + manifest로 캐시 공급됩니다.

## 세션 JSON 스키마 변경

### Epic 세션 (신규 `kind`)

```jsonc
{
  "slug": "epic-phase-pipeline",
  "kind": "epic",                       // 신규
  "idea": "...",
  "master_flow": true,
  "phases": {                           // = Epic 범위 Stage: interview / plan(skeleton) / phasing / review(arch)
    "interview": { "status": "completed", "artifact": "..." },
    "plan":      { "status": "completed", "level": "skeleton", "artifact": "...", "task_count": 47, "batch_count": 7 },
    "phasing":   { "status": "completed", "artifact": ".../phase-manifest-<epic>.json" }, // 신규 stage
    "review":    { "status": "completed", "level": "architecture", "verdict": "PASS" } // Epic에서는 rich-spec 없음
  },
  "phase_manifest": [                   // 신규
    { "idx": 1, "label": "DB + bridge foundation", "batches": [1,2], "depends_on": [] },
    { "idx": 2, "label": "API layer",              "batches": [3,4], "depends_on": [1] },
    { "idx": 3, "label": "UI",                     "batches": [5,6], "depends_on": [2] }
  ],
  "child_slugs": ["epic-phase-pipeline-p1", "epic-phase-pipeline-p2", "epic-phase-pipeline-p3"] // 신규
}
```

### Phase(자식) 세션 (신규 `kind`)

```jsonc
{
  "slug": "epic-phase-pipeline-p1",
  "kind": "phase",                      // 신규
  "parent_slug": "epic-phase-pipeline", // 신규
  "phase_index": 1,                     // 신규
  "phase_label": "DB + bridge foundation", // 신규
  "depends_on": [],                     // 신규 (phase_index 목록)
  "base_branch": "main",                // 신규: 이 Phase가 분기하는 브랜치.
                                        // depends_on=[] → ship이 시작된 브랜치(예: main);
                                        // depends_on=[k] → css/<epic>/p<k> (스택)
  "phases": {                           // = Phase 범위 Stage: plan(detail) / review(rich) / execute / verify / document / pr
    "plan":     { "status": "...", "level": "detailed", "artifact": "docs/superpowers/plans/<epic>-p1.md", "task_count": 13 },
    "review":   { "status": "...", "level": "rich-spec", "verdict": "...", "rich_specs": [".claude/css/plans/<epic>-p1-T*.md"] },
    "execute":  { "status": "...", "worktree": "../<repo>-css-<epic>-p1", "branch": "css/<epic>/p1" },
    "verify":   { "status": "...", "verdict": "..." },
    "document": { "status": "...", "artifact": "docs/<epic>/p1/README.md" },
    "pr":       { "status": "...", "artifact": "<PR URL>" }
  }
}
```

- `_active.json`에 `latest_slug`와 함께 `active_epic`, `active_phase`가 추가됩니다.
- 하위 호환: 레거시 세션(`kind` 없음)은 암묵적 단일 Phase를 가진 `kind=epic`으로 취급됩니다.

## CSS 파이프라인 커맨드 수정

### `commands/plan.md` (2단계)

- 세션 `kind`에서 수준을 감지: **Epic**(`kind=epic`) → **스켈레톤 plan**(배치로 묶인 개략 태스크 제목 + 대략적 파일 타깃, *스텝별 코드 없음* — phasing이 소비하는 저렴한 산출물) 생성. **Phase**(`kind=phase`) → 그 Phase의 배치로만 범위가 한정된 **상세 잘게-쪼갠 plan**(스텝별 완전 코드) 생성, `docs/superpowers/plans/<epic>-p<n>.md`에 기록.
- `phases.plan.level = "skeleton" | "detailed"` 기록.

### 신규 `commands/phase.md` (phasing 단계)

- 입력: Epic 세션의 plan + 배치.
- 배치를 `depends_on` 엣지를 가진 Phase로 묶고, 제안된 `phase_manifest`를 제시하며 승인을 요청합니다(**신규 게이트**).
- 발동 가드: `task_count > 20 OR batch_count > 4`일 때만 실행. 임계치 미만 → 단일 Phase manifest를 자동 작성하고 진행(레거시 동작).
- 출력: `.claude/css/plans/phase-manifest-<epic>.json`; Epic 세션의 `phases.phasing` + `phase_manifest` + `child_slugs` 갱신.

### `commands/ship.md` (오케스트레이터 재작업)

- Epic 수준(한 번): interview → plan(skeleton) → phasing. 멀티 Phase인 경우:
  1. Epic **아키텍처 review**(개략 라우팅, **rich-spec 없음**) 실행.
  2. `phase_manifest`에서 자식 Phase 세션 생성.
  3. Phase를 위상 정렬 순서로 순회. 각 자식: plan(detailed) → review(rich-spec) → execute → verify → document → pr(자기 PR).
  4. Gate 2(실행 전)와 Gate 3(pr 전)이 **Phase별**이 됨(대시보드에서 일괄 승인 옵션).
  5. 독립 Phase는 병렬 실행을 위해 별도 세션/워크트리로 dispatch될 수 있음.
- 단일 Phase Epic은 현재의 선형 흐름을 유지(스켈레톤 + 상세가 하나의 plan/review 패스로 합쳐짐).

### `commands/review.md` + `agents/reviewer.md` (2단계)

- **Epic 수준**(`kind=epic`): **아키텍처/커버리지 review** — 스켈레톤 plan을 spec과 대조 감사하고, **Phase 컬럼**을 가진 커버리지 매트릭스를 구성(모든 스켈레톤 태스크에 `phase_manifest`의 `phase_index` 태깅)하며, Phase별 **개략** Single-Specialist 라우팅을 결정. **여기서는 rich-spec을 생성하지 않음.**
- **Phase 수준**(`kind=phase`): 기존 rich-spec dispatch — 전문가가 **이 Phase의 태스크에 대해서만** 태스크별 RED scaffold + GREEN 템플릿을 작성, `.claude/css/plans/<epic>-p<n>-T*.md`에 기록. 이것이 `/css:execute`가 읽는 캐시.

### `commands/execute.md` + `agents/executor.md`

- 신규 인자 `--phase <n>`(또는 자식 slug에 직접 동작).
- **Phase의 상세 plan**(`phases.plan.artifact`)과 **Phase의 rich-spec**(그 Phase 자체의 `review` 단계가 생성 — Epic이 아님)을 읽음.
- 워크트리 `../<repo>-css-<epic>-p<n>`, 브랜치 `css/<epic>/p<n>`, `base_branch`에서 생성.
- rich-spec 준비 점검은 Phase의 태스크로 필터링.
- exec-log는 Phase별 키.

### `commands/verify.md` / `commands/document.md`

- Phase의 워크트리/브랜치에서 동작.
- verify는 이 Phase에 할당된 인수 기준만 매핑.
- document는 `docs/<epic>/p<n>/` 기록(Phase별, D3). 선택적 Epic 집계 README는 보류.

### `commands/pr.md` + `agents/pr-creator.md`

- Phase별 PR. 신규 `--base <branch>`: 의존 Phase PR은 이전 Phase 브랜치를 타깃(**스택 PR**); 독립 Phase는 Epic base 타깃.
- PR 본문은 Epic spec 링크, 이 Phase의 인수 기준 나열, `Stacked on #<N>` 표기 및 형제 Phase PR 상호 링크.

### Locking / `_active.json`

- 락 단위가 slug별에서 **Phase별**로 이동하여 형제 Phase가 서로를 막지 않음.
- `_active.json`은 `active_epic` + `active_phase` 추적.

### 브랜치 & PR 전략 (스택)

```
main
 └─ css/<epic>/p1            → PR #a  (base: main/epic-base)
     └─ css/<epic>/p2        → PR #b  (base: css/<epic>/p1)   depends_on [1]
         └─ css/<epic>/p3    → PR #c  (base: css/<epic>/p2)   depends_on [2]
```

병합 순서는 스택을 따릅니다. 독립 Phase(`depends_on: []`)는 Epic base에서 분기하고 `main`에 직접 PR을 엽니다.

## 대시보드 데이터 모델 (PostgreSQL)

D2에 따라 **`sessions_history`를 확장**합니다(마이그레이션 `alembic/versions/0002_phase_hierarchy.py`):

| 컬럼 | 타입 | 비고 |
|--------|------|-------|
| `kind` | `text` | `'epic' \| 'phase'`; 백필 시 기본값 `'epic'`(레거시 행) |
| `parent_slug` | `text NULL` | 프로젝트 내 slug 기준 자기 참조 |
| `phase_index` | `integer NULL` | 1-기반; epic은 null |
| `phase_label` | `text NULL` | 사람용 라벨 |
| `depends_on` | `jsonb` 기본값 `[]` | phase_index 목록 |

- `CHECK (kind IN ('epic','phase'))`와 `(project_id, parent_slug)` 인덱스 추가.
- `ParsedSession`(라이브 리더)도 동일 필드를 가짐; 라이브 세션은 `parent_slug`로 그룹화.
- 레거시 행은 `kind='epic'`, `parent_slug=NULL`로 백필 → 단일 Phase Epic으로 렌더링(D9).

## 대시보드 백엔드 변경

| 파일 | 변경 |
|------|--------|
| `services/session_reader.py` | `kind`, `parent_slug`, `phase_index`, `phase_label`, `depends_on` 파싱; 자식을 부모 아래로 그룹화 |
| `services/`(신규) `epic_flow.py` | Epic → Phase 그래프 조립: 노드(Phase + 현재 Stage + PR 상태) + 의존성 엣지 |
| `routers/sessions.py` | 계층형(Epic + 자식 Phase) 또는 부모 참조를 포함한 평면형 반환 |
| `routers/projects.py` | 프로젝트별 Epic 그룹화 엔드포인트 |
| `sse.py` / `routers/sse_router.py` | 신규 이벤트: `phase_started`, `phase_completed`, `phase_pr_opened` |
| `bridge.py` | 최소 변경: 큐 이벤트 `command`/`session_id`가 Phase slug를 전달; 구조 변경 없음 |

## 대시보드 프론트엔드 변경

| 파일 | 변경 |
|------|--------|
| `types.ts` | `PhaseName`→`StageName`, `currentPhase`→`currentStage` 이름 변경. `Phase`, `EpicFlow` 타입 추가; `Session`에 `kind`, `parentSlug`, `phaseIndex`, `dependsOn` 추가. 신규 SSE 변형 |
| `components/KanbanBoard.tsx` | 카드를 **Epic 스윔레인**으로 그룹화; 카드 = Phase. **컬럼 모델 재작업 필요**(Phase B): Epic은 interview/plan/phasing/review 순회; Phase는 plan/review/execute/verify/document/pr 순회 — `phasing`은 신규 컬럼이고 `plan`/`review`는 이제 두 범위에서 나타남. 정확한 컬럼 집합은 Phase B에서 확정 |
| `components/`(신규) `EpicFlowView.tsx` | **핵심 산출물**: Phase 노드 + 의존성 엣지 + Phase별 Stage/PR 상태("작업 흐름" 뷰) |
| `components/SessionCard.tsx` | phase 라벨/인덱스, PR 링크, `stacked on` 표시 |
| `stores/sessionsStore.ts`, `projectsStore.ts` | `parentSlug`로 그룹화; Phase 그래프 도출 |
| `components/HistoryView.tsx` | 아카이브된 세션을 Epic으로 그룹화 |
| `components/DetailSlideOver.tsx` | Phase 의존성, 형제 Phase, 스택 PR 체인 표시 |

## 데이터 흐름 (엔드투엔드)

1. `/css:ship "<대규모 아이디어>"` → Epic 세션 생성.
2. interview → plan **(스켈레톤: 47개 개략 태스크 / 7개 배치, 코드 없음)**.
3. phasing → 사용자가 의존성을 가진 3개 Phase 승인 → `phase_manifest` + 3개 자식 세션 기록.
4. review **(Epic, 아키텍처)** → 커버리지 매트릭스가 각 스켈레톤 태스크에 Phase 태깅; 개략 전문가 라우팅. **아직 rich-spec 없음.**
5. Phase별(위상 정렬): plan **(상세, 이 Phase만)** → review **(rich-spec, 이 Phase만)** → execute(자기 워크트리/브랜치) → verify → document(`docs/<epic>/p<n>`) → pr(스택).
6. 각 세션 JSON 기록은 대시보드 watcher가 감지 → SSE → Epic Flow 뷰 라이브 갱신; 각 Phase는 현재 Stage와 PR을 표시.

## 에러 처리

- **phasing이 사용자에게 거부됨** → plan으로 루프백하거나 manifest 편집; 승인 전까지 자식 미생성.
- **Phase verify 실패** → 그 Phase 내부에서 루프(기존 `retry_counters.verify`), 독립적인 형제 Phase를 막지 않음.
- **스택 base가 아직 미병합** → PR이 선행 브랜치를 타깃으로 열림; "미병합 #N에 의존" 경고 기록.
- **병렬 파일 충돌** → 자동 해소는 범위 밖(비목표); phasing이 같은 파일을 병렬 Phase에 할당하지 않도록 해야 함(reviewer가 중복 표시).
- **손상/부분 자식 세션** → `parse_session_file`이 이미 None을 반환하고 로깅; Epic은 사용 가능한 Phase로 계속 렌더링.

## 테스트 전략

- **파이프라인**: phasing 발동 임계치, manifest 생성, 위상 정렬, slug/브랜치 도출을 단위 테스트. 픽스처: 20개 초과 태스크의 plan이 의존성 체인을 가진 3-Phase manifest를 생성.
- **스키마**: `0002`의 up/down 마이그레이션 테스트; 백필 정확성(레거시 → 단일 Phase Epic).
- **백엔드**: `session_reader` 그룹화; `epic_flow` 그래프 조립(엣지가 `depends_on`과 일치); 신규 이벤트의 SSE 방출.
- **프론트엔드**: `EpicFlowView`가 모킹된 Epic으로부터 노드/엣지 렌더링; 스윔레인 그룹화; `kind` 없는 레거시 세션의 하위 호환 렌더링.
- **E2E(보류, 대시보드 v0.1과 동일)**: 멀티 Phase Epic의 전체 ship.

## 인수 기준

1. `task_count > 20`인 `/css:ship`은 Epic 세션 + 사용자 승인 `phase_manifest` + N개 자식 Phase 세션을 생성한다.
2. 각 Phase는 자기 워크트리, 브랜치 `css/<epic>/p<n>`, PR을 생성한다; 의존 Phase는 `--base`로 스택된다.
3. Epic 범위에서 interview + 스켈레톤-plan + phasing + 아키텍처-review가 정확히 한 번 실행되며 완전-코드 plan과 rich-spec을 **생성하지 않는다**. Phase 범위에서 상세-plan + rich-spec-review + execute + verify + document + pr가 Phase당 한 번 실행된다.
4. document가 Phase별로 `docs/<epic>/p<n>/`를 기록한다.
5. `sessions_history`가 `kind/parent_slug/phase_index/phase_label/depends_on`을 가진다; 마이그레이션이 레거시 행을 단일 Phase Epic으로 백필하며 UI가 깨지지 않는다.
6. 대시보드가 의존성 엣지와 Phase별 Stage/PR 상태를 가진 Epic → Phase 흐름 뷰를 SSE로 라이브 갱신하며 표시한다.
7. 소규모 아이디어(`task_count ≤ 20`)는 여전히 단일 세션 경로로 변경 없이 출하된다.
8. **비용 격리**: Epic 세션 산출물에는 어떤 Phase의 상세 plan이나 rich-spec도 없다; Phase 세션의 작업 집합은 자기 슬라이스(스켈레톤 + manifest + 자기 상세)로 제한된다.

## 빌드 순서 / 분해 노트

이 설계 자체가 두 개의 빌드 Phase로 깔끔하게 분해됩니다(도그푸딩):

- **Phase A — 파이프라인**: 스키마, `commands/phase.md`, **2단계 `plan` + `review`**(Epic에서 스켈레톤/아키텍처; Phase에서 상세/rich-spec), ship 오케스트레이션, execute/verify/document/pr + 에이전트, locking. (새 세션 JSON 형태를 생성.)
- **Phase B — 대시보드**: 마이그레이션 `0002`, 백엔드 reader/flow/routers/SSE, 프론트엔드 이름 변경 + `EpicFlowView` + 스윔레인. (새 형태를 소비; Phase A에 의존.)

`writing-plans`는 이 경계를 따라 분할해야 합니다.

## 리스크 & 미해결 질문

- **스택 PR 마찰**: 리뷰 후 하위 Phase를 리베이스하면 스택이 churn됨. 완화책: Phase를 작게 유지; 병합 순서 문서화.
- **phasing 품질**: 나쁜 Phase 경계(교차 의존성)는 이점을 줄임. 완화책: reviewer가 병렬 Phase 간 파일 중복 표시.
- **대시보드 이름 변경 영향 범위**: `phase→stage` 이름 변경이 많은 파일에 영향; Phase B의 기계적 첫 커밋으로 처리.
- **미해결**: Epic이 마지막에 집계 README를 받아야 하는가(현재 D3에서 보류)? 첫 실제 멀티 Phase 실행 후 재검토.

## 참고

- `2026-05-28-pipeline-dashboard-design.md` (대시보드 v0.1)
- `commands/*.md`, `agents/css/*.md`
- `dashboard/backend/models.py`, `dashboard/frontend/src/types.ts`
