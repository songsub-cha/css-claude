> **English** · [한국어](usage.ko.md)

# Usage

## Quick start

From anywhere inside a git project:

```
/css:ship "<idea>"
```

The pipeline runs interview → plan → review → execute → verify → document → pr, with three approval gates.

## Standalone commands

Each stage can also be run independently with `--slug`:

```
/css:interview "<idea>"
/css:plan --slug <slug>
/css:review --slug <slug>
/css:execute --slug <slug>
/css:verify --slug <slug>
/css:document --slug <slug>
/css:pr --slug <slug>
```

`--slug` is optional. If omitted, CSS automatically picks the most recent session from `<project>/.claude/css/sessions/_active.json`.

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
| Domain-specialist Rich Spec | `<project>/.claude/css/plans/<domain>-spec-<slug>-<ts>.md` |
| Final user docs | `<project>/docs/<slug>/{README,api,changelog}.md` |
| Implementation branch | `css/<slug>` (worktree: `../<repo>-css-<slug>`) |

## Resuming

- `Ctrl+C` is always safe. Session state is preserved.
- Restarting with `/css:ship --slug <slug>` (or any standalone command with `--slug`) automatically resumes from the interrupted stage.
