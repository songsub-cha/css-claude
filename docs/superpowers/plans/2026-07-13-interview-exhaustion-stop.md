# Interview 소진 기반 종료 규칙 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `/css:interview`의 질문 개수 할당량(최소 10 / 최소 3)을 스펙 골격 기반 소진 판정으로 교체한다.

**Architecture:** 프롬프트 문서 2개(EN 원본 + ko 미러)의 해당 단락을 교체하고 self_check에 소진 항목을 추가하며, 회귀 방지용 계약 테스트 1건을 기존 `PipelineCommandContractTests`에 추가한다. 코드·스키마 변경 없음.

**Tech Stack:** Markdown 프롬프트 문서, Python `unittest` (이 레포는 pytest 부재 — `python -m unittest`로 실행).

**Spec:** `docs/superpowers/specs/2026-07-13-interview-exhaustion-stop-design.md`

## Global Constraints

- 개수 기준 문구("at least 10", "never fewer than 3", "최소 10개 이상", "최소 3개 미만은 절대 안 됨")는 전면 삭제하며 어떤 형태의 질문 개수 할당량도 재도입하지 않는다.
- `commands/interview.md`와 `i18n/commands/interview.ko.md`는 문단 단위로 1:1 미러를 유지한다 (같은 위치, 같은 의미).
- self_check 항목은 두 파일 모두 기존 관례대로 영어로 쓴다.
- 테스트는 레포 루트에서 `python -m unittest`로 실행한다 (pytest 없음).
- 이 계획 외 파일은 수정하지 않는다 (verify/ship/architecture/README/codex 무관 — 스펙의 영향 범위 확인 참조).

---

### Task 1: 소진 기반 종료 규칙 교체 (계약 테스트 + 문서 2개)

**Files:**
- Modify: `tools/agent_registry/test_pipeline_contracts.py` (44행 `test_review_requires_phasing_for_candidate_epic` 바로 앞에 메서드 삽입)
- Modify: `commands/interview.md:39` (단락 교체) 및 `commands/interview.md:51` (self_check 항목 추가)
- Modify: `i18n/commands/interview.ko.md:39` (단락 교체) 및 `i18n/commands/interview.ko.md:51` (self_check 항목 추가)

**Interfaces:**
- Consumes: `test_pipeline_contracts.py`의 기존 헬퍼 `read(rel: str) -> str` (레포 루트 기준 상대 경로로 파일을 읽음), 클래스 `PipelineCommandContractTests`.
- Produces: `commands/interview.md`에 계약 문구 `exhaustion over count`와 `user-confirmed or explicitly N/A`가 존재하고 `at least 10`이 부재함을 고정하는 테스트 `test_interview_questioning_is_exhaustion_based`.

- [ ] **Step 1: 실패하는 계약 테스트 추가**

`tools/agent_registry/test_pipeline_contracts.py`의 `PipelineCommandContractTests` 클래스 안, `test_review_requires_phasing_for_candidate_epic` 메서드(44행) 바로 앞에 다음 메서드를 삽입한다:

```python
    def test_interview_questioning_is_exhaustion_based(self):
        text = read("commands/interview.md")
        self.assertIn("exhaustion over count", text)
        self.assertIn("user-confirmed or explicitly N/A", text)
        self.assertNotIn("at least 10", text)
```

- [ ] **Step 2: 테스트 실행해 실패 확인**

Run (레포 루트에서):
```bash
python -m unittest tools.agent_registry.test_pipeline_contracts.PipelineCommandContractTests.test_interview_questioning_is_exhaustion_based -v
```
Expected: FAIL — `AssertionError: 'exhaustion over count' not found in ...` (Ran 1 test, failures=1)

- [ ] **Step 3: `commands/interview.md:39` 단락 교체**

다음 기존 단락(3칸 들여쓰기, step 5의 하위 단락)을:

```markdown
   **Minimum questioning depth**: instruct brainstorming to keep probing requirements, scope, edge cases, and design trade-offs until the idea is concrete — typically **at least 10** substantive questions for feature/Epic-scale ideas, and **never fewer than 3** even for a genuinely small, already-concrete change. Never shortcut to the spec while scope, edge cases, or trade-offs remain open.
```

다음으로 교체한다 (들여쓰기 동일하게 3칸 유지):

```markdown
   **Questioning depth — exhaustion over count**: instruct brainstorming to keep probing until the tacit knowledge behind the idea is exhausted — never until a question quota is met. Operational stop test: maintain a running spec outline (purpose/users, scope in/out, behavior scenarios, edge cases, error handling, integrations & constraints, non-functional needs, acceptance criteria). While any section would be filled by an assumption the user has not confirmed, that section generates the next question. End the interview only when (a) every section is user-confirmed or explicitly N/A, and (b) a final sweep question ("anything we haven't covered?") surfaces nothing new. Never pad with filler questions; never stop while an answer could still change the spec.
```

- [ ] **Step 4: `commands/interview.md` self_check 항목 추가**

`<self_check>` 블록(50행~) 안에서 다음 줄을:

```markdown
- [ ] Artifact written by brainstorming (spec markdown file exists)
```

다음 두 줄로 교체한다:

```markdown
- [ ] Artifact written by brainstorming (spec markdown file exists)
- [ ] Interview ended by exhaustion: every spec-outline section user-confirmed or explicitly N/A
```

- [ ] **Step 5: `i18n/commands/interview.ko.md:39` 미러 단락 교체**

다음 기존 단락을:

```markdown
   **최소 질문 깊이**: brainstorming 에게 요구사항, 범위, 엣지 케이스, 설계 트레이드오프를 아이디어가 구체화될 때까지 계속 파고들도록 지시한다 — feature/Epic 규모 아이디어는 일반적으로 **최소 10개 이상**의 실질적인 질문, 정말로 작고 이미 구체적인 변경이라도 **최소 3개 미만은 절대 안 됨**. 범위, 엣지 케이스, 트레이드오프가 열려 있는 한 spec 으로 절대 건너뛰지 않는다.
```

다음으로 교체한다 (들여쓰기 동일하게 3칸 유지):

```markdown
   **질문 깊이 — 개수가 아니라 소진**: brainstorming 에게 아이디어 뒤에 숨은 암묵지가 소진될 때까지 계속 파고들도록 지시한다 — 질문 개수 할당량을 채우는 방식은 절대 아니다. 운영 가능한 정지 판정: spec 골격(목적/사용자, 범위 in/out, 동작 시나리오, 엣지 케이스, 에러 처리, 연동·제약, 비기능 요구, 수용 기준)을 인터뷰 내내 유지하면서, 사용자가 확인하지 않은 가정으로 채워질 섹션이 남아 있는 한 그 섹션이 다음 질문을 생성한다. (a) 모든 섹션이 사용자 확인 완료이거나 명시적 N/A 이고, (b) 마지막 스윕 질문("아직 다루지 않은 부분이 있나요?")에서 새 항목이 나오지 않을 때에만 인터뷰를 종료한다. filler 질문으로 채우지 않는다; 답이 spec 을 바꿀 수 있는 질문이 남아 있는 한 절대 멈추지 않는다.
```

그리고 같은 파일의 `<self_check>` 블록에서 Step 4와 동일한 교체를 수행한다 (ko 파일의 self_check도 영어이며 텍스트가 EN 파일과 동일함):

```markdown
- [ ] Artifact written by brainstorming (spec markdown file exists)
- [ ] Interview ended by exhaustion: every spec-outline section user-confirmed or explicitly N/A
```

- [ ] **Step 6: 테스트 통과 및 무회귀 확인**

Run (레포 루트에서):
```bash
python -m unittest tools.agent_registry.test_pipeline_contracts -v
```
Expected: `Ran 19 tests ... OK` (기존 18개 + 신규 1개, 실패 0)

Run (개수 문구 잔존 검사):
```bash
grep -rn "at least 10\|최소 10\|never fewer than 3\|최소 3개" commands/ i18n/
```
Expected: 출력 없음 (exit code 1)

- [ ] **Step 7: 커밋**

```bash
git add tools/agent_registry/test_pipeline_contracts.py commands/interview.md i18n/commands/interview.ko.md
git commit -m "feat(interview): replace question quota with exhaustion-based stop rule"
```
