---
description: Test + coverage + code review + security review (CSS pipeline stage 5)
argument-hint: "[--session <name>] [--exec-log <path>]"
---

# /css:verify

Independently verify task commands, full tests, coverage, acceptance criteria, code quality, and security.

## Steps

1. Parse arguments, resolve the session, enforce the three-attempt counter, acquire the verify lock, and update `_active.json` (`latest_slug`, `active_epic`, `active_phase`).
2. Resolve the spec from the session or parent_session. Resolve executable Rich Specs from `session.phases.review.rich_specs`; use legacy path fallback only when the field is absent.
3. Scope a child Phase to artifacts tagged `Phase: {phase_index}`. Treat single-Phase and kind-less legacy sessions as `Phase: 1`.
4. Dispatch `css-verifier` with worktree, branch, language_profile, spec, plan, phase_index, and exact `rich_specs`.
5. In the worktree, rerun every Rich Spec `GREEN command`, then run full `language_profile.test_command` and `coverage_command`.
6. Map every in-scope acceptance criterion to concrete code and test evidence. Dispatch `css-code-reviewer` and `css-security-reviewer` in parallel; they cannot write, so persist their returned reports under `.claude/css/verifies/`.
7. Any GREEN command failure, full-test failure, coverage below threshold, unmapped criterion, or CRITICAL/HIGH finding causes `LOOPBACK_TO_EXECUTE` until the retry limit, then `ESCALATE`.
8. Record the aggregate report and verdict; release the lock.

<self_check>
- [ ] Every task GREEN command was rerun
- [ ] Full tests and coverage ran in the worktree
- [ ] Code and security review reports exist
- [ ] Retry counter is updated on loopback
</self_check>

$ARGUMENTS
