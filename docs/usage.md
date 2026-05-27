# Usage

## Quick start

In any git project:

```
/css:ship "<짧은 아이디어>"
```

The pipeline walks through: interview → plan → review → execute → verify → document → pr, with three approval gates.

## Individual commands

Each stage can also run standalone with `--slug`:

```
/css:interview "<idea>"
/css:plan --slug <slug>
/css:review --slug <slug>
/css:execute --slug <slug>
/css:verify --slug <slug>
/css:document --slug <slug>
/css:pr --slug <slug>
```

`--slug` is optional; CSS reads `<project>/.claude/css/sessions/_active.json` to find the most recent session.

## Multi-session concurrency

Open two terminals in the same project:

```
# Terminal 1
/css:ship "feature A"

# Terminal 2
/css:ship "feature B"
```

Each call generates its own slug and operates in isolation (separate session file, separate worktree, separate branch). The two never touch each other's state.

## Output locations

- Spec: `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md` (written by `superpowers:brainstorming`)
- Plan: `docs/superpowers/plans/YYYY-MM-DD-<feature>.md` (written by `superpowers:writing-plans`)
- Reviews/Executions/Verifies/Documents (staging): `<project>/.claude/css/{reviews,executions,verifies,documents}/`
- Domain specs (api/db/ui/etc.): `<project>/.claude/css/plans/<domain>-spec-<slug>-<ts>.md`
- Final user-facing docs: `<project>/docs/<slug>/{README,api,changelog}.md`
- Implementation branch: `css/<slug>` in worktree `../<repo>-css-<slug>`

## Resuming

- `Ctrl+C` is safe. Session state persists.
- Restart with `/css:ship --slug <slug>` (or any standalone command with `--slug`).
- The command resolves what phase the session is in and resumes from there.
