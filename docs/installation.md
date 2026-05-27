# Installation

## Prerequisites

- Claude Code installed (the desktop app or CLI). Run it at least once so `~/.claude/` exists.
- `superpowers` plugin enabled (`/plugin enable superpowers@claude-plugins-official`).
- `gh` CLI installed and authenticated (`gh auth status`).
- `git` >= 2.5.
- (Ubuntu only) `jq` for settings introspection.

## Windows

```powershell
git clone https://github.com/songsub-cha/css-claude.git
cd css-claude
.\scripts\install.ps1
```

To overwrite an existing personal config: `.\scripts\install.ps1 -Force`

## Ubuntu 22.04

```bash
git clone https://github.com/songsub-cha/css-claude.git
cd css-claude
bash scripts/install.sh
```

To overwrite an existing personal config: `FORCE=1 bash scripts/install.sh`

## Verifying

After install, in any project that uses git:

```
/css:ship "add a hello-world function"
```

You should see the brainstorming flow begin. Ctrl+C is safe — your session state is preserved.

## Uninstalling

Windows: `.\scripts\uninstall.ps1`
Ubuntu:  `bash scripts/uninstall.sh`

Personal config (`~/.claude/css/config.json`) and project artifacts (`<project>/.claude/css/`) are kept. Remove manually if you no longer want them.
