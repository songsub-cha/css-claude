---
description: <project>/docs/<slug>/ 마크다운 문서 생성 (CSS 파이프라인 6단계)
argument-hint: "[--session <name>]"
---

# /css:document

구현된 기능에 대한 사용자 대상 마크다운 문서를 생성한다. `css-documenter` 를 감싼다(wrap).

## 단계

1. **인자 파싱**: `--session`.

2. **세션 해석**.

3. **사전 점검(Pre-check)**: `session.phases.verify.verdict` 가 반드시 `PASS` 여야 한다. 아니면 다음 메시지로 중단한다: "verify 가 통과되지 않았습니다. `/css:verify` 를 먼저 통과시켜주세요."

4. **락 획득**. 락 키 = `locks/{slug}-document.lock` (`kind:"phase"` 인 경우 `slug` 는 자식 슬러그). `_active.json` 을 `active_epic`(`parent_slug` 또는 자신)과 `active_phase`(`phase_index` 또는 null)로 갱신한다.

5. **docs 경로 결정**:
   - `kind:"phase"` 세션 → 출력 경로 = `docs/{epic}/p{phase_index}/README.md` (D3 Phase 별). Epic 레벨 통합 README 는 없음(D3 미해결 항목에 따라 보류).
   - 레거시 단일 Phase 세션 → 출력 경로 = `docs/{slug}/README.md` (기존 동작).

6. **헤더 출력**: `[css:document @ slug={slug}]`.

7. **documenter 디스패치**:

   ```
   Task(
     subagent_type="css-documenter",
     description="css document: {slug}",
     prompt="""
     <inputs>
     worktree: {session.phases.execute.worktree}
     spec: {session.phases.interview.artifact}
     plan: {session.phases.plan.artifact}
     verify: {session.phases.verify.artifact}
     epic: {parent_slug or slug}
     phase_index: {phase_index or null}
     docs_path: {docs/{epic}/p{phase_index}/README.md | docs/{slug}/README.md}
     </inputs>
     <task>
     Generate {docs_path} (required: Overview, Quick Start, Usage Examples, Architecture, Testing, Future Work) and conditionally api.md (when a public API surface exists) and changelog.md (when behavior changed or migration is required). Use Mermaid for diagrams; pull every example from a verified test (cite path:line); commit in the worktree as "docs(css): add docs for {slug}".
     </task>
     <output_contract>
     Final line: ARTIFACT=<project>/{docs_path}
     </output_contract>
     """
   )
   ```

8. **세션 갱신**: `phases.document.status = completed`, `phases.document.artifact = <README path>`.

9. **락 해제**.

<self_check>
- [ ] docs/<slug>/README.md exists
- [ ] Commit "docs(css): add docs for {slug}" in worktree
</self_check>

$ARGUMENTS
