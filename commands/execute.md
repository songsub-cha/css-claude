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
5. Create or resume the isolated worktree and branch, both cut from `session.base_branch` (captured at interview; fallback `main`). Phase path/branch are `../{repo}-css-{parent_slug}-p{phase_index}` and `css/{parent_slug}/p{phase_index}`; single-session path/branch are `../{repo}-css-{slug}` and `css/{slug}`. The worktree parent directory is `session.config.execute.worktree_parent` when set, else `..`. Note: a sibling (`..`) worktree lives outside the project directory, so Claude Code may require permission approval for writes there — either pre-approve the worktree path (additional working directory / `--add-dir`), or set `worktree_parent` to `.worktrees` to keep the worktree inside the repo (ensure `.worktrees/` is git-ignored). Record worktree, branch, and base_branch in the session. Refuse every write outside the resolved worktree.
6. Enforce Gate 2 for master flow — when `session.master_flow == true`, require `session.gates.gate2_pre_execute.state == "approved"`; if not, abort: "Gate 2가 승인되지 않았습니다. `/css:ship --session <name>`으로 진행하세요." (standalone non-master runs need no gate — the user invoked execute directly). Acquire the execute lock (`locks/{slug}-execute.lock`; stale after 60 min → replace with a note; a fresh lock from another run → abort with guidance), update `_active.json` (`latest_slug`, `active_epic`, `active_phase`), and dispatch `css-executor` with the exact `rich_specs` list. The executor is a subagent and cannot prompt the user; match its final line by the `VERDICT=` prefix (not full-line equality — a `reason="..."` suffix may follow), and on `VERDICT=PAUSE`, surface the quoted reason, ask the user here, then re-dispatch with `--resume`. Instruct it to `cd` into and verify the worktree (`pwd` must match; ESCALATE on mismatch) before any write, keep every mutation and `git` command inside it, and never force-push, hard-reset, `rm -rf` tracked paths, or `chmod 777`.
7. For each task:
   - Apply `RED scaffold`, run `RED command`, and require non-zero exit.
   - Apply `GREEN template`, run `GREEN command`, and require zero exit.
   - Use `language_profile.test_command` only for legacy artifacts without per-task commands.
   - Use the bounded debugger (at most `session.config.execute.tdd_self_heal_max` attempts, default 2) then the specialist fallback ladder; specialists write only inside the worktree and never test or commit.
   - Refactor, rerun validation, and commit the task with CSS-* trailers only (no Claude/AI attribution).
8. Run full tests and coverage after each batch; write the execution log with cache_miss_count (a cache miss = a task where the Rich Spec template did not survive contact and a fallback specialist had to be invoked); update session status from the final verdict and record `phases.execute.commit_count` and `phases.execute.test_summary = {tests, passed, coverage_pct}` (gh_sync stage-summary comments read these); release the lock.

<self_check>
- [ ] Exact recorded Rich Specs were indexed; advisories were excluded
- [ ] Every task ran its RED and GREEN commands
- [ ] Executor verified the worktree cwd (Step 0) before writing
- [ ] Worktree path and branch are recorded
- [ ] Main working tree has no unexpected changes
</self_check>

$ARGUMENTS
