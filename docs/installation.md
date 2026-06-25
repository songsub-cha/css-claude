> **English** · [한국어](installation.ko.md)

# Installation

## Prerequisites

- Claude Code installed (desktop app or CLI). Run it at least once so the `~/.claude/` directory is created.
- The `superpowers` plugin enabled (`/plugin enable superpowers@claude-plugins-official`).
- The `gh` CLI installed and authenticated (`gh auth status`).
- `git` >= 2.5.
- `ast-grep` (`sg`) — structural code-pattern search, used by many of the agents.
  ```bash
  # npm (requires Node.js, recommended for cross-platform)
  npm install -g @ast-grep/cli

  # or cargo (requires Rust)
  cargo install ast-grep --locked
  ```
  Verify the install: `sg --version`
- (Ubuntu only) `jq` is required for config parsing.

## Plugin (Claude Code)

The simplest path on Claude Code is the in-repo marketplace:

```
/plugin marketplace add songsub-cha/css-claude
/plugin install css@css-claude
```

Bump `version` in `.claude-plugin/plugin.json` on each release so installed users receive updates. The platform scripts below remain fully supported and install the same commands and agents.

## Windows

```powershell
git clone https://github.com/songsub-cha/css-claude.git
cd css-claude
powershell -ExecutionPolicy Bypass -File scripts\install.ps1
```

To overwrite existing personal settings: `powershell -ExecutionPolicy Bypass -File scripts\install.ps1 -Force`

## Ubuntu 22.04

```bash
git clone https://github.com/songsub-cha/css-claude.git
cd css-claude
bash scripts/install.sh
```

To overwrite existing personal settings: `FORCE=1 bash scripts/install.sh`

## Verifying the install

After installing, from any git-backed project:

```
/css:ship "add a hello-world function"
```

If the brainstorming flow starts, you're set. `Ctrl+C` is always safe and session state is preserved.

## Uninstall

Windows: `powershell -ExecutionPolicy Bypass -File scripts\uninstall.ps1`
Ubuntu:  `bash scripts/uninstall.sh`

Personal settings (`~/.claude/css/config.json`) and project artifacts (`<project>/.claude/css/`) are not removed. Delete them manually if you no longer need them.

## Codex App / CLI (experimental)

CSS also runs on OpenAI Codex App and CLI. The same `commands/` and `agents/` sources are transformed into Codex skills under `~/.agents/skills` plus runtime/agent data under `~/.codex/css`; your Claude Code install is untouched.

```bash
bash scripts/install-codex.sh
# Windows:
powershell -ExecutionPolicy Bypass -File scripts\install-codex.ps1
```

Then select skills such as `css-ship` from the App/CLI skill menu, or mention them directly:

```
$css-ship "add a hello-world function"
```

Some Codex surfaces also show enabled skills in the slash menu; choose the same `css-*` skill there when available.

Stage skills are `$css-interview`, `$css-plan`, `$css-phase`, `$css-review`, `$css-execute`, `$css-verify`, `$css-document`, and `$css-pr`.

Optional — enable parallel specialists by adding to `~/.codex/config.toml`:

```toml
[features]
multi_agent = true
```

Without it, specialists run sequentially in one agent (no parallelism, same result). Session state is shared with Claude Code at `<project>/.claude/css/`, so a session started in either tool resumes in the other. Execution behavior is governed by `~/.codex/css/RUNTIME.md`. Prerequisites: Python 3 (install-time), plus `codex`, `git`, and optionally `gh` at runtime.
