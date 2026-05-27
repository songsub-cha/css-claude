---
description: Implement the plan in an isolated worktree with strict TDD, cache-first from rich specs (CSS pipeline stage 4)
argument-hint: "[--slug <name>] [--plan <plan-path>] [--resume]"
---

# /css:execute

Create or attach to a git worktree, then drive the executor through batches with TDD. GREEN draws from the rich-spec artifacts produced at `/css:review` (cache-first); specialists are only re-invoked as bounded fallback.

## Steps

1. **Parse arguments**: `--slug`, `--plan`, `--resume`.

2. **Resolve session**. Default `--slug` from `_active.json` if missing.

3. **Resolve plan path** (same rules as `/css:review`).

4. **Detect language profile** if `session.language_profile` is unset. Run the detection logic from the spec (Section: Language Detection Logic). Write the resolved profile into the session.

5. **Pre-flight: rich-spec readiness check**:
   - List `<project>/.claude/css/plans/*-spec-{slug}-*.md`.
   - For every plan task routed to a specialist, confirm the corresponding artifact has a `## Task {id}` section with `RED scaffold:` + `GREEN template:`.
   - If anything is missing → abort with "rich-spec 누락. `/css:review` 를 먼저 통과시켜주세요 (verdict=PASS)."

6. **Worktree setup** (if not `--resume`):
   - Compute repo name: `basename $(git rev-parse --show-toplevel)`.
   - Worktree path: `../{repo}-css-{slug}` (or `worktree_parent` from config if set).
   - If the path already exists: ask user "기존 worktree 가 있습니다. [재사용 / 새로 만들기 / 취소]".
   - On new: `git worktree add <path> -b css/<slug>` (base = current branch).
   - Record `phases.execute.worktree = <path>` and `phases.execute.branch = css/<slug>` in the session.

7. **AskUserQuestion (master-flow Gate 2)** ONLY if invoked as part of `/css:ship` (i.e., `session.master_flow == true`):
   "Plan 검증 완료. worktree '`<path>`' 생성 후 execute 를 시작합니다. 배치 N개, 작업 M개. 진행할까요? [Yes / Show plan / Cancel]"

8. **Echo header**: `[css:execute @ slug={slug}]`.

9. **Dispatch the executor**:

   ```
   Task(
     subagent_type="css-executor",
     description="css execute: {slug}",
     prompt="""
     <inputs>
     plan: {plan path}
     worktree: {worktree path}
     branch: css/{slug}
     language_profile: {profile object}
     session: <project>/.claude/css/sessions/{slug}.json
     rich_specs_dir: <project>/.claude/css/plans/
     </inputs>
     <task>
     Implement the plan task-by-task using strict Red-Green-Refactor TDD with the cache-first protocol:
       - RED: copy the matching rich-spec section's RED scaffold to the worktree, run, must fail.
       - GREEN: copy the matching rich-spec section's GREEN template, run tests.
       - On failure: css-debugger × 2 → specialist fallback × 1 → abort.
       - REFACTOR: css-code-simplifier (read-only suggestions).
       - COMMIT: per-task, on css/{slug}, with CSS-Slug / CSS-Task / CSS-Specialist-Spec / CSS-Specialist-Fallback trailers as applicable.
     Per-batch user checkpoints via AskUserQuestion. Coverage measured after each batch; below threshold → css-test-engineer (max 2 rounds).
     Index all rich-spec artifacts under rich_specs_dir before starting (build task_id → (spec_path, anchor) map).
     </task>
     <output_contract>
     Write exec log to: <project>/.claude/css/executions/exec-log-{slug}-{ts}.md
     Log MUST record cache_miss_count per slug.
     Final line: VERDICT=PASS | VERDICT=ESCALATE | VERDICT=PAUSE
     </output_contract>
     """
   )
   ```

10. **Parse verdict**:
    - `PASS` → session: `phases.execute.status = completed`. Announce next.
    - `ESCALATE` → surface reason to user with options [retry batch / accept and continue / abort].
    - `PAUSE` → user cancelled. Preserve state for `--resume`.

11. **Release lock**.

<self_check>
- [ ] Worktree path recorded in session
- [ ] Branch css/{slug} created and contains task commits
- [ ] exec-log file exists with cache_miss_count recorded
- [ ] Coverage measured and recorded
</self_check>

$ARGUMENTS
