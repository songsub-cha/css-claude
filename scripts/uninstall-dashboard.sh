#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(git rev-parse --show-toplevel)"
systemctl --user disable --now css-dashboard-bridge.service 2>/dev/null || true
rm -f "$HOME/.config/systemd/user/css-dashboard-bridge.service"; systemctl --user daemon-reload
read -p "Remove postgres volume (deletes history)? [y/N] " yn
if [ "$yn" = "y" ] || [ "$yn" = "Y" ]; then (cd "$REPO_ROOT/dashboard" && docker compose down -v)
else (cd "$REPO_ROOT/dashboard" && docker compose down); fi
if [ -f "$HOME/.claude/css-dashboard/config.json" ]; then
  python3 -c "import json,os; p=os.path.expanduser('~/.claude/css-dashboard/config.json'); d=json.load(open(p)); d['dashboard_enabled']=False; json.dump(d, open(p,'w'), indent=2)"
fi
echo "Dashboard uninstalled. CSS reverts to legacy AskUserQuestion mode."
