---
description: Generate <project>/docs/<slug>/ markdown documentation (CSS pipeline stage 6)
argument-hint: "[--slug <name>]"
---

# /css:document

Generate user-facing markdown documentation for the implemented feature. Wraps `css-documenter`.

## Steps

1. **Parse arguments**: `--slug`.

2. **Resolve session**.

3. **Pre-check**: `session.phases.verify.verdict` must be `PASS`. If not, abort with: "verify 가 통과되지 않았습니다. `/css:verify` 를 먼저 통과시켜주세요."

4. **Acquire lock**. Lock key = `locks/{slug}-document.lock` (for `kind:"phase"`, `slug` is the child slug). Update `_active.json` with `active_epic` (`parent_slug` or self) and `active_phase` (`phase_index` or null).

5. **Determine docs path**:
   - `kind:"phase"` session → output path = `docs/{epic}/p{phase_index}/README.md` (D3 per-Phase). No Epic-level aggregate README (deferred per D3 open question).
   - Legacy single-Phase session → output path = `docs/{slug}/README.md` (existing behavior).

6. **Echo header**: `[css:document @ slug={slug}]`.

7. **Dispatch the documenter**:

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

8. **Update session**: `phases.document.status = completed`, `phases.document.artifact = <README path>`.

9. **Release lock**.

<self_check>
- [ ] docs/<slug>/README.md exists
- [ ] Commit "docs(css): add docs for {slug}" in worktree
</self_check>

$ARGUMENTS
