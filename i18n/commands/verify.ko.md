---
description: 테스트 + 커버리지 + 코드 리뷰 + 보안 리뷰 (CSS 파이프라인 5단계)
argument-hint: "[--session <name>] [--exec-log <path>]"
---

# /css:verify

태스크 명령, 전체 테스트, 커버리지, 수용 기준, 코드 품질, 보안을 독립적으로 검증한다.

## 단계

1. 인자를 파싱하고, 세션을 해석하고, loopback 예산을 강제한다: `session.retries.verify` 가 `session.config.verify.max_loopback_attempts`(기본 3) 미만이어야 하며, 아니면 `ESCALATE`. verify 락을 획득하고(`locks/{slug}-verify.lock`; 60분 경과 시 stale → 안내와 함께 교체; 다른 실행의 신선한 락 → 안내와 함께 중단) `_active.json`(`latest_slug`, `active_epic`, `active_phase`)을 갱신한다.
2. 세션 또는 parent_session 에서 spec 을 해석한다. `session.phases.review.rich_specs` 에서 실행 가능한 Rich Spec 을 해석한다; 그 필드가 없을 때만 레거시 경로 폴백을 사용한다.
3. 자식 Phase 는 `Phase: {phase_index}` 로 태그된 산출물로 범위를 한정한다. 단일 Phase 와 kind 없는 레거시 세션은 `Phase: 1` 로 취급한다.
4. worktree, 브랜치, language_profile, spec, plan, phase_index, 실행 로그(`--exec-log` 에서, 없으면 `session.phases.execute.artifact` — 그 주장된 결과를 실제 재실행 결과와 교차 검증한다), 정확한 `rich_specs` 와 함께 `css-verifier` 를 디스패치한다.
5. worktree 안에서 모든 Rich Spec 의 `GREEN command` 를 재실행한 뒤, 전체 `language_profile.test_command` 와 `coverage_command` 를 실행한다.
6. 범위 내 모든 수용 기준을 구체적인 코드와 테스트 증거에 매핑한다. `css-code-reviewer` 와 `css-security-reviewer` 를 병렬로 디스패치한다; 그들은 쓸 수 없으므로 반환된 리포트를 `.claude/css/verifies/` 아래 저장한다.
7. GREEN 명령 실패, 전체 테스트 실패, `session.config.verify.coverage_threshold`(기본 85) 미만 커버리지, 매핑되지 않은 기준, 또는 CRITICAL/HIGH 발견 사항(두 리뷰어 중 하나의 `VERDICT=ISSUES_FOUND critical=<n> high=<n> ...` 마지막 줄에서 읽음)은 재시도 한도까지 `LOOPBACK_TO_EXECUTE`(`retries.verify` 증가)를 유발하고, 그 후에는 `ESCALATE` 한다.
8. 집계 리포트, `verdict`, `phases.verify.test_summary = {tests, passed, coverage_pct}` 를 기록한다(gh_sync stage-summary 코멘트가 이를 읽는다); 락을 해제한다.

<self_check>
- [ ] 모든 태스크의 GREEN 명령이 재실행됨
- [ ] 전체 테스트와 커버리지가 worktree 에서 실행됨
- [ ] 코드 및 보안 리뷰 리포트가 존재함
- [ ] loopback 시 재시도 카운터가 갱신됨
</self_check>

$ARGUMENTS
