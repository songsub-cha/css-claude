---
description: plan 감사, Single-Specialist Task Rule 강제, 도메인 전문가를 디스패치해 rich spec 작성 (CSS 파이프라인 3단계)
argument-hint: "[--session <name>] [--plan <plan-path>]"
---

# /css:review

plan 을 spec 에 비추어 감사하고, 도메인 전문가를 디스패치해 RICH spec(태스크별 RED 스캐폴드 + GREEN 템플릿)을 생성하며, loopback 여부를 결정한다. `css-reviewer` 를 감싼다(wrap).

## 단계

1. **인자 파싱**: `--session`, `--plan`.

2. **세션 해석** (`/css:plan` 과 동일한 규칙).

3. **plan 경로 해석**: `--plan <path>` > `session.phases.plan.artifact` > 오류.

4. **재시도 카운터 확인**: `session.retry_counters.review >= 2` 이면 `verdict = ESCALATE` 로 설정하고 사용자에게 질문한다: "review 자동 재시도 한도(2회) 초과. 어떻게 진행할까요? [한 번 더 시도 / 현재 plan으로 진행 / 중단]". 사용자 선택을 적용하고 중단한다.

5. 이 슬러그에 대해 `review` 의 **락을 획득**한다.

6. **헤더 출력**: `[css:review @ slug={slug}, attempt={n+1}/2]`.

7. 세션 `kind` 로부터 **review 레벨 결정**:
   - `kind == "epic"` (또는 없음) → **아키텍처 리뷰**: 스켈레톤 plan 을 spec 과 대조해 감사한다; **Phase 컬럼**을 포함한 커버리지 매트릭스를 만든다(모든 스켈레톤 태스크에 `phase_manifest` 의 `phase_index` 를 태그). Phase 별 거친(coarse) Single-Specialist 라우팅을 결정한다. **rich-spec 은 생성하지 않는다.** 리포트를 `.claude/css/reviews/review-{slug}-arch-{ts}.md` 에 작성한다.
   - `kind == "phase"` → **rich-spec 디스패치** (기존 동작): 도메인 전문가를 디스패치해 **이 Phase 의 태스크에 대해서만** 태스크별 RED 스캐폴드 + GREEN 템플릿을 생성하고 `.claude/css/plans/{parent_slug}-p{phase_index}-T*.md` 에 작성한다; 각 블록은 `Phase: {phase_index}` 라인을 포함한다.

8. **reviewer 디스패치**:

   ```
   Task(
     subagent_type="css-reviewer",
     description="css review: {slug}",
     prompt="""
     <inputs>
     spec: {spec path}
     plan: {plan path}
     session: <project>/.claude/css/sessions/{slug}.json
     project_root: <cwd>
     review_level: {architecture | rich-spec}
     phase_index: {phase_index or null}
     </inputs>
     <task>
     Audit the plan against the spec. Build the coverage matrix.
     - architecture level (kind=epic): add Phase column tagging each task with its phase_index from phase_manifest. Coarse Single-Specialist routing per Phase. NO rich-specs. Report to .claude/css/reviews/review-{slug}-arch-{ts}.md.
     - rich-spec level (kind=phase): run the Single-Specialist Task Rule audit per task (multi-domain → LOOPBACK_TO_PLAN). Detect domains and dispatch matching specialists in parallel via Task — each specialist MUST produce a RICH spec artifact with per-task RED scaffolds + GREEN templates tagged with Phase: {phase_index}.
     Emit the final verdict.
     </task>
     <output_contract>
     Write the report to: <project>/.claude/css/reviews/review-{slug}-{ts}.md
     Sections in order: Verdict, Coverage Matrix (with Phase column for architecture reviews), Single-Specialist Audit table, Findings, Domain Specialist Dispatch summary (with rich-spec artifact paths), Retry Counter.
     Final line: VERDICT=PASS | VERDICT=LOOPBACK_TO_PLAN | VERDICT=LOOPBACK_TO_INTERVIEW
     </output_contract>
     """
   )
   ```

8. **에이전트의 마지막 줄에서 판정 파싱**:
   - `PASS` → 세션 갱신: `phases.review.status = completed`, `phases.review.verdict = PASS`; 아무것도 증가시키지 않는다. 다음 단계를 안내한다.
   - `LOOPBACK_TO_PLAN` → `retry_counters.review` 를 증가시킨다. `< 2` 이면 자동으로 `/css:plan --session <slug>` 를 호출한 뒤 `/css:review` 를 다시 실행한다. `>= 2` 이면 사용자에게 에스컬레이션한다.
   - `LOOPBACK_TO_INTERVIEW` → 사용자에게 "interview 단계로 되돌아가시겠습니까?" 라고 묻는다. 확인 시 `/css:interview --session <slug>` → `/css:plan` → `/css:review` 를 호출한다.
   - `ESCALATE` → 중단하고 사용자에게 노출한다.

9. **락 해제**.

<self_check>
- [ ] Report file exists
- [ ] session.phases.review.verdict set
- [ ] Every routed task has a populated per-task block in its rich-spec artifact
- [ ] retry_counters.review updated on loopback
- [ ] Final line contains VERDICT=...
</self_check>

$ARGUMENTS
