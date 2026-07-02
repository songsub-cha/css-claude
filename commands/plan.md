---
description: Turn the spec into a structured plan via superpowers:writing-plans (CSS pipeline stage 2)
argument-hint: "[--session <name>] [--from <spec-path>]"
---

# /css:plan

Translate the approved spec into a skeleton Epic plan or an executable detailed plan.

## Steps

1. Parse `--session` and `--from`; otherwise resolve `_active.json.latest_slug`.
2. Resolve the spec in this order: `--from`, `session.phases.interview.artifact`, then `parent_session.phases.interview.artifact`. Stop if none exists.
3. Acquire the plan lock (`locks/{slug}-plan.lock`; stale after 60 min → replace with a note; a fresh lock from another run → abort with guidance), update `_active.json` (`latest_slug`, `active_epic`, `active_phase`), and echo `[css:plan @ slug={slug}]`.
4. Determine the level:
   - Multi-Phase candidate: `kind == "epic"` AND `single_phase != true` -> skeleton plan with coarse tasks, batches, rough file targets, `task_count`, and `batch_count`.
   - `kind == "phase"`, `single_phase == true`, or kind-less legacy session -> detailed bite-sized TDD plan with exact files, complete code, dependencies, and executable verification commands.
5. For a child Phase, include only its manifest batches and write `docs/superpowers/plans/{parent_slug}-p{phase_index}.md`. Otherwise write `docs/superpowers/plans/YYYY-MM-DD-{slug}.md`.
6. Invoke `superpowers:writing-plans`. Require every task to map to one specialist or executor-direct glue; decompose multi-domain tasks before review.
7. Record status, artifact, level, task_count, batch_count, and completed_at. Release the lock.

<self_check>
- [ ] Spec resolved directly or through parent_session
- [ ] Single-Phase and legacy sessions have detailed plans
- [ ] Plan artifact exists and session points to it
- [ ] Final line contains `NEXT=review` or `ARTIFACT=<plan path>`
</self_check>

$ARGUMENTS
