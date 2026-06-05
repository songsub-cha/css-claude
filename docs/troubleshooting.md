# Troubleshooting

## "CSS requires the superpowers plugin"

`/css:interview` and `/css:plan` depend on `superpowers`. Enable it:

```
/plugin enable superpowers@claude-plugins-official
```

or edit `~/.claude/settings.json`:

```json
{
  "enabledPlugins": {
    "superpowers@claude-plugins-official": true
  }
}
```

## "gh not found" during /css:pr

Install GitHub CLI: https://cli.github.com/manual/installation, then `gh auth login`.

## "Worktree already exists for slug X"

Either reuse the existing worktree (CSS will prompt), or `git worktree remove ../<repo>-css-<slug>` and start fresh.

## "Same-slug collision: another session is in phase Y"

Two terminals tried to run the same slug. Wait, or use a different idea/slug. If the lock is stale (>30 min), CSS auto-releases with a warning.

## "RED failed: tests did not fail"

The Red phase needs the test to fail before the implementation exists. Either:
- The plan's test is wrong (asserts something already true).
- An earlier task already added the implementation.

Run `/css:review --slug <slug>` to re-audit the plan.

## "Coverage below 85% after self-heal"

`css-test-engineer` was invoked twice but couldn't reach 85%. Inspect the coverage report path in the verify log; add tests manually or lower the threshold per-project in `<project>/.claude/css/config.json`.

## "session.json schema mismatch"

A new CSS version expects a newer session schema. Either:
- Finish the current session under the old version, then upgrade.
- Or back up `<project>/.claude/css/sessions/<slug>.json.bak.<ts>` and restart the session with the new CSS version.

## Old Codex `/css-*` prompts still appear

Older CSS Codex installs generated custom prompt files under `~/.codex/prompts/css-*.md`. Current installs use Codex skills under `~/.agents/skills/css-*/SKILL.md` and do not remove legacy prompt files automatically. If the old prompt entries are confusing, delete only the generated CSS prompt files:

```bash
rm ~/.codex/prompts/css-*.md
```

On Windows PowerShell:

```powershell
Remove-Item "$env:USERPROFILE\.codex\prompts\css-*.md"
```

## Cleaning up failed sessions

```bash
# Remove session file
rm <project>/.claude/css/sessions/<slug>.json

# Remove worktree
git worktree remove ../<repo>-css-<slug>

# Optionally delete branch (only if NOT pushed)
git branch -D css/<slug>
```
