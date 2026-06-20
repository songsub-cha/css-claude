# Epic/Phase 파이프라인 분해 (Phase A)

## 개요

CSS 파이프라인에 **Epic/Phase 분해** 기능이 추가되었습니다. 기존에는 `/css:ship`이 하나의 세션에서 전체 파이프라인을 실행했습니다. 아이디어가 작으면 괜찮지만, 대형 피처는 `plan` 단계에서 47개 태스크/7배치를 생성하고 `review` 단계에서 모든 태스크에 대해 rich-spec을 한꺼번에 생성하는 바람에 **세션 토큰이 ~1M을 초과**하고 하나의 거대한 PR로 뭉쳐집니다.

**근본 원인:** 세션이 비대해지는 이유는 `plan`(완전한 코드 포함 단계)과 `review`(태스크별 RED scaffold + GREEN template) 두 단계가 **Epic 전체 범위에서 한 번에** 실행되기 때문입니다. Phase별로 `execute`만 나누어도 `plan`과 `review`가 이미 전체 세부 내용을 펼쳐놓은 상태라면 아무런 의미가 없습니다.

**해결책:** 세부 내용 전개를 Phase로 연기합니다.

- **Epic 세션**은 저렴합니다: interview + 스켈레톤 plan + phasing + 아키텍처 review만 실행하며 코드를 생성하지 않습니다.
- **Phase 세션**은 자신의 배치만을 위한 상세 plan + rich-spec review + execute + verify + document + pr을 실행하며 독립된 PR을 생성합니다.

### 4레벨 용어

| 용어 | 의미 | 위치 |
|------|------|------|
| **Project** | 레포지터리 (등록된 워크스페이스) | `projects` 테이블 |
| **Epic** | 하나의 피처/아이디어 = Phase들의 컨테이너 | `sessions_history` `kind=epic` 행 |
| **Phase** | 배포 가능한 증분 = PR 1개 = 자식 세션 1개 | `sessions_history` `kind=phase` 행 |
| **Stage** | 세션 내부의 파이프라인 단계 (interview, plan, phasing, review, execute, verify, document, pr) | 세션 JSON의 `phases` 맵 |

> 주의: 기존 코드에서 `phase`라고 불렸던 7개의 파이프라인 단계는 이제 **Stage**라고 합니다. 새 기능에서 **Phase**는 기능 수준의 단위를 의미합니다.

---

## Quick Start

### 소형 아이디어 (변경 없음)

`task_count ≤ 20` AND `batch_count ≤ 4`인 경우 파이프라인이 기존 단일 세션 경로로 동작합니다.

```bash
/css:ship "간단한 기능 추가"
# threshold 미만 → 기존과 동일한 단일 세션, 단일 PR
```

### 대형 아이디어 (Epic/Phase 분해)

`task_count > 20` 또는 `batch_count > 4`이면 파이프라인이 자동으로 분해를 제안합니다.

```bash
/css:ship "대규모 대시보드 기능 — API + DB + UI 포함"
# → interview → plan (스켈레톤) → /css:phase (사용자 승인 게이트)
# → Epic 아키텍처 review
# → Phase p1: 상세 plan → rich-spec review → execute → verify → document → PR #a
# → Phase p2: 상세 plan → rich-spec review → execute → verify → document → PR #b (base=p1)
# → Phase p3: 상세 plan → rich-spec review → execute → verify → document → PR #c (base=p2)
```

### 수동으로 Phase 단계 실행

```bash
# Epic 세션에서 phasing 단계만 독립 실행:
/css:phase --session my-epic
```

---

## 사용 예시

### 1. Threshold gate: 분해 여부 판단

`tools/css_schema/derive.py:should_phase`가 임계치를 계산합니다.
(출처: `tools/css_schema/test_derive.py:12-15`)

```python
from css_schema.derive import should_phase

should_phase(20, 4)   # False — 경계값, 단일 세션 유지
should_phase(21, 1)   # True  — task_count > 20
should_phase(5, 5)    # True  — batch_count > 4
```

### 2. Phase 슬러그 및 브랜치 이름 도출

(출처: `tools/css_schema/test_derive.py:17-19`)

```python
from css_schema.derive import phase_slug, phase_branch

phase_slug("my-epic", 2)    # "my-epic-p2"
phase_branch("my-epic", 2)  # "css/my-epic/p2"
```

### 3. 스택 기반 브랜치 계산

독립 Phase는 Epic 베이스(보통 `main`)에서 분기하고, 의존 Phase는 이전 Phase 브랜치에 스택됩니다.
(출처: `tools/css_schema/test_derive.py:21-28`)

```python
from css_schema.derive import base_branch_for

MANIFEST = [
    {"idx": 1, "label": "foundation", "batches": [1, 2], "depends_on": []},
    {"idx": 2, "label": "api",        "batches": [3],    "depends_on": [1]},
    {"idx": 3, "label": "ui",         "batches": [4, 5], "depends_on": [2]},
]

base_branch_for(MANIFEST, 1, "my-epic")                    # "main"       (독립)
base_branch_for(MANIFEST, 3, "my-epic")                    # "css/my-epic/p2" (p2에 스택)
base_branch_for(MANIFEST, 1, "my-epic", epic_base="dev")   # "dev"        (커스텀 베이스)
```

### 4. 매니페스트 유효성 검사

(출처: `tools/css_schema/test_schema.py:11-12`)

```python
from css_schema.schema import validate_manifest, SchemaError

manifest = [
    {"idx": 1, "label": "DB + bridge foundation", "batches": [1, 2], "depends_on": []},
    {"idx": 2, "label": "API layer",              "batches": [3, 4], "depends_on": [1]},
    {"idx": 3, "label": "UI",                     "batches": [5, 6], "depends_on": [2]},
]
validate_manifest(manifest)  # 예외 없음 → 유효

validate_manifest([])                                      # SchemaError: 비어있음
validate_manifest([{"idx": 1, ...}, {"idx": 1, ...}])     # SchemaError: 중복 idx
validate_manifest([{"idx": 1, ..., "depends_on": [2]}])   # SchemaError: 순방향 의존성
```

정식 예시는 `tools/css_schema/fixtures/valid_manifest.json`을 참조합니다.

### 5. 레거시 세션 (하위 호환성)

`kind` 필드가 없는 기존 세션은 `kind="epic"` 단일 Phase Epic으로 처리됩니다.
(출처: `tools/css_schema/test_schema.py:52-54`)

```python
# kind가 없어도 유효 (D9 하위 호환)
validate_session({"slug": "old", "phases": {"interview": {"status": "completed"}}})
```

---

## 아키텍처

### 세션 흐름

```mermaid
flowchart TD
    subgraph Epic["Epic 세션 (저렴 - 코드 없음)"]
        I[interview] --> P[plan\n스켈레톤]
        P --> PH[/css:phase\n사용자 승인 게이트]
        PH --> R[review\n아키텍처만]
        R --> CS[child_slugs 생성]
    end

    CS --> P1 & P2 & P3

    subgraph P1["Phase p1 세션 (독립)"]
        P1a[plan 상세] --> P1b[review rich-spec]
        P1b --> P1c[execute]
        P1c --> P1d[verify]
        P1d --> P1e[document]
        P1e --> P1f["PR #a\nbase=main"]
    end

    subgraph P2["Phase p2 세션 (p1 의존)"]
        P2a[plan 상세] --> P2b[review rich-spec]
        P2b --> P2c[execute]
        P2c --> P2d[verify]
        P2d --> P2e[document]
        P2e --> P2f["PR #b\nbase=css/epic/p1"]
    end

    subgraph P3["Phase p3 세션 (p2 의존)"]
        P3a[plan 상세] --> P3b[review rich-spec]
        P3b --> P3c[execute]
        P3c --> P3d[verify]
        P3d --> P3e[document]
        P3e --> P3f["PR #c\nbase=css/epic/p2"]
    end

    P1f -->|"병합 후"| P2f
    P2f -->|"병합 후"| P3f
```

### 2레벨 plan + review (토큰 폭증 방지의 핵심)

| 수준 | plan | review |
|------|------|--------|
| **Multi-Phase Epic** (`kind=epic`, `single_phase=false`) | 스켈레톤: 코드 없는 거친 태스크 타이틀 + 배치 그룹 | 아키텍처 review: 커버리지 매트릭스 + Phase 열 + 전문가 라우팅. **rich-spec 없음** |
| **Single-Phase Epic** (`kind=epic`, `single_phase=true`) | 상세: 단일 세션에서 실행 가능한 완전한 TDD 단계 | 태스크별 rich-spec dispatch (`Phase: 1`) |
| **Phase** (`kind=phase`) | 상세: 이 Phase 배치만을 위한 완전한 TDD 단계 | rich-spec dispatch: 이 Phase 태스크만을 위한 RED scaffold + GREEN template |

`commands/plan.md:30-32` 및 `commands/review.md:24-26`에서 `kind`로 분기하며, `agents/reviewer.md:81-84`의 `Review_Level_Gate`가 Epic에서 specialist 파견을 차단합니다.

### 스택 PR 전략

```
main
 └─ css/<epic>/p1            → PR #a  (base: main)
     └─ css/<epic>/p2        → PR #b  (base: css/<epic>/p1)  depends_on=[1]
         └─ css/<epic>/p3    → PR #c  (base: css/<epic>/p2)  depends_on=[2]
```

- 독립 Phase (`depends_on: []`) → Epic 베이스에서 분기, `main`으로 PR
- 의존 Phase → 이전 Phase 브랜치에 스택, 전임 Phase PR에 "Stacked on #N" 표기

### 세션 JSON 구조

**Epic 세션** (`tools/css_schema/fixtures/epic_session.json`):
```json
{
  "slug": "epic-phase-pipeline",
  "kind": "epic",
  "phases": {
    "plan":    {"level": "skeleton", "task_count": 47, "batch_count": 7},
    "phasing": {"status": "completed", "artifact": "...phase-manifest-*.json"},
    "review":  {"level": "architecture", "verdict": "PASS"}
  },
  "phase_manifest": [...],
  "child_slugs": ["epic-phase-pipeline-p1", "epic-phase-pipeline-p2", "epic-phase-pipeline-p3"]
}
```

**Phase 세션** (`tools/css_schema/fixtures/phase_session.json`):
```json
{
  "slug": "epic-phase-pipeline-p2",
  "kind": "phase",
  "parent_slug": "epic-phase-pipeline",
  "parent_session": ".claude/css/sessions/epic-phase-pipeline.json",
  "phase_index": 2,
  "depends_on": [1],
  "base_branch": "css/epic-phase-pipeline/p1",
  "phases": {
    "plan":     {"level": "detailed", "task_count": 9},
    "review":   {"level": "rich-spec", "verdict": "PASS", "rich_specs": ["...-T01.md"], "advisories": []},
    "execute":  {"worktree": "../repo-css-epic-phase-pipeline-p2", "branch": "css/epic-phase-pipeline/p2"},
    "document": {"artifact": "docs/epic-phase-pipeline/p2/README.md"}
  }
}
```

### 브랜치 및 워크트리 명명 규칙

| 항목 | 패턴 | 예시 |
|------|------|------|
| Phase 슬러그 | `<epic>-p<idx>` | `my-epic-p2` |
| Phase 브랜치 | `css/<epic>/p<idx>` | `css/my-epic/p2` |
| 워크트리 경로 | `../<repo>-css-<epic>-p<idx>` | `../my-repo-css-my-epic-p2` |
| 문서 경로 | `docs/<epic>/p<idx>/README.md` | `docs/my-epic/p2/README.md` |
| exec-log 경로 | `exec-log-<epic>-p<idx>-<ts>.md` | `exec-log-my-epic-p2-20260529T1200.md` |
| 잠금 키 | `locks/<child-slug>-<stage>.lock` | `locks/my-epic-p2-execute.lock` |

### 잠금 및 `_active.json`

잠금 단위가 Epic 수준에서 Phase 수준으로 이동했습니다. 잠금 키에 자식 슬러그(`<child_slug>-<stage>.lock`)를 사용하여 형제 Phase가 서로 차단하지 않습니다.

`_active.json`은 `active_epic`과 `active_phase` 필드를 추가로 추적합니다.
(출처: `tools/css_schema/test_schema.py:77-79`)

```json
{
  "latest_slug": "my-epic-p2",
  "active_epic": "my-epic",
  "active_phase": 2
}
```

---

## 테스트

### 테스트 실행

```bash
# tools/ 폴더에서:
python -m unittest discover -s tools -t tools -v
```

**결과 (검증 완료):** 21개 테스트 전부 통과, 종료 코드 0 (verify 보고서: `verify-epic-phase-pipeline-20260529T2313.md`).

### 테스트 클래스

| 클래스 | 파일 | 테스트 수 | 검증 대상 |
|--------|------|-----------|-----------|
| `TestDerive` | `tools/css_schema/test_derive.py` | 5 | threshold gate, 슬러그/브랜치 도출, 스택 계산 |
| `TestManifest` | `tools/css_schema/test_schema.py` | 6 | 유효 매니페스트, 빈 목록, 중복 idx, 빈 배치, 순방향 의존성, 알 수 없는 의존성 |
| `TestSession` | `tools/css_schema/test_schema.py` | 6 | Epic 세션, Phase 세션, 레거시 D9, 누락된 parent, 잘못된 kind, 누락된 slug |
| `TestActiveAndFixtures` | `tools/css_schema/test_schema.py` | 4 | `_active.json` 최소 형태, epic+phase, latest_slug 필수, 픽스처 라운드트립 |

### 커버리지

| 파일 | 커버리지 | 비고 |
|------|---------|------|
| `tools/css_schema/__init__.py` | 100% | |
| `tools/css_schema/derive.py` | 94% | 미미한 방어적 KeyError 분기 |
| `tools/css_schema/schema.py` | 83% | 방어적 타입 가드 분기들 (정상) |
| **전체** | **92%** | 임계치 85% 초과 |

### 픽스처

`tools/css_schema/fixtures/` 디렉터리에는 스키마 validator에 대한 정식 예시가 포함되어 있습니다.

- `valid_manifest.json` — 3-Phase 선형 체인 매니페스트
- `epic_session.json` — `plan.level=skeleton`, `review.level=architecture`가 포함된 Epic 세션
- `phase_session.json` — `plan.level=detailed`, `base_branch=css/epic-phase-pipeline/p1`이 포함된 Phase p2 세션

---

## 향후 작업

### Phase B — 대시보드 (다음 단계)

Phase A는 파이프라인 메카닉스를 구현했습니다. Phase B는 이 스키마를 소비하는 대시보드 레이어를 추가합니다.

- `sessions_history` DB 마이그레이션: `kind`, `parent_slug`, `phase_index`, `phase_label`, `depends_on` 컬럼 (`alembic/versions/0002_phase_hierarchy.py`)
- 백엔드: `session_reader.py` Epic/Phase 그룹화, `epic_flow.py` 의존성 그래프 어셈블리, SSE 이벤트(`phase_started`, `phase_completed`, `phase_pr_opened`)
- 프론트엔드: `EpicFlowView.tsx` (Phase 노드 + 의존성 엣지 + 단계별 상태), Kanban 수영레인, `PhaseName → StageName` 이름 변경

### Epic 집계 README (미결)

현재 Document는 Phase별 `docs/<epic>/p<n>/README.md`를 생성합니다 (결정 D3). 피처 수준의 집계 README는 실제 다중 Phase 실행 후 검토하도록 연기했습니다.

### 병렬 Phase 실행

독립 Phase(`depends_on: []`)는 이론적으로 별도 세션/워크트리에서 병렬 실행이 가능합니다. `commands/ship.md`에 `MAY be dispatched`로 명시되어 있으나 오케스트레이션 자동화는 Phase B 이후 과제입니다.

### 파일 충돌 감지

병렬 Phase가 동일한 파일을 수정하면 수동 해결이 필요합니다. 아키텍처 review 단계에서 Phase 간 파일 겹침을 경고하도록 개선할 수 있습니다.
