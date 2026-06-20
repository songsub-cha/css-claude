#!/usr/bin/env bash
# install.sh — Ubuntu 22.04 installer for CSS (Claude Super System)
#
# Usage:
#   bash scripts/install.sh                    # install from cloned repo
#   FORCE=1 bash scripts/install.sh            # overwrite existing config

set -euo pipefail

SOURCE_PATH="${SOURCE_PATH:-$(cd "$(dirname "$0")/.." && pwd)}"
CLAUDE_HOME="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
FORCE="${FORCE:-0}"

# --- helpers ---
section() { echo; echo "=== $1 ==="; }
ok()      { printf "  \033[32m[OK]\033[0m %s\n" "$1"; }
warn()    { printf "  \033[33m[WARN]\033[0m %s\n" "$1"; }
fail()    { printf "  \033[31m[MISSING]\033[0m %s\n" "$1"; }
need()    {
  if command -v "$1" >/dev/null 2>&1; then
    ok "$1"
  else
    fail "$1 (hint: $2)"
    return 1
  fi
}

# --- prerequisites ---
section "Verifying prerequisites"
ok_count=0
fail_count=0
for tool_hint in \
  "git=Install git: sudo apt-get install -y git" \
  "gh=Install gh: https://cli.github.com/manual/installation" \
  "jq=Install jq: sudo apt-get install -y jq"
do
  tool="${tool_hint%%=*}"
  hint="${tool_hint#*=}"
  if need "$tool" "$hint"; then
    ok_count=$((ok_count + 1))
  else
    fail_count=$((fail_count + 1))
  fi
done

if [ ! -d "$CLAUDE_HOME" ]; then
  fail "Claude config dir ($CLAUDE_HOME) — run Claude Code at least once first"
  fail_count=$((fail_count + 1))
else
  ok "Claude config dir ($CLAUDE_HOME)"
fi

if [ "$fail_count" -gt 0 ]; then
  echo
  echo "Aborting: fix the missing prerequisites above and re-run." >&2
  exit 1
fi

# superpowers warning (non-fatal)
settings_path="$CLAUDE_HOME/settings.json"
if [ -f "$settings_path" ]; then
  if jq -e '.enabledPlugins["superpowers@claude-plugins-official"] == true' "$settings_path" >/dev/null 2>&1; then
    ok "superpowers plugin enabled"
  else
    warn "superpowers plugin not enabled in settings.json"
    warn "CSS depends on it. Enable via /plugin or edit settings.json."
  fi
fi

# --- create dirs ---
section "Creating directories"
cmd_dir="$CLAUDE_HOME/commands/css"
agent_dir="$CLAUDE_HOME/agents/css"
css_dir="$CLAUDE_HOME/css"
mkdir -p "$cmd_dir" "$agent_dir" "$css_dir"
echo "  $cmd_dir"
echo "  $agent_dir"
echo "  $css_dir"

# --- copy ---
section "Copying commands"
cmd_count=0
if compgen -G "$SOURCE_PATH/commands/*.md" >/dev/null; then
  for f in "$SOURCE_PATH"/commands/*.md; do
    case "$f" in *.ko.md) continue ;; esac
    cp "$f" "$cmd_dir/"
    echo "  $(basename "$f")"
    cmd_count=$((cmd_count + 1))
  done
fi
echo "  ($cmd_count command files copied)"

section "Copying agents"
agent_count=0
if compgen -G "$SOURCE_PATH/agents/*.md" >/dev/null; then
  for f in "$SOURCE_PATH"/agents/*.md; do
    case "$f" in *.ko.md) continue ;; esac
    cp "$f" "$agent_dir/"
    echo "  $(basename "$f")"
    agent_count=$((agent_count + 1))
  done
fi
echo "  ($agent_count agent files copied)"

section "Copying lib"
lib_dir="$css_dir/lib"
mkdir -p "$lib_dir"
lib_count=0
if compgen -G "$SOURCE_PATH/lib/*.sh" >/dev/null; then
  for f in "$SOURCE_PATH"/lib/*.sh; do
    cp "$f" "$lib_dir/"
    echo "  $(basename "$f")"
    lib_count=$((lib_count + 1))
  done
fi
echo "  ($lib_count lib files copied)"

section "Installing default config"
src_config="$SOURCE_PATH/config/default-config.json"
dst_config="$css_dir/config.json"
if [ -f "$dst_config" ] && [ "$FORCE" != "1" ]; then
  warn "$dst_config already exists (use FORCE=1 to overwrite)"
else
  cp "$src_config" "$dst_config"
  echo "  $dst_config"
fi

section "Done"
echo "Installed:"
echo "  $cmd_count commands in $cmd_dir"
echo "  $agent_count agents   in $agent_dir"
echo "  config at        $dst_config"
echo
echo "Try: /css:ship \"<small idea>\" in a sample project."
