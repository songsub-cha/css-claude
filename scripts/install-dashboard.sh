#!/usr/bin/env bash
set -euo pipefail
require() { command -v "$1" >/dev/null || { echo "missing dependency: $1"; exit 1; }; }
require docker; docker compose version >/dev/null || { echo "docker compose plugin required"; exit 1; }
require python3; require systemctl
CSS_DIR="$HOME/.claude/css-dashboard"
mkdir -p "$CSS_DIR"/{queue,queue/processed,queue/failed,runs,bin}; chmod 700 "$CSS_DIR"
REPO_ROOT="$(git rev-parse --show-toplevel)"
[ -f "$CSS_DIR/config.json" ] || cp "$REPO_ROOT/config/dashboard-config.example.json" "$CSS_DIR/config.json"
if [ ! -f "$REPO_ROOT/dashboard/.env" ]; then
  PW=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))")
  sed "s|changeme|$PW|g" "$REPO_ROOT/dashboard/.env.example" > "$REPO_ROOT/dashboard/.env"
fi
cp "$REPO_ROOT/dashboard/bridge/bridge.py" "$CSS_DIR/bin/bridge.py"; chmod 700 "$CSS_DIR/bin/bridge.py"
mkdir -p "$HOME/.config/systemd/user"
cp "$REPO_ROOT/dashboard/bridge/css-dashboard-bridge.service" "$HOME/.config/systemd/user/"
systemctl --user daemon-reload
systemctl --user enable --now css-dashboard-bridge.service
(cd "$REPO_ROOT/dashboard" && docker compose up -d --build); sleep 5
(cd "$REPO_ROOT/dashboard" && docker compose exec -T dashboard alembic upgrade head)
HOST_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
echo "Dashboard up at http://${HOST_IP:-localhost}:7421"
