# API 레퍼런스 — Epic/Phase 파이프라인

이 문서는 `tools/css_schema/` 패키지와 `/css:phase` 커맨드가 노출하는 공개 API 계약을 정의합니다.

---

## `tools/css_schema` 패키지

### 임포트

```python
from css_schema.derive import should_phase, phase_slug, phase_branch, base_branch_for
from css_schema.schema import validate_manifest, validate_session, validate_active, SchemaError
```

테스트 실행: `python -m unittest discover -s tools -t tools -v` (tools/ 폴더에서)

---

## `css_schema.derive` — 순수 도출 함수

모든 함수는 부작용이 없는 순수 함수입니다. 파일 I/O, 네트워크, 상태 변경이 없습니다.

### `should_phase(task_count: int, batch_count: int) -> bool`

결정 D7의 임계치 게이트. Epic을 여러 Phase로 분해해야 하는지 판단합니다.

**반환값:** `True` when `task_count > 20 OR batch_count > 4`

**경계 조건:** 정확히 20/4이면 `False` — 단일 세션 경로를 유지합니다.

```python
# tools/css_schema/test_derive.py:12-15
should_phase(20, 4)   # False — 경계값
should_phase(21, 1)   # True  — task_count > 20
should_phase(5, 5)    # True  — batch_count > 4
```

---

### `phase_slug(epic_slug: str, idx: int) -> str`

Phase 세션 슬러그를 도출합니다.

**형식:** `"{epic_slug}-p{idx}"`

```python
# tools/css_schema/test_derive.py:17-18
phase_slug("epic-x", 2)   # "epic-x-p2"
```

---

### `phase_branch(epic_slug: str, idx: int) -> str`

Phase git 브랜치 이름을 도출합니다.

**형식:** `"css/{epic_slug}/p{idx}"`

```python
# tools/css_schema/test_derive.py:17-19
phase_branch("epic-x", 2)  # "css/epic-x/p2"
```

---

### `base_branch_for(manifest: list[dict], idx: int, epic_slug: str, epic_base: str = "main") -> str`

Phase가 분기해야 하는 브랜치를 도출합니다.

**매개변수:**

| 이름 | 타입 | 설명 |
|------|------|------|
| `manifest` | `list[dict]` | 유효한 phase_manifest (validate_manifest 통과) |
| `idx` | `int` | 대상 Phase의 `idx` |
| `epic_slug` | `str` | Epic 슬러그 |
| `epic_base` | `str` | 기본값 `"main"` — Epic 자체가 분기한 브랜치 |

**반환값:**
- `depends_on` 가 빈 목록 → `epic_base` 반환
- `depends_on` 에 값이 있으면 → 가장 큰 의존 idx의 브랜치 (`phase_branch(epic_slug, max(deps))`)

```python
# tools/css_schema/test_derive.py:21-28
MANIFEST = [
    {"idx": 1, "label": "foundation", "batches": [1, 2], "depends_on": []},
    {"idx": 2, "label": "api",        "batches": [3],    "depends_on": [1]},
    {"idx": 3, "label": "ui",         "batches": [4, 5], "depends_on": [2]},
]

base_branch_for(MANIFEST, 1, "epic-x")                  # "main"
base_branch_for(MANIFEST, 3, "epic-x")                  # "css/epic-x/p2"
base_branch_for(MANIFEST, 1, "epic-x", epic_base="dev") # "dev"
```

**예외:** `KeyError` — `idx`가 매니페스트에 없는 경우 (내부 방어 코드, 호출자는 validate_manifest를 먼저 통과시켜야 함)

---

## `css_schema.schema` — 유효성 검사 함수

### `class SchemaError(ValueError)`

CSS 세션/매니페스트 아티팩트가 계약을 위반할 때 발생합니다.

```python
from css_schema.schema import SchemaError

try:
    validate_manifest([])
except SchemaError as e:
    print(e)  # "phase_manifest must be a non-empty list"
```

---

### `validate_manifest(manifest: object) -> None`

`phase_manifest` 배열이 DAG 불변 조건을 만족하는지 검증합니다. 오류 시 `SchemaError` 발생.

**강제 조건:**

| 조건 | 오류 메시지 |
|------|------------|
| 비어있지 않은 목록이어야 함 | `"phase_manifest must be a non-empty list"` |
| 각 항목은 `dict`여야 함 | `"each phase must be an object"` |
| `idx`는 `int >= 1`이어야 함 | `"phase idx must be int >= 1, got ..."` |
| `idx` 중복 불가 | `"duplicate phase idx {idx}"` |
| `label`은 비어있지 않은 문자열 | `"phase {idx} needs a non-empty label"` |
| `batches`는 비어있지 않은 목록 | `"phase {idx} needs a non-empty batches list"` |
| `depends_on`은 목록이어야 함 | `"phase {idx} depends_on must be a list"` |
| `depends_on`의 값은 더 작은 idx이어야 함 (위상 순서) | `"phase {idx} depends_on {d}: must be an existing smaller idx"` |

```python
# tools/css_schema/test_schema.py:10-38

validate_manifest(VALID)          # 예외 없음

# 오류 케이스:
validate_manifest([])             # SchemaError
validate_manifest([dup, dup])     # SchemaError: duplicate idx
validate_manifest([{"batches": [], ...}])                  # SchemaError: empty batches
validate_manifest([{"idx": 1, "depends_on": [2]}, ...])   # SchemaError: forward dep
validate_manifest([{"idx": 1, "depends_on": [9]}])        # SchemaError: unknown dep
```

---

### `validate_session(obj: dict) -> None`

Epic 또는 Phase 세션 JSON을 검증합니다. 오류 시 `SchemaError` 발생.

**강제 조건:**

| 조건 | 비고 |
|------|------|
| `slug`는 비어있지 않은 문자열 | 필수 |
| `kind`는 `"epic"` 또는 `"phase"` | `kind` 부재 → `"epic"` 으로 기본값 (D9 하위 호환) |
| `phases`는 `dict` | 필수 |
| `phase_manifest`가 있으면 validate_manifest를 통과해야 함 | 선택적 |
| `kind="phase"` → `parent_slug`, `phase_index`, `base_branch` 필수 | Phase 전용 |
| `phase_index`는 `int >= 1` | Phase 전용 |
| `depends_on`이 있으면 목록이어야 함 | Phase 전용 |

```python
# tools/css_schema/test_schema.py:42-67

# Epic 세션 (유효)
validate_session({"slug": "e", "kind": "epic",
                  "phases": {"interview": {"status": "completed"}}})

# Phase 세션 (유효)
validate_session({"slug": "e-p1", "kind": "phase", "parent_slug": "e",
                  "phase_index": 1, "depends_on": [], "base_branch": "main",
                  "phases": {"execute": {"status": "pending"}}})

# 레거시 세션 — kind 없이도 유효 (D9)
validate_session({"slug": "old", "phases": {"interview": {"status": "completed"}}})

# 오류 케이스:
validate_session({"slug": "e-p1", "kind": "phase",
                  "phase_index": 1, "base_branch": "main", "phases": {}})
# SchemaError: phase session missing required field 'parent_slug'
```

---

### `validate_active(obj: dict) -> None`

`_active.json` 파일을 검증합니다. 오류 시 `SchemaError` 발생.

**강제 조건:**

| 조건 | 비고 |
|------|------|
| `latest_slug`는 비어있지 않은 문자열 | 필수 |
| `active_phase`가 있으면 `int`여야 함 | 선택적 |

```python
# tools/css_schema/test_schema.py:74-83

validate_active({"latest_slug": "e"})                                    # 유효
validate_active({"latest_slug": "e-p1", "active_epic": "e", "active_phase": 1})  # 유효
validate_active({})  # SchemaError: _active.json requires a non-empty latest_slug
```

---

## `/css:phase` 커맨드

**파일:** `commands/phase.md`

**설명:** Epic 플랜 배치를 의존성 순서가 있는 Phase로 그룹화하고, 자식 Phase 세션을 생성합니다. `/css:plan`과 `/css:review` 사이의 Stage 2.5입니다.

### 인수

| 인수 | 기본값 | 설명 |
|------|--------|------|
| `--session <name>` | `_active.json.latest_slug` | Epic 슬러그 |

### 사전 조건

- `phases.plan.status == "completed"` — plan이 먼저 완료되어야 함

### 동작

1. **Threshold gate:** `should_phase(task_count, batch_count)` 호출
   - `False` → 단일 Phase 매니페스트 자동 생성, "단일 세션 경로 (임계치 미만)" 공지, Step 7로 이동
   - `True` → 계속
2. **제안 매니페스트 제시** — `[승인 / 수정 / 취소]` 게이트
3. **validate_manifest** 실행으로 승인된 매니페스트 검증
4. **지속화:**
   - `.claude/css/plans/phase-manifest-{slug}.json` 저장
   - Epic 세션: `kind="epic"`, `phases.phasing=completed`, `phase_manifest`, `child_slugs` 업데이트
   - Phase별 자식 세션 파일 생성: `kind="phase"`, `parent_slug`, `parent_session`, `phase_index`, `phase_label`, `depends_on`, `base_branch`; 부모 interview/spec 컨텍스트 복사
5. 잠금 키: `locks/{slug}-phasing.lock` (Epic 슬러그 — phasing은 자식이 생기기 전 Epic 하나에 대해 한 번만 실행되는 단일 임계 구역)
6. "Phasing 완료: {N} Phases. NEXT=review" 공지

### 출력 아티팩트

| 파일 | 설명 |
|------|------|
| `.claude/css/plans/phase-manifest-{epic}.json` | 승인된 phase_manifest |
| `.claude/css/sessions/{epic}-p{n}.json` | 각 Phase의 자식 세션 파일 |

### 자기 점검

- `phase-manifest-{slug}.json`이 `validate_manifest`를 통과해야 함
- Epic 세션에 `phase_manifest` + `child_slugs`가 포함되어야 함
- Phase별로 `validate_session`을 통과하는 자식 세션 파일이 1개씩 있어야 함
- 최종 줄에 `NEXT=review`가 포함되어야 함

---

## 세션 JSON 계약 (전체 필드 레퍼런스)

### Epic 세션 (`kind="epic"`)

정식 예시: `tools/css_schema/fixtures/epic_session.json`

| 필드 | 타입 | 설명 |
|------|------|------|
| `slug` | `str` | Epic 식별자 |
| `kind` | `"epic"` | 세션 유형 |
| `single_phase` | `bool` | `true`면 상세 plan + rich-spec 단일 세션 경로 |
| `idea` | `str` | 원본 아이디어 |
| `phases.plan.level` | `"skeleton"` | 스켈레톤 플랜 — 코드 없음 |
| `phases.plan.task_count` | `int` | 전체 태스크 수 |
| `phases.plan.batch_count` | `int` | 전체 배치 수 |
| `phases.phasing.artifact` | `str` | phase-manifest JSON 경로 |
| `phases.review.level` | `"architecture"` | 아키텍처 review — rich-spec 없음 |
| `phases.review.rich_specs` | `list[str]` | 실행 가능한 태스크 단위 Rich Spec 경로 |
| `phases.review.advisories` | `list[str]` | 실행 대상이 아닌 architecture/security advisory 경로 |
| `phase_manifest` | `list` | Phase 설명 배열 (validate_manifest 통과) |
| `child_slugs` | `list[str]` | 자식 Phase 슬러그 목록 |

### Phase 세션 (`kind="phase"`)

정식 예시: `tools/css_schema/fixtures/phase_session.json`

| 필드 | 타입 | 설명 |
|------|------|------|
| `slug` | `str` | `{epic}-p{idx}` 형식 |
| `kind` | `"phase"` | 세션 유형 |
| `parent_slug` | `str` | Epic 슬러그 |
| `parent_session` | `str` | 부모 세션 경로; 자식 컨텍스트 fallback |
| `phase_index` | `int` | 1-기반 Phase 번호 |
| `phase_label` | `str` | 사람이 읽을 수 있는 레이블 |
| `depends_on` | `list[int]` | 이 Phase가 의존하는 phase_index 목록 |
| `base_branch` | `str` | 이 Phase가 분기하는 브랜치 |
| `phases.plan.level` | `"detailed"` | 이 Phase 배치의 완전한 TDD 단계 |
| `phases.review.level` | `"rich-spec"` | 이 Phase 태스크의 RED scaffold + GREEN template |
| `phases.review.rich_specs` | `list[str]` | 이 Phase의 실행 가능한 태스크 단위 Rich Spec 경로 |
| `phases.review.advisories` | `list[str]` | 실행 대상이 아닌 advisory 경로 |
| `phases.execute.worktree` | `str` | `../{repo}-css-{epic}-p{n}` |
| `phases.execute.branch` | `str` | `css/{epic}/p{n}` |
| `phases.document.artifact` | `str` | `docs/{epic}/p{n}/README.md` |
| `phases.pr.artifact` | `str` | PR URL |

### `_active.json`

| 필드 | 타입 | 설명 |
|------|------|------|
| `latest_slug` | `str` | 필수. 가장 최근 활성 슬러그 |
| `active_epic` | `str` | 선택. 현재 활성 Epic 슬러그 |
| `active_phase` | `int` | 선택. 현재 활성 Phase 인덱스 |
