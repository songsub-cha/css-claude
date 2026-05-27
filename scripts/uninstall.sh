#!/usr/bin/env bash
# uninstall.sh — Remove CSS commands and agents.
# Preserves ~/.claude/css/config.json and per-project artifacts.
set -euo pipefail

CLAUDE_HOME="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
cmd_dir="$CLAUDE_HOME/commands/css"
agent_dir="$CLAUDE_HOME/agents/css"

for d in "$cmd_dir" "$agent_dir"; do
  if [ -d "$d" ]; then
    rm -rf "$d"
    printf "\033[32mRemoved\033[0m %s\n" "$d"
  else
    printf "\033[33mSkip (absent)\033[0m %s\n" "$d"
  fi
done

echo
echo "Kept:"
echo "  $CLAUDE_HOME/css/config.json — your personal defaults"
echo "  <project>/.claude/css/ — per-project artifacts (remove manually if no longer needed)"
echo
echo "To reinstall: bash scripts/install.sh"
