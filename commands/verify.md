---
description: Test + coverage + code review + security review (CSS pipeline stage 5)
argument-hint: "[--session <name>] [--exec-log <path>]"
---

# /css:verify

Independently verify task commands, full tests, coverage, acceptance criteria, code quality, and security.

## Steps

1. Parse arguments, resolve the session, and enforce the loopback budget: `session.retries.verify` must be below `session.config.verify.max_loopback_attempts` (default 3), else `ESCALATE`. Acquire the verify lock (`locks/{slug}-verify.lock`; stale after 60 min → replace with a note; a fresh lock from another run → abort with guidance) and update `_active.json` (`latest_slug`, `active_epic`, `active_phase`).
2. Resolve the spec from the session or parent_session. Resolve executable Rich Specs from `session.phases.review.rich_specs`; use legacy path fallback only when the field is absent.
3. Scope a child Phase to artifacts tagged `Phase: {phase_index}`. Treat single-Phase and kind-less legacy sessions as `Phase: 1`.
4. Dispatch `css-verifier` with worktree, branch, language_profile, spec, plan, phase_index, the execution log (from `--exec-log`, else `session.phases.execute.artifact` — cross-check its claimed results against what actually reruns), and exact `rich_specs`.
5. In the worktree, rerun every Rich Spec `GREEN command`, then run full `language_profile.test_command` and `coverage_command`.
6. Map every in-scope acceptance criterion to concrete code and test evidence. Dispatch `css-code-reviewer` and `css-security-reviewer` in parallel; they cannot write, so persist their returned reports under `.claude/css/verifies/`.
7. Any GREEN command failure, full-test failure, coverage below `session.config.verify.coverage_threshold` (default 85), unmapped criterion, or CRITICAL/HIGH finding (read from either reviewer's `VERDICT=ISSUES_FOUND critical=<n> high=<n> ...` final line) causes `LOOPBACK_TO_EXECUTE` (increment `retries.verify`) until the retry limit, then `ESCALATE`.
8. Record the aggregate report, `verdict`, and `phases.verify.test_summary = {tests, passed, coverage_pct}` (gh_sync stage-summary comments read these); release the lock.

<self_check>
- [ ] Every task GREEN command was rerun
- [ ] Full tests and coverage ran in the worktree
- [ ] Code and security review reports exist
- [ ] Retry counter is updated on loopback
</self_check>

$ARGUMENTS
