#!/usr/bin/env bash
# Golden: bridge systemd user unit assertions
# Run from worktree root: bash tests/golden/bridge-systemd.spec.md
set -euo pipefail

test -f dashboard/bridge/css-dashboard-bridge.service || { echo "FAIL: css-dashboard-bridge.service not found"; exit 1; }
grep -q "ExecStart=/usr/bin/python3 %h/.claude/css-dashboard/bin/bridge.py" dashboard/bridge/css-dashboard-bridge.service || { echo "FAIL: ExecStart line missing or incorrect"; exit 1; }
grep -q "Restart=on-failure" dashboard/bridge/css-dashboard-bridge.service || { echo "FAIL: Restart=on-failure missing"; exit 1; }
grep -q "WantedBy=default.target" dashboard/bridge/css-dashboard-bridge.service || { echo "FAIL: WantedBy=default.target missing"; exit 1; }

echo "PASS: bridge-systemd golden assertions"
