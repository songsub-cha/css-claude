---
description: spec 을 superpowers:writing-plans 로 구조화된 plan 으로 전환 (CSS 파이프라인 2단계)
argument-hint: "[--session <name>] [--from <spec-path>]"
---

# /css:plan

spec 을 단계별 plan 으로 변환한다. `superpowers:writing-plans` 를 감싼다(wrap).

## 단계

1. **인자 파싱**: `--session` 과 `--from` 을 추출한다.

2. **세션 해석**:
   - `--session` → `<project>/.claude/css/sessions/<slug>.json` 을 로드한다.
   - `--session` 없음 → `<project>/.claude/css/sessions/_active.json` 에서 `latest_slug` 를 읽는다.
   - 둘 다 해석되지 않으면 → 질문한다: "어떤 슬러그의 plan을 작성할까요? `/css:plan --session <name>` 또는 `--from <spec path>` 로 다시 시도해주세요." 그리고 종료한다.

3. **spec 경로 해석**:
   - `--from <path>` 가 주어지면 그것을 사용한다.
   - 그렇지 않으면 `session.phases.interview.artifact`.
   - 없으면 → 질문한다: "spec 이 아직 없습니다. `/css:interview` 를 먼저 실행하거나 `--from <path>` 로 spec 경로를 지정해주세요." 그리고 종료한다.

4. 이 슬러그에 대해 `plan` 의 **phase 락을 획득**한다.

5. **헤더 출력**: `[css:plan @ slug={slug}]`.

6. **superpowers 확인** (`/css:interview` 와 동일한 점검).

7. 세션 `kind` 로부터 **plan 레벨 결정**:
   - `kind == "epic"` (또는 없음, 레거시) → **스켈레톤 plan**: 대략적인 파일 타깃과 함께 배치로 묶인 거친(coarse) 태스크 제목. **단계별 코드는 없음**. `docs/superpowers/plans/YYYY-MM-DD-<slug>.md` 로 출력한다. `phases.plan.level = "skeleton"`, `task_count`, `batch_count` 를 기록한다.
   - `kind == "phase"` → **상세 plan**: **이 Phase 의 배치들에 대해서만**(`phase_index` 기준) 완전한 코드를 포함한 한입 크기(bite-sized) TDD 단계. `docs/superpowers/plans/{parent_slug}-p{phase_index}.md` 로 출력한다. `phases.plan.level = "detailed"` 를 기록한다.

8. **writing-plans 호출**:
   ```
   Skill("superpowers:writing-plans")
   ```
   spec 경로와 레벨을 컨텍스트로 전달한다. writing-plans 에게 다음 CSS 단계(`/css:review`)가 각 태스크에 대해 Single-Specialist Task Rule(단일 전문가 태스크 규칙)을 감사한다는 점을 상기시킨다: 모든 태스크는 정확히 하나의 도메인 전문가(또는 executor 직접 처리하는 glue)에 매핑되어야 한다. 다중 도메인 태스크는 `LOOPBACK_TO_PLAN` 을 유발한다 — 미리 분해해 두는 편이 낫다.

9. **writing-plans 완료 시**:
   - plan 파일을 찾는다.
   - 세션 갱신: `phases.plan.status = completed`, `phases.plan.artifact = <plan path>`, `phases.plan.level = <"skeleton"|"detailed">`, `phases.plan.task_count = <int>`, `phases.plan.batch_count = <int>`, `phases.plan.completed_at = <ISO>`.

10. **락 해제** 후 안내:
    "Plan 작성 완료 (level={level}): `<plan path>`. 다음 단계: `/css:review` 또는 `/css:ship --session <slug>`로 진행."

<self_check>
- [ ] Plan file exists at the path recorded in session
- [ ] session file phase status updated
- [ ] Final line contains NEXT=review or ARTIFACT=<plan path>
</self_check>

$ARGUMENTS
