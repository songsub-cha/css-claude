#!/usr/bin/env bash
# install-codex.sh -- install CSS into OpenAI Codex runtime + skills.
# Single source = this repo's commands/ + agents/. The Claude Code install is
# untouched (use scripts/install.sh for that).
#
# Usage:
#   bash scripts/install-codex.sh                 # install
#   FORCE=1 bash scripts/install-codex.sh         # overwrite existing config.json
set -euo pipefail

SOURCE_PATH="${SOURCE_PATH:-$(cd "$(dirname "$0")/.." && pwd)}"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
CODEX_SKILLS_DIR="${CODEX_SKILLS_DIR:-$HOME/.agents/skills}"
FORCE="${FORCE:-0}"

section() { echo; echo "=== $1 ==="; }

section "Verifying prerequisites"
PYTHON=""
for cand in python3 python; do
  # Must exist AND actually run Python — on Windows `python3` is often a
  # Microsoft Store alias stub that exists on PATH but does nothing.
  if command -v "$cand" >/dev/null 2>&1 && "$cand" -c 'import sys' >/dev/null 2>&1; then
    PYTHON="$cand"; break
  fi
done
if [ -z "$PYTHON" ]; then
  echo "  [MISSING] python3/python (required to transform sources)" >&2
  exit 1
fi
echo "  [OK] $PYTHON"
command -v codex >/dev/null 2>&1 && echo "  [OK] codex CLI" || echo "  [WARN] codex CLI not found (runtime dependency)"
command -v git   >/dev/null 2>&1 && echo "  [OK] git"        || echo "  [WARN] git not found (runtime dependency)"
command -v gh    >/dev/null 2>&1 && echo "  [OK] gh"          || echo "  [WARN] gh not found (PR step falls back to handoff)"

section "Installing CSS Codex artifacts"
force_flag=""
[ "$FORCE" = "1" ] && force_flag="--force"
( cd "$SOURCE_PATH/tools" && "$PYTHON" -m codex_install --source "$SOURCE_PATH" --dest "$CODEX_HOME" --skills-dir "$CODEX_SKILLS_DIR" $force_flag )

section "Done"
echo "Optional — enable parallel specialists in $CODEX_HOME/config.toml:"
echo "  [features]"
echo "  multi_agent = true"
echo
echo "Try: \$css-ship \"<small idea>\" in a new Codex App or CLI session."
