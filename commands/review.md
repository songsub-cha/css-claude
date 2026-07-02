---
description: Audit the plan, enforce Single-Specialist Task Rule, dispatch domain specialists to author rich specs (CSS pipeline stage 3)
argument-hint: "[--session <name>] [--plan <plan-path>]"
---

# /css:review

Audit the plan and create task-scoped executable Rich Specs before implementation.

## Steps

1. Parse `--session` and `--plan`; resolve the session, plan, and spec. A child may resolve the spec from `parent_session.phases.interview.artifact`.
2. Enforce the loopback budget: `session.retries.review` must be below `session.config.review.max_loopback_attempts` (default 2), else `ESCALATE`. Acquire the review lock (`locks/{slug}-review.lock`; stale after 60 min → replace with a note; a fresh lock from another run → abort with guidance) and update `_active.json` (`latest_slug`, `active_epic`, `active_phase`).
   A multi-Phase candidate Epic must have `phases.phasing.status == completed`; otherwise stop and direct the user to `/css:phase --session <slug>`.
3. Choose the review level:
   - Multi-Phase Epic (`kind == "epic"` AND `single_phase != true`): architecture review only, no executable Rich Specs, report `.claude/css/reviews/review-{slug}-arch-{ts}.md`.
   - Phase, single-Phase Epic, or kind-less legacy session: Rich Spec review.
4. Enforce the Single-Specialist Task Rule. Multi-domain tasks must loop back to plan unless a dominant domain and `Cross_Domain_Notes` are explicitly justified.
5. For Rich Spec review, assign exactly one path per routed task before dispatch:
   - Phase: `.claude/css/plans/{parent_slug}-p{phase_index}-T{task_id}.md`
   - Single-session: `.claude/css/plans/{slug}-T{task_id}.md`
   Pass each specialist its `artifact_paths` mapping. Specialists MUST NOT invent filenames.
6. Every executable task artifact must contain:
   `## Task {id}`, `Specialist:`, `Phase: {phase_index or 1}`, `Files:`, `Verification mode: command`, `RED scaffold:`, `RED command:`, `GREEN template:`, `GREEN command:`, `Edge cases:`, `Depends-on:`, `Cross_Domain_Notes:`, and final `ARTIFACT=<path>`.
7. Dispatch advisories separately; these reviewers cannot write, so persist each returned report under `.claude/css/reviews/`:
   - `css-architect` for module boundaries, new architecture, or large refactors.
   - `css-security-reviewer` for auth, authorization, secrets, dependencies, payments, file uploads, or security-sensitive input.
   Advisory paths are not executable Rich Specs. CRITICAL/HIGH security design findings cause `LOOPBACK_TO_PLAN`.
8. Write the mode-specific review report and parse the final verdict.
9. On PASS record `phases.review.status`, `verdict`, `level`, `artifact`, exact executable `rich_specs`, separate `advisories`, and severity counts as `phases.review.findings = {critical, high, medium, low}` (gh_sync stage-summary comments read these). On loopback, increment `retries.review` and invoke the required earlier stage. Release the lock.

<self_check>
- [ ] Multi-Phase Epic review produced no executable Rich Specs
- [ ] Every routed task has exactly one valid task-scoped artifact
- [ ] `rich_specs` contains only executable artifacts; `advisories` is separate
- [ ] Final line contains `VERDICT=...`
</self_check>

$ARGUMENTS
