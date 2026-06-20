---
description: Implement the plan in an isolated worktree with strict TDD, cache-first from rich specs (CSS pipeline stage 4)
argument-hint: "[--session <name>] [--plan <plan-path>] [--resume]"
---

# /css:execute

Implement task-scoped Rich Specs inside an isolated worktree using strict Red-Green-Refactor TDD.

## Steps

1. Parse `--session`, `--plan`, `--resume`, and optional `--phase`; resolve the session and detailed plan.
2. Resolve a language profile when absent, preserving existing project scripts:
   - `pyproject.toml`/`uv.lock`: Python, `uv run pytest`, `uv run pytest --cov`
   - `package.json`: Node/TypeScript, existing test and coverage scripts
   - `pom.xml`: Maven, `./mvnw test` or `mvn test`
   - `build.gradle[.kts]`: Gradle, `./gradlew test`
   - `go.mod`: Go, `go test ./...`, `go test -cover ./...`
   - Otherwise ask for test and coverage commands, then persist them.
3. Resolve executable Rich Specs from `session.phases.review.rich_specs`. Only when absent, fall back to Phase `{parent_slug}-p{phase_index}-T*.md`, single-session `{slug}-T*.md`, then legacy `*-spec-{slug}-*.md`.
4. Pre-flight every routed task. Require exactly one non-advisory artifact with all canonical fields from `/css:review`; require `Phase: {phase_index or 1}`.
5. Create or resume the isolated worktree and branch. Phase path/branch are `../{repo}-css-{parent_slug}-p{phase_index}` and `css/{parent_slug}/p{phase_index}` from `session.base_branch`; single-session path/branch are `../{repo}-css-{slug}` and `css/{slug}`. Record worktree, branch, and base_branch in the session. Refuse every write outside the resolved worktree.
6. Enforce Gate 2 for master flow, acquire the execute lock, update `_active.json` (`latest_slug`, `active_epic`, `active_phase`), and dispatch `css-executor` with the exact `rich_specs` list. Instruct it to `cd` into and verify the worktree (`pwd` must match; ESCALATE on mismatch) before any write, keep every mutation and `git` command inside it, and never force-push, hard-reset, `rm -rf` tracked paths, or `chmod 777`.
7. For each task:
   - Apply `RED scaffold`, run `RED command`, and require non-zero exit.
   - Apply `GREEN template`, run `GREEN command`, and require zero exit.
   - Use `language_profile.test_command` only for legacy artifacts without per-task commands.
   - Use the bounded debugger then specialist fallback ladder; specialists write only inside the worktree and never test or commit.
   - Refactor, rerun validation, and commit the task with CSS-* trailers only (no Claude/AI attribution).
8. Run full tests and coverage after each batch; write the execution log with cache_miss_count; update session status from the final verdict; release the lock.

<self_check>
- [ ] Exact recorded Rich Specs were indexed; advisories were excluded
- [ ] Every task ran its RED and GREEN commands
- [ ] Executor verified the worktree cwd (Step 0) before writing
- [ ] Worktree path and branch are recorded
- [ ] Main working tree has no unexpected changes
</self_check>

$ARGUMENTS
