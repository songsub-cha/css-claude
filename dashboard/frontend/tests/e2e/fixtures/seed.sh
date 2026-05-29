#!/usr/bin/env bash
# E2E seed: creates a mock session (feat-x in review stage, gate2 pending)
# and a mock claude binary that flips the session to execute on approval.
set -euo pipefail

CSS_DASHBOARD_DIR="$HOME/.claude/css-dashboard"
PROJECTS_JSON="$CSS_DASHBOARD_DIR/projects.json"
SESSIONS_DIR="$HOME/.claude/css/sessions"
BIN_DIR="$CSS_DASHBOARD_DIR/bin"

mkdir -p "$CSS_DASHBOARD_DIR" "$SESSIONS_DIR" "$BIN_DIR"

# Seed a test project
SEED_PROJECT='{"id":1,"repo_root":"/tmp/e2e-test-project","repo_name":"e2e-test-project","color":"#22c55e"}'
if [ ! -f "$PROJECTS_JSON" ]; then
  echo "[$SEED_PROJECT]" > "$PROJECTS_JSON"
else
  python3 -c "
import json, sys
data = json.load(open('$PROJECTS_JSON'))
if not any(p.get('repo_root') == '/tmp/e2e-test-project' for p in data):
    data.append($SEED_PROJECT)
    json.dump(data, open('$PROJECTS_JSON', 'w'), indent=2)
"
fi

# Seed a session JSON for feat-x in review stage with gate2 pending
SESSION_FILE="$SESSIONS_DIR/feat-x.json"
cat > "$SESSION_FILE" <<'SESSIONEOF'
{
  "slug": "feat-x",
  "repo_root": "/tmp/e2e-test-project",
  "repo_name": "e2e-test-project",
  "current_phase": "review",
  "idea": "E2E test feature",
  "phases": {
    "interview": {"status": "completed"},
    "plan": {"status": "completed"},
    "review": {"status": "in_progress"}
  },
  "gates": {
    "gate2_pre_execute": {
      "state": "pending",
      "source": null,
      "reached_at": "2026-05-28T00:00:00Z",
      "approved_at": null,
      "approved_by": null
    }
  },
  "mtime": 1748390400
}
SESSIONEOF

# Seed a mock claude binary that flips current_phase to execute on approval
MOCK_CLAUDE="$BIN_DIR/claude"
cat > "$MOCK_CLAUDE" <<'CLAUDEEOF'
#!/usr/bin/env bash
# Mock claude binary for E2E tests
# When called with CSS_DASHBOARD_RESUME=1, flips feat-x to execute phase
SESSION_FILE="$HOME/.claude/css/sessions/feat-x.json"
if [ "${CSS_DASHBOARD_RESUME:-}" = "1" ] && [ -f "$SESSION_FILE" ]; then
  python3 -c "
import json
data = json.load(open('$SESSION_FILE'))
data['current_phase'] = 'execute'
data['gates']['gate2_pre_execute']['state'] = 'approved'
data['gates']['gate2_pre_execute']['approved_by'] = 'dashboard_drag'
json.dump(data, open('$SESSION_FILE', 'w'), indent=2)
print('mock-claude: flipped feat-x to execute')
"
fi
CLAUDEEOF
chmod +x "$MOCK_CLAUDE"

echo "E2E seed complete: feat-x session created in review with gate2 pending."
