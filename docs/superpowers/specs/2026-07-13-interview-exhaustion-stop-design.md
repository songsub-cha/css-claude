# Interview 질문 종료 규칙 — 소진 기반 정지 판정 (설계)

- **날짜**: 2026-07-13
- **상태**: 승인됨 (설계 리뷰 완료)
- **범위**: `/css:interview` 단계의 질문 깊이 규칙만. 코드·스키마·다른 스테이지 변경 없음.

## 배경

`commands/interview.md`의 "Minimum questioning depth" 단락은 질문 개수를 고정한다
(feature/Epic 규모는 "typically at least 10", 작은 변경도 "never fewer than 3").
고정 개수는 대리 지표라서 양방향으로 어긋난다:

- 작은 아이디어에는 할당량을 채우기 위한 filler 질문을 유발한다.
- 큰 아이디어에는 "10개 채웠으니 충분"이라는 조기 종료 명분을 준다.

한편 이 floor가 존재했던 이유는 LLM이 질문을 덜 하고 spec으로 직행하려는
편향 때문이다. 따라서 개수를 단순히 "물어볼 게 없을 때까지"라는 서술형
선언으로 바꾸면, 소진 판정의 주체가 모델 자신이라 3~4개 만에 "더 없음"을
선언하고 끝낼 위험이 있다. 개수 규칙은 **검증 가능한 정지 조건**으로
치환해야 한다.

## 결정: 스펙 골격 기반 소진 판정 (A안)

인터뷰어는 spec 골격을 인터뷰 내내 유지하고, 골격의 각 섹션이 다음 질문을
생성하는 구조로 바꾼다. 검토한 대안: (B) 순수 서술형 소진 선언 — 조기 종료
리스크로 기각, (C) 서술형 + 최소 3개 floor 유지 — "개수 = 품질" 프록시가
약하게 재도입되어 기각.

- 스펙 골격: 목적/사용자, 범위 in/out, 동작 시나리오, 엣지 케이스, 에러 처리,
  연동·제약, 비기능 요구, 수용 기준.
- **사용자가 확인하지 않은 가정**으로 채워질 섹션이 남아 있는 한, 그 섹션이
  다음 질문을 생성한다.
- 종료 조건 두 가지를 모두 충족할 때만 인터뷰를 끝낸다:
  (a) 모든 섹션이 사용자 확인 완료이거나 명시적 N/A,
  (b) 마지막 스윕 질문("아직 다루지 않은 부분?")에서 새 항목이 나오지 않음.
- filler 질문 금지. 답이 spec을 바꿀 수 있는 질문이 남아 있는 한 정지 금지.
- 개수 기준("at least 10", "never fewer than 3")은 전면 삭제한다. 이미
  구체적인 작은 변경이면 소진 조건이 빨리 충족되어 짧게 끝나는 것이 맞다.

## 변경 내용

### 1. `commands/interview.md:39` — 단락 교체

기존 "**Minimum questioning depth**" 단락 전체를 다음으로 교체
(brainstorming 스킬에 내리는 지시문이므로 "instruct brainstorming" 프레이밍 유지):

> **Questioning depth — exhaustion over count**: instruct brainstorming to keep
> probing until the tacit knowledge behind the idea is exhausted — never until a
> question quota is met. Operational stop test: maintain a running spec outline
> (purpose/users, scope in/out, behavior scenarios, edge cases, error handling,
> integrations & constraints, non-functional needs, acceptance criteria). While
> any section would be filled by an assumption the user has not confirmed, that
> section generates the next question. End the interview only when (a) every
> section is user-confirmed or explicitly N/A, and (b) a final sweep question
> ("anything we haven't covered?") surfaces nothing new. Never pad with filler
> questions; never stop while an answer could still change the spec.

### 2. `i18n/commands/interview.ko.md:39` — 미러 번역 교체

> **질문 깊이 — 개수가 아니라 소진**: brainstorming 에게 아이디어 뒤에 숨은
> 암묵지가 소진될 때까지 계속 파고들도록 지시한다 — 질문 개수 할당량을
> 채우는 방식은 절대 아니다. 운영 가능한 정지 판정: spec 골격(목적/사용자,
> 범위 in/out, 동작 시나리오, 엣지 케이스, 에러 처리, 연동·제약, 비기능 요구,
> 수용 기준)을 인터뷰 내내 유지하면서, 사용자가 확인하지 않은 가정으로 채워질
> 섹션이 남아 있는 한 그 섹션이 다음 질문을 생성한다. (a) 모든 섹션이 사용자
> 확인 완료이거나 명시적 N/A 이고, (b) 마지막 스윕 질문("아직 다루지 않은
> 부분이 있나요?")에서 새 항목이 나오지 않을 때에만 인터뷰를 종료한다. filler
> 질문으로 채우지 않는다; 답이 spec 을 바꿀 수 있는 질문이 남아 있는 한 절대
> 멈추지 않는다.

### 3. self_check 항목 추가 (양 파일 공통, 기존 self_check 관례대로 영어)

```
- [ ] Interview ended by exhaustion: every spec-outline section user-confirmed or explicitly N/A
```

### 4. 계약 테스트 추가 — `tools/agent_registry/test_pipeline_contracts.py`

커맨드 문서의 핵심 문구를 계약 테스트로 고정하는 기존 관례를 따른다:

```python
def test_interview_questioning_is_exhaustion_based(self):
    text = read("commands/interview.md")
    self.assertIn("exhaustion over count", text)
    self.assertIn("user-confirmed or explicitly N/A", text)
    self.assertNotIn("at least 10", text)
```

## 영향 범위 확인

- "at least 10 / 최소 10" 문구는 위 두 문서에만 존재한다 (과거 plans 문서의
  "10개"는 무관한 이력이라 유지).
- 기존 계약 테스트는 interview.md에서 `kind:"epic"` 관련 문자열만 검사하며
  이 단락을 참조하지 않는다. golden spec, ship.md, architecture.md, codex
  RUNTIME도 마찬가지.

## 검증

- `tools/agent_registry/test_pipeline_contracts.py`를 unittest로 실행해 신규
  테스트 통과 및 기존 계약 무회귀 확인 (이 저장소는 pytest 부재, unittest 사용).
- 두 문서에 "at least 10"/"최소 10" 잔존 여부 grep으로 0건 확인.

## 범위 외 (보류 결정 기록)

`css-code-reviewer` 서브에이전트를 `/code-review` 스킬 호출로 대체하는 안은
2026-07-13 논의에서 **보류**되었다. 재개 시 확인할 미결 사항:

1. 서브에이전트(css-verifier) 안에서 `Skill("code-review")` 호출 가능 여부
   카나리아 — 불가하면 `/css:verify` 커맨드(메인 컨텍스트) 레벨로 리뷰를
   끌어올리는 구조 필요.
2. 출력 계약 어댑터 — loopback 판정과 gh_sync가 의존하는
   `VERDICT=ISSUES_FOUND critical=<n> ...` 최종 라인과
   `.claude/css/verifies/code-review-*.md` 아티팩트를 유지하려면 /code-review
   결과(CONFIRMED/PLAUSIBLE)를 같은 형식으로 직렬화해야 함
   (CONFIRMED → loopback 트리거, PLAUSIBLE → advisory 매핑).
3. codex 포트 분기 — Codex에는 /code-review가 없으므로 에이전트 파일 폴백
   유지 여부 결정 필요. 추가로 phase 브랜치(비-main 분기)에서 /code-review의
   diff 자동 감지 범위 검증, 파이프라인에서는 ultra 금지(low~max만) 확인.
