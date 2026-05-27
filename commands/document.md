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

4. **Acquire lock**.

5. **Echo header**: `[css:document @ slug={slug}]`.

6. **Dispatch the documenter**:

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
     </inputs>
     <task>
     Generate <project>/docs/{slug}/README.md (required: Overview, Quick Start, Usage Examples, Architecture, Testing, Future Work) and conditionally api.md (when a public API surface exists) and changelog.md (when behavior changed or migration is required). Use Mermaid for diagrams; pull every example from a verified test (cite path:line); commit in the worktree as "docs(css): add docs for {slug}".
     </task>
     <output_contract>
     Final line: ARTIFACT=<project>/docs/{slug}/README.md
     </output_contract>
     """
   )
   ```

7. **Update session**: `phases.document.status = completed`, `phases.document.artifact = <README path>`.

8. **Release lock**.

<self_check>
- [ ] docs/<slug>/README.md exists
- [ ] Commit "docs(css): add docs for {slug}" in worktree
</self_check>

$ARGUMENTS
