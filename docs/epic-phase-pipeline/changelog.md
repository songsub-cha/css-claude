# 변경 이력 — Epic/Phase 파이프라인

## [Phase A] 2026-05-29 — 파이프라인 메카닉스

### 동작 변경

이 변경은 CSS 파이프라인의 동작을 변경하며, 특히 **대형 아이디어**에 영향을 줍니다. 소형 아이디어(`task_count ≤ 20` AND `batch_count ≤ 4`)는 영향을 받지 않습니다.

---

### 새 Stage: `phasing`

`/css:plan`과 `/css:review` 사이에 새로운 Stage 2.5가 추가되었습니다.

**이전 동작:** plan 완료 후 바로 review로 진행

**새 동작:**
1. `should_phase(task_count, batch_count)` 평가
2. 임계치 미만(`task_count ≤ 20` AND `batch_count ≤ 4`) → "단일 세션 경로 (임계치 미만)" 공지 후 기존 흐름 유지
3. 임계치 초과 → 사용자가 `phase_manifest`를 승인하는 새 게이트 제시

**관련 파일:** `commands/phase.md` (신규), `commands/ship.md` (수정)

---

### `plan` — 2레벨 분기

**이전 동작:** 항상 완전한 TDD 단계(코드 포함)의 상세 플랜을 생성

**새 동작:** 세션 `kind`에 따라 분기

| `kind` | plan 수준 | 설명 |
|--------|-----------|------|
| `"epic"` (또는 부재) | `"skeleton"` | 코드 없는 거친 태스크 타이틀 + 배치 그룹. 파이프라인 비용 절감의 핵심 |
| `"phase"` | `"detailed"` | 이 Phase 배치만을 위한 완전한 TDD 단계 (기존 동작) |

**기록 필드:** `phases.plan.level = "skeleton" | "detailed"`

**관련 파일:** `commands/plan.md` (수정)

---

### `review` — 2레벨 분기

**이전 동작:** 항상 rich-spec dispatch (전문가 파견, RED scaffold + GREEN template) 실행

**새 동작:** 세션 `kind`에 따라 분기

| `kind` | review 수준 | 산출물 |
|--------|------------|--------|
| `"epic"` (또는 부재) | `"architecture"` | 커버리지 매트릭스 + Phase 열 + 전문가 라우팅. rich-spec 없음. `.claude/css/reviews/review-{epic}-arch-{ts}.md` |
| `"phase"` | `"rich-spec"` | 이 Phase 태스크만의 RED/GREEN 블록. `.claude/css/plans/{epic}-p{n}-T*.md` (기존 동작) |

Epic에서 전문가 파견을 차단하는 `Review_Level_Gate`가 `agents/reviewer.md:81-84`에 추가되었습니다.

**관련 파일:** `commands/review.md` (수정), `agents/reviewer.md` (수정)

---

### `execute` — Phase 범위 지정

**이전 동작:** 단일 슬러그의 플랜과 rich-spec을 전부 구현

**새 동작:**
- `kind="phase"` 세션: 워크트리 `../{repo}-css-{epic}-p{n}`, 브랜치 `css/{epic}/p{n}`, `base_branch` 기준으로 생성. 태그 `Phase: {phase_index}`가 붙은 태스크만 구현
- 레거시 단일 세션: 변경 없음 (`../{repo}-css-{slug}`, `css/{slug}`)

**새 인수:** `--phase <n>` (선택적, `kind="phase"` 세션에서는 `phase_index`로 자동 추론)

**관련 파일:** `commands/execute.md` (수정), `agents/executor.md` (수정)

---

### `verify` — Phase 기준 범위 지정

**이전 동작:** spec의 모든 인수 기준 검증

**새 동작:** `kind="phase"` 세션에서는 rich-spec 블록에 `Phase: {phase_index}` 태그가 있는 기준만 검증. 루프백 `LOOPBACK_TO_EXECUTE`는 Epic이 아닌 동일 Phase 자식 슬러그로 재진입

**관련 파일:** `commands/verify.md` (수정)

---

### `document` — Phase별 문서 경로

**이전 동작:** 항상 `docs/{slug}/README.md`에 저장

**새 동작:**

| `kind` | 출력 경로 |
|--------|-----------|
| `"phase"` | `docs/{epic}/p{phase_index}/README.md` |
| 레거시 | `docs/{slug}/README.md` (변경 없음) |

**관련 파일:** `commands/document.md` (수정)

---

### `pr` — 스택 PR 및 `--base`

**이전 동작:** 항상 `main`을 base로 PR 생성

**새 동작:**
- `--base <branch>` 인수 추가 (기본값: `main`)
- `base_branch != main`: PR 본문에 "Stacked on #N" 포함, 형제 Phase PR 상호 링크
- `gh pr create --base <base_branch>` 사용

**관련 파일:** `commands/pr.md` (수정), `agents/pr-creator.md` (수정)

---

### 잠금 및 `_active.json`

**이전 동작:** 잠금 키가 Epic 슬러그 수준. `_active.json`에 `latest_slug`만 존재

**새 동작:**
- 잠금 키: `locks/{child_slug}-{stage}.lock` (Phase 수준 — 형제 Phase 간 충돌 없음)
- `_active.json` 신규 필드: `active_epic`, `active_phase`

---

### 세션 JSON — 신규 필드

Epic 및 Phase 세션 JSON에 다음 필드가 추가되었습니다.

**Epic 세션 신규 필드:**

| 필드 | 타입 | 기본값 |
|------|------|--------|
| `kind` | `"epic"` | `"epic"` (하위 호환 기본값) |
| `phases.plan.level` | `"skeleton"` | — |
| `phases.phasing` | `object` | — |
| `phase_manifest` | `list` | — |
| `child_slugs` | `list[str]` | — |

**Phase 세션 신규 필드 (전체):**

| 필드 | 타입 |
|------|------|
| `kind` | `"phase"` |
| `parent_slug` | `str` |
| `phase_index` | `int` |
| `phase_label` | `str` |
| `depends_on` | `list[int]` |
| `base_branch` | `str` |

---

### 신규 Python 패키지: `tools/css_schema/`

| 모듈 | 역할 |
|------|------|
| `tools/css_schema/__init__.py` | 패키지 초기화 |
| `tools/css_schema/derive.py` | 순수 도출 함수: `should_phase`, `phase_slug`, `phase_branch`, `base_branch_for` |
| `tools/css_schema/schema.py` | 유효성 검사: `validate_manifest`, `validate_session`, `validate_active`, `SchemaError` |
| `tools/css_schema/test_derive.py` | derive.py 테스트 (5개) |
| `tools/css_schema/test_schema.py` | schema.py 테스트 (16개) |
| `tools/css_schema/fixtures/` | 정식 JSON 예시 3개 |

---

### 마이그레이션 안내

#### 기존 세션 (하위 호환)

`kind` 필드가 없는 기존 세션은 `kind="epic"` 단일 Phase Epic으로 처리됩니다 (결정 D9). 동작 변경 없음.

`validate_session({"slug": "old", "phases": {...}})` — 예외 없이 통과.

#### 대시보드 (Phase B에서 처리)

DB의 `sessions_history` 테이블 마이그레이션은 Phase B 범위입니다. Phase A는 파이프라인 메카닉스만 포함하며, 대시보드에 대한 영향 없음.

#### 커맨드 사용자

명시적 변경 없음. `/css:ship`, `/css:plan`, `/css:review` 등 기존 커맨드가 그대로 동작합니다. 새 `phasing` Stage와 게이트는 `task_count > 20 OR batch_count > 4`인 경우에만 나타납니다.

---

## 영향받는 파일 목록

### 신규 파일

- `commands/phase.md`
- `tools/css_schema/__init__.py`
- `tools/css_schema/derive.py`
- `tools/css_schema/schema.py`
- `tools/css_schema/test_derive.py`
- `tools/css_schema/test_schema.py`
- `tools/css_schema/fixtures/valid_manifest.json`
- `tools/css_schema/fixtures/epic_session.json`
- `tools/css_schema/fixtures/phase_session.json`

### 수정된 파일

- `commands/ship.md` — phasing Stage + per-Phase 루프
- `commands/plan.md` — 2레벨 분기
- `commands/review.md` — 2레벨 분기
- `commands/execute.md` — Phase 범위 지정 + `--phase` 인수
- `commands/verify.md` — Phase 기준 범위 지정
- `commands/document.md` — Phase별 문서 경로
- `commands/pr.md` — `--base` 인수 + 스택 PR
- `agents/reviewer.md` — `Review_Level_Gate` 추가
- `agents/executor.md` — Phase 입력 및 범위 지정
- `agents/pr-creator.md` — `base_branch` + stacked PR 본문
- `README.md` — Epic/Phase 분해 섹션 추가
