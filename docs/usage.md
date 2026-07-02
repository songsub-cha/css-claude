> **English** · [한국어](usage.ko.md)

# Usage

## Quick start

From anywhere inside a git project:

```
/css:ship "<idea>"
```

The pipeline runs interview → plan → phase → review → execute → verify → document → pr, with three approval gates.

## Standalone commands

Each stage can also be run independently with `--session`:

```
/css:interview "<idea>"
/css:plan --session <slug>
/css:phase --session <slug>
/css:review --session <slug>
/css:execute --session <slug>
/css:verify --session <slug>
/css:document --session <slug>
/css:pr --session <slug>
/css:clean --session <slug>    # post-merge cleanup
```

`--session` is optional. If omitted, CSS automatically picks the most recent session from `<project>/.claude/css/sessions/_active.json`.

## Codex App / CLI equivalents

After `scripts/install-codex.*`, Codex exposes the same stages as installed `css-*` skills. Select a skill from the App/CLI skill menu, or mention it directly:

```
$css-ship "<idea>"
$css-review --session <slug>
```

The full set is `$css-interview`, `$css-plan`, `$css-phase`, `$css-review`, `$css-execute`, `$css-verify`, `$css-document`, `$css-pr`, and `$css-clean`. Skill invocation text is treated as the command's `$ARGUMENTS`; execution details are governed by `~/.codex/css/RUNTIME.md`.

## Concurrent multi-session

You can open two terminals and work on the same project at the same time:

```
# Terminal 1
/css:ship "Feature A"

# Terminal 2
/css:ship "Feature B"
```

Each invocation generates an independent slug and is isolated in its own session file, its own worktree, and its own branch. The two sessions never affect each other's state.

## Artifact locations

| Kind | Path |
|------|------|
| Spec | `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md` |
| Plan | `docs/superpowers/plans/YYYY-MM-DD-<feature>.md` |
| Staging (review / execute / verify / document) | `<project>/.claude/css/{reviews,executions,verifies,documents}/` |
| Task-scoped Rich Spec | `<project>/.claude/css/plans/{<slug>-T<task-id>.md | <epic>-p<phase>-T<task-id>.md}` |
| Final user docs | `<project>/docs/<slug>/{README,api,changelog}.md` |
| Implementation branch | `css/<slug>` (worktree: `../<repo>-css-<slug>`) |

## Resuming

- `Ctrl+C` is always safe. Session state is preserved.
- Restarting with `/css:ship --session <slug>` (or any standalone command with `--session`) automatically resumes from the interrupted stage.

## Cleanup

Once the PR has merged, tear down the worktree and local branch:

```
/css:clean --session <slug>
```

It never deletes dirty changes, unpushed commits, or an unmerged PR without asking first. Use `--keep-branch` to keep the local branch; the remote branch is never touched.
