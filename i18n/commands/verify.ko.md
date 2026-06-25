---
description: 테스트 + 커버리지 + 코드 리뷰 + 보안 리뷰 (CSS 파이프라인 5단계)
argument-hint: "[--session <name>] [--exec-log <path>]"
---

# /css:verify

테스트 스위트, 커버리지, 기준(criteria) 매핑, 코드 품질 리뷰, 보안 리뷰를 실행하고 하나의 판정(verdict)으로 병합한다. `css-verifier` 를 감싼다(wrap).

## 단계

1. **인자 파싱**: `--session`, `--exec-log`.

2. **세션 해석**.

3. **재시도 카운터**: `session.retry_counters.verify >= 3` 이면 옵션과 함께 사용자에게 에스컬레이션한다.

4. `verify` 의 **락 획득**. 락 키 = `locks/{slug}-verify.lock` (`kind:"phase"` 인 경우 `slug` 는 자식 슬러그 — 형제 Phase 마다 구분됨). `_active.json` 을 `active_epic` 과 `active_phase` 로 갱신한다.

5. **헤더 출력**: `[css:verify @ slug={slug}, attempt={n+1}/3]`.

6. **verify 범위 결정**:
   - `kind:"phase"` 세션 → rich-spec 블록에서 `Phase: {phase_index}` 로 태그된 기준으로 범위를 한정한다. worktree 와 branch 는 Phase 세션에서 가져온다(`phases.execute.worktree`, `phases.execute.branch`).
   - 레거시 단일 Phase 세션 → 전체 기준 집합(기존 동작).

7. **verifier 디스패치**:

   ```
   Task(
     subagent_type="css-verifier",
     description="css verify: {slug}",
     prompt="""
     <inputs>
     worktree: {session.phases.execute.worktree}
     branch: {session.phases.execute.branch}
     language_profile: {profile}
     spec: {session.phases.interview.artifact}
     plan: {session.phases.plan.artifact}
     phase_index: {phase_index or null}
     </inputs>
     <task>
     Run tests + coverage in the worktree using language_profile commands; map every acceptance criterion in the spec (scoped to phase_index when set — criteria whose rich-spec block carries Phase: {phase_index}) to concrete code/test evidence (file:line citations); dispatch css-code-reviewer and css-security-reviewer in parallel via Task; merge findings; decide verdict. Any CRITICAL or HIGH from either reviewer, OR tests fail, OR coverage < threshold, OR criterion unmapped → LOOPBACK_TO_EXECUTE (if attempts < 3) else ESCALATE.
     </task>
     <output_contract>
     Write aggregate report to: <project>/.claude/css/verifies/verify-{slug}-{ts}.md
     Sections: Verdict, Test Summary, Coverage Table, Acceptance Criteria Matrix, Code-quality Findings (link), Security Findings (link), Loopback Recommendation, Retry Counter.
     Final line: VERDICT=PASS | VERDICT=LOOPBACK_TO_EXECUTE | VERDICT=ESCALATE
     </output_contract>
     """
   )
   ```

8. **판정 파싱**:
   - `PASS` → 다음 단계.
   - `LOOPBACK_TO_EXECUTE` → 카운터를 증가시킨다. `< 3` 이면 자동으로 `/css:execute --session <slug> --resume` 를 호출하고(`kind:"phase"` 인 경우 `<slug>` 는 Epic 이 아니라 자식 슬러그) verify 를 다시 실행한다. `>= 3` 이면 에스컬레이션한다.
   - `ESCALATE` → 중단.

9. **락 해제**.

<self_check>
- [ ] verify-{slug}-{ts}.md exists
- [ ] code-review-{slug}-{ts}.md exists
- [ ] security-review-{slug}-{ts}.md exists
- [ ] retry_counters.verify updated on loopback
</self_check>

$ARGUMENTS
