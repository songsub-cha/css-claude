---
description: spec 을 superpowers:writing-plans 로 스켈레톤 Epic plan 또는 실행 가능한 상세 plan 으로 전환 (CSS 파이프라인 2단계)
argument-hint: "[--session <name>] [--from <spec-path>]"
---

# /css:plan

승인된 spec 을 스켈레톤 Epic plan 또는 실행 가능한 상세 plan 으로 변환한다.

## 단계

1. `--session` 과 `--from` 을 파싱한다; 아니면 `_active.json.latest_slug` 를 해석한다.
2. 이 순서로 spec 을 해석한다: `--from`, `session.phases.interview.artifact`, 그다음 `parent_session.phases.interview.artifact`. 아무것도 없으면 중단한다.
3. plan 락을 획득하고(`locks/{slug}-plan.lock`; 60분 경과 시 stale → 안내와 함께 교체; 다른 실행의 신선한 락 → 안내와 함께 중단), `_active.json`(`latest_slug`, `active_epic`, `active_phase`)을 갱신하고, `[css:plan @ slug={slug}]` 를 출력한다.
4. 레벨을 결정한다:
   - Multi-Phase 후보: `kind == "epic"` AND `single_phase != true` -> 거친 태스크, 배치, 대략적인 파일 타깃, `task_count`, `batch_count` 를 갖춘 스켈레톤 plan.
   - `kind == "phase"`, `single_phase == true`, 또는 kind 없는 레거시 세션 -> 정확한 파일, 완전한 코드, 의존성, 실행 가능한 검증 명령을 갖춘 상세 한입 크기(bite-sized) TDD plan.
5. 자식 Phase 의 경우 그 매니페스트 배치만 포함해 `docs/superpowers/plans/{parent_slug}-p{phase_index}.md` 에 작성한다. 그 외에는 `docs/superpowers/plans/YYYY-MM-DD-{slug}.md` 에 작성한다.
6. `superpowers:writing-plans` 를 호출한다. 모든 태스크가 하나의 전문가나 executor-직접 연결(glue)에 매핑되도록 요구한다; review 전에 다중 도메인 태스크를 분해한다.
7. status, artifact, level, task_count, batch_count, completed_at 을 기록한다. 락을 해제한다.

<self_check>
- [ ] Spec resolved directly or through parent_session
- [ ] Single-Phase and legacy sessions have detailed plans
- [ ] Plan artifact exists and session points to it
- [ ] Final line contains `NEXT=review` or `ARTIFACT=<plan path>`
</self_check>

$ARGUMENTS
