---
description: plan 을 감사하고, 구현 전 태스크 단위 실행 가능 Rich Spec 을 생성 (CSS 파이프라인 3단계)
argument-hint: "[--session <name>] [--plan <plan-path>]"
---

# /css:review

plan 을 감사하고 구현 전에 태스크 단위 실행 가능 Rich Spec 을 생성한다.

## 단계

1. `--session` 과 `--plan` 을 파싱한다; 세션, plan, spec 을 해석한다. 자식은 `parent_session.phases.interview.artifact` 에서 spec 을 해석할 수 있다.
2. loopback 예산을 강제한다: `session.retries.review` 가 `session.config.review.max_loopback_attempts`(기본 2) 미만이어야 하며, 아니면 `ESCALATE`. review 락을 획득하고(`locks/{slug}-review.lock`; 60분 경과 시 stale → 안내와 함께 교체; 다른 실행의 신선한 락 → 안내와 함께 중단) `_active.json`(`latest_slug`, `active_epic`, `active_phase`)을 갱신한다.
   multi-Phase 후보 Epic 은 `phases.phasing.status == completed` 여야 한다; 아니면 중단하고 사용자를 `/css:phase --session <slug>` 로 안내한다.
3. review 레벨을 선택한다:
   - Multi-Phase Epic(`kind == "epic"` 이고 `single_phase != true`): 아키텍처 리뷰만, 실행 가능한 Rich Spec 없음, 리포트는 `.claude/css/reviews/review-{slug}-arch-{ts}.md`.
   - Phase, single-Phase Epic, 또는 kind 없는 레거시 세션: Rich Spec 리뷰.
4. Single-Specialist Task Rule 을 강제한다. 다중 도메인 태스크는 지배적 도메인과 `Cross_Domain_Notes` 가 명시적으로 정당화되지 않는 한 plan 으로 loopback 해야 한다.
5. Rich Spec 리뷰의 경우, 디스패치 전에 라우팅된 태스크마다 정확히 하나의 경로를 배정한다:
   - Phase: `.claude/css/plans/{parent_slug}-p{phase_index}-T{task_id}.md`
   - Single-session: `.claude/css/plans/{slug}-T{task_id}.md`
   각 전문가에게 `artifact_paths` 매핑을 전달한다. 전문가는 파일명을 절대 임의로 만들어서는 안 된다.
6. 모든 실행 가능한 태스크 산출물은 다음을 포함해야 한다:
   `## Task {id}`, `Specialist:`, `Phase: {phase_index or 1}`, `Files:`, `Verification mode: command`, `RED scaffold:`, `RED command:`, `GREEN template:`, `GREEN command:`, `Edge cases:`, `Depends-on:`, `Cross_Domain_Notes:`, 그리고 마지막 `ARTIFACT=<path>`.
7. advisory 는 별도로 디스패치한다; 이 리뷰어들은 쓸 수 없으므로 반환된 각 리포트를 `.claude/css/reviews/` 아래 저장한다:
   - `css-architect` — 모듈 경계, 새 아키텍처, 또는 대규모 리팩터.
   - `css-security-reviewer` — 인증, 권한 부여, 시크릿, 의존성, 결제, 파일 업로드, 또는 보안 민감 입력.
   advisory 경로는 실행 가능한 Rich Spec 이 아니다. CRITICAL/HIGH 보안 설계 발견 사항은 `LOOPBACK_TO_PLAN` 을 유발한다.
8. 모드별 리뷰 리포트를 작성하고 최종 판정을 파싱한다.
9. PASS 시 `phases.review.status`, `verdict`, `level`, `artifact`, 정확한 실행 가능 `rich_specs`, 별도의 `advisories`, 그리고 심각도 개수를 `phases.review.findings = {critical, high, medium, low}` 로 기록한다(gh_sync stage-summary 코멘트가 이를 읽는다). loopback 시 `retries.review` 를 증가시키고 필요한 이전 단계를 호출한다. 락을 해제한다.

<self_check>
- [ ] Multi-Phase Epic 리뷰는 실행 가능한 Rich Spec 을 생성하지 않았음
- [ ] 라우팅된 모든 태스크가 정확히 하나의 유효한 태스크 단위 산출물을 가짐
- [ ] `rich_specs` 는 실행 가능한 산출물만 포함; `advisories` 는 분리됨
- [ ] 마지막 줄에 `VERDICT=...` 포함
</self_check>

$ARGUMENTS
