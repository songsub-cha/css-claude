---
description: Generate <project>/docs/<slug>/ markdown documentation (CSS pipeline stage 6)
argument-hint: "[--session <name>]"
---

# /css:document

Generate user-facing documentation from verified implementation evidence.

## Steps

1. Resolve `--session`; require `session.phases.verify.verdict == "PASS"`; acquire the document lock; update `_active.json` (`latest_slug`, `active_epic`, `active_phase`).
2. Resolve the spec from `session.phases.interview.artifact` or `parent_session.phases.interview.artifact`.
3. Choose the docs path:
   - Phase: `docs/{parent_slug}/p{phase_index}/README.md`
   - Single-session: `docs/{slug}/README.md`
4. Dispatch `css-documenter` with worktree, resolved spec, plan, verify report, and docs path. Require Overview, Quick Start, Usage Examples, Architecture, Testing, and Future Work. Examples must cite verified tests.
5. Commit docs in the worktree, record `phases.document.artifact`, and release the lock.

<self_check>
- [ ] Resolved docs path exists
- [ ] Documentation commit exists in the worktree
</self_check>

$ARGUMENTS
