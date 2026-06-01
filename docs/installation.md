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
