---
description: Remove the session worktree and merged branch after the PR lands (CSS pipeline housekeeping)
argument-hint: "[--session <name>] [--keep-branch] [--force]"
---

# /css:clean

Tear down a session's isolated worktree (and optionally its local branch) once the PR has merged. Safe by default: never deletes dirty, unpushed, or unmerged work without explicit confirmation.

## Steps

1. Parse `--session` (default `_active.json.latest_slug`), `--keep-branch`, `--force`. Resolve the session. For a `kind:"epic"` session with `child_slugs`, offer to run the same procedure for each completed child session.
2. Acquire the clean lock (`locks/{slug}-clean.lock`; stale after 60 min → replace with a note; a fresh lock from another run → abort with guidance).
3. Read `phases.execute.worktree` and `phases.execute.branch`. If neither exists (or the worktree directory is already gone), report "정리할 worktree가 없습니다", record `phases.clean`, release the lock, and exit.
4. Safety checks — each failed check requires an explicit AskUserQuestion confirmation before proceeding (`--force` does not skip the question; it only pre-summarizes everything that will be discarded into a single confirmation):
   - **Dirty**: `git -C <worktree> status --porcelain` must be empty.
   - **Merged**: when `phases.pr.artifact` is a PR URL and `gh` is available, `gh pr view <url> --json state` must report `MERGED`; for OPEN/CLOSED (or when no PR exists) ask before proceeding.
   - **Unpushed**: `git -C <worktree> log origin/<branch>..<branch> --oneline` must be empty; a never-pushed branch also requires confirmation.
5. Remove: `git worktree remove <worktree>` (plain — add `--force` only after the confirmations above), then `git worktree prune`. Unless `--keep-branch`, delete the local branch with `git branch -d <branch>` (`-D` only after confirmation). Never touch the remote branch — GitHub's "delete branch on merge" or the user owns that.
6. Update session: `phases.clean = {status: "completed", removed_worktree: <bool>, removed_branch: <bool>, completed_at: <ISO>}`. Release the lock and print exactly what was removed.

<self_check>
- [ ] No dirty, unpushed, or unmerged work was deleted without explicit confirmation
- [ ] Worktree removed and pruned (or reported absent)
- [ ] Branch handling matched --keep-branch and the confirmations
- [ ] phases.clean recorded; lock released
</self_check>

$ARGUMENTS
