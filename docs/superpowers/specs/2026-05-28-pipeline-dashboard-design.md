# CSS Pipeline Dashboard — Design Spec

## Metadata

- **Created**: 2026-05-28
- **Owner**: sub1904@gmail.com
- **Status**: Design — pending plan + implementation
- **Slug (session id)**: `pipeline-dashboard`
- **Brainstorming session**: Driven by `superpowers:brainstorming` via `/css:ship`
- **Targets**:
  - New: `dashboard/` (FastAPI backend + React frontend + bridge daemon + docker-compose)
  - Modified: `commands/{interview,ship,execute,pr}.md` and all 8 commands (CLI flag rename)
  - New: `scripts/install-dashboard.sh`, `scripts/uninstall-dashboard.sh`

## Overview

A **locally-hosted, multi-project dashboard** that visualizes CSS pipeline progress and lets the user approve each pipeline Gate by **dragging a session card from one Kanban column to the next**. The dashboard observes the existing CSS session JSON files via a file watcher, persists completed-session history + user settings in PostgreSQL, and triggers pipeline resumes through a small host-side bridge daemon that invokes the `claude` CLI on the user's behalf.

The dashboard does **not replace** the existing terminal flow — both terminal `AskUserQuestion` approval and dashboard drag-and-drop approval are supported, even mixed within a single session (Gate 2 in terminal, Gate 3 in dashboard, or vice versa). Mutual exclusion is enforced via the existing per-session lock file.

### Primary user (single-user, personal-use tool)

The repository owner running CSS pipelines on an Ubuntu 22.04 home server, accessed from a Windows 11 workstation over LAN. No multi-tenant requirements.

### Goals

1. **Visibility**: At-a-glance view of every active CSS session across every registered project, with per-stage progress, elapsed time, batch/task detail, and artifact accordion.
2. **Drag-and-drop Gate approval**: Replace terminal `AskUserQuestion` for Gate 2 (pre-execute) and Gate 3 (pre-pr) with a Kanban card drag from one column to the next. Approval triggers automatic pipeline resume.
3. **History + settings**: Archive completed sessions for retrospection; let the user assign a stable color per repository for visual grouping.
4. **Cross-path approval**: Either approval channel (terminal or dashboard) usable per-Gate per-invocation. No global mode switch.
5. **Minimal CSS pipeline disruption**: Only 4 of 8 commands change. Modifications are additive (legacy AskUserQuestion path preserved when dashboard is disabled).

### Non-Goals (v0.1)

- Multi-user, RBAC, or remote (WAN) access. LAN-only, no authentication.
- Editing pipeline state from the dashboard beyond gate approval (no abort, no rollback, no edit). v0.1 is *observer + gate-approver*.
- Mobile-optimized layout. Desktop (≥1280px) primary; tablet best-effort.
- Replacing CSS pipeline orchestration. The dashboard never owns pipeline logic; CSS commands remain authoritative.
- Hot-reload of CSS command modifications across versions (assume single CSS version installed).

## Decisions Summary

| Topic | Decision |
|---|---|
| Project scope | Multi-project. Dashboard reads sessions from all registered repos on the host. |
| Backend stack | Python 3.12 + FastAPI + uvicorn + asyncpg + SQLAlchemy 2.x + watchdog |
| Frontend stack | React 19 + Vite + TypeScript + TailwindCSS v4 + dnd-kit + zustand + react-markdown |
| Persistence | PostgreSQL 16 (history + config). Active sessions remain file-based as source of truth. |
| Real-time | Server-Sent Events (SSE) from FastAPI → React |
| Network | Bind 0.0.0.0:7421 (LAN). No authentication (LAN trust). |
| Layout | A. Kanban 7-column with left-stripe repo color and right slide-out detail panel (GitHub Issues style) |
| Drag rules | Gate 2 (review→execute) and Gate 3 (document→pr) only. Other column moves rejected. |
| Gate approval cross-path | Per-Gate per-invocation. TTY check + lock file mutual exclusion. |
| Daemon-CSS coupling | File-based (session JSON + queue dir). Hook-based replacement evaluated and rejected (Hooks fire only inside live CC sessions). |
| Bridge location | Runs on host as systemd user service (not in container). Avoids in-container `claude` auth + worktree-parent volume issues. |
| Project auto-discovery | First `/css:*` invocation in a project appends to `~/.claude/css-dashboard/projects.json` (flock-serialized). |
| Resume failure | Card error icon + retry button. Audit logged. No automatic retry in v0.1. |
| Artifact rendering | Accordion (default collapsed) + lazy fetch on expand. Whitelisted artifact names per session. |
| Deployment | docker-compose (dashboard + postgres). Install script bootstraps DB, systemd unit, config. |
| CLI flag rename | `--slug <name>` → `--session <name>` across all 8 commands. Internal JSON field `slug` preserved. |
| Hooks (optional) | `PostToolUse` (on Write to session JSON) for instant SSE push, `SessionStart` banner. Not load-bearing. |

## Architecture

```
┌────────────────────────────── Ubuntu 22.04 host ──────────────────────────────┐
│                                                                                │
│  ┌──────────────────┐                                                          │
│  │ Claude Code (TUI) │  user runs /css:ship --session X "idea" in a project   │
│  │                   │  writes: <project>/.claude/css/sessions/X.json          │
│  │                   │  writes: ~/.claude/css-dashboard/projects.json (auto)   │
│  └──────────────────┘                                                          │
│           ▲                                                                    │
│           │ re-spawned via `claude --print "/css:ship --session X"`           │
│           │                                                                    │
│  ┌────────┴──────────────────────────────── docker-compose stack ───────────┐ │
│  │                                                                          │ │
│  │  ┌─────────────────────────┐    ┌─────────────────────────┐             │ │
│  │  │ dashboard (FastAPI)     │    │ PostgreSQL 16            │             │ │
│  │  │  - watchdog file watcher│◄──►│  - projects              │             │ │
│  │  │  - REST + SSE           │    │  - sessions_history       │             │ │
│  │  │  - React static build   │    │  - gate_audit_log         │             │ │
│  │  └─────┬───────────────────┘    │  - daemon_runs            │             │ │
│  │        │                        └─────────────────────────┘             │ │
│  └────────┼───────────────────────────────────────────────────────────────────┘ │
│           │ writes approval events to queue dir                                │
│  ┌────────▼─────────┐  ← runs on host as systemd user service                  │
│  │ daemon-bridge    │ watches ~/.claude/css-dashboard/queue/*.json             │
│  │ (~80 LoC Python) │ on event: spawns `claude --print '/css:ship --session X'│
│  │                  │ POSTs run results back to dashboard                      │
│  └──────────────────┘                                                          │
│                                                                                │
│  ~/.claude/                                                                    │
│   ├── css/sessions/<session-id>.json   ← state of truth                        │
│   ├── css-dashboard/                                                           │
│   │     ├── config.json    ← {dashboard_enabled, claude_cli, ...}              │
│   │     ├── projects.json  ← auto-registered project paths + repo metadata    │
│   │     ├── queue/<evt-id>.json ← approval signal files (consumed by bridge)  │
│   │     ├── queue/processed/, queue/failed/                                    │
│   │     ├── runs/<run-id>.log                                                  │
│   │     └── server-info    ← daemon URL                                        │
│   └── ...                                                                       │
└────────────────────────────────────────────────────────────────────────────────┘
                                  ▲
                                  │ http://<host-ip>:7421 (LAN, no auth)
                                  │ React drag&drop → POST /api/...
                                  │ Server → React via /api/sse (SSE)
                                ┌─┴───────┐
                                │ Browser  │
                                │ (Windows)│
                                └──────────┘
```

### Why the bridge lives on the host (not in the container)

Running `claude` inside the dashboard container would require:
- Mounting host OAuth tokens / `~/.claude/.credentials`
- Mounting parent directories of every registered project so `git worktree add ../<repo>-css-<session>` resolves
- Network access (container → Anthropic API) with possibly different DNS/proxy from host
- Duplicate authentication if user re-authenticates via `claude auth login`

A tiny host-side bridge sidesteps all of this. The container is reduced to: UI + state + DB. The bridge is ~80 LoC, idempotent, restart-safe.

### Why Hooks cannot replace the daemon

Claude Code Hooks (`PreToolUse`, `PostToolUse`, etc.) only fire while a CC process is actively running. They cannot:
- Watch file system when no CC is running
- Spawn a new `claude` process
- Drive the dashboard's auto-resume

Hooks remain a *useful optional optimization* (PostToolUse on session JSON writes pushes SSE faster than file watcher debounce) but are not load-bearing for the dashboard.

## State of Truth & File Layout

| Data | Location | Owner |
|---|---|---|
| Active session state | `<project>/.claude/css/sessions/<id>.json` | CSS commands write; watcher reads |
| Phase lock | `<project>/.claude/css/locks/<id>.lock` | CSS commands. Bridge checks before resume; dashboard checks before drag approval. |
| Plan / spec / rich-spec / exec-log / verify | `<project>/.claude/css/{plans,executions,verifies}/` and `<project>/docs/` | CSS pipeline outputs; dashboard reads on artifact-accordion expand |
| Registered projects | `~/.claude/css-dashboard/projects.json` | CSS commands append on first run (flock); dashboard reads + auto-assigns color |
| Approval queue | `~/.claude/css-dashboard/queue/*.json` | Dashboard writes; bridge consumes |
| Run logs | `~/.claude/css-dashboard/runs/<run-id>.log` | Bridge writes; dashboard reads on demand |
| Dashboard config | `~/.claude/css-dashboard/config.json` | Install script writes; CSS commands + dashboard read |
| Completed-session archive | PostgreSQL `sessions_history` | Watcher inserts on pipeline completion |
| User settings (repo colors, etc.) | PostgreSQL `projects`, `settings` | Dashboard UI edits via REST |

When a session terminates (success or failure), the watcher detects `phases.pr.status` transitioning to `completed` (or any phase to `failed`), inserts an archive row into `sessions_history`, and **preserves the JSON file** (not deleted — single source of truth retained for forensic re-read).

## Data Model (PostgreSQL)

```sql
CREATE TABLE projects (
  id            SERIAL PRIMARY KEY,
  repo_root     TEXT UNIQUE NOT NULL,
  repo_name     TEXT NOT NULL,
  color         TEXT NOT NULL DEFAULT '#3b82f6',
  registered_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_seen_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE sessions_history (
  id              SERIAL PRIMARY KEY,
  project_id      INT REFERENCES projects(id) ON DELETE CASCADE,
  session_id      TEXT NOT NULL,
  idea            TEXT NOT NULL,
  started_at      TIMESTAMPTZ NOT NULL,
  finished_at     TIMESTAMPTZ,
  final_phase     TEXT NOT NULL,
  outcome         TEXT NOT NULL CHECK (outcome IN ('completed', 'failed', 'aborted')),
  pr_url          TEXT,
  phase_durations JSONB NOT NULL,
  snapshot        JSONB NOT NULL,
  archived_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (project_id, session_id, archived_at)
);

CREATE TABLE gate_audit_log (
  id              SERIAL PRIMARY KEY,
  project_id      INT REFERENCES projects(id),
  session_id      TEXT NOT NULL,
  gate            TEXT NOT NULL CHECK (gate IN ('gate2_pre_execute', 'gate3_pre_pr')),
  reached_at      TIMESTAMPTZ NOT NULL,
  approved_at     TIMESTAMPTZ,
  approval_source TEXT CHECK (approval_source IN ('dashboard_drag', 'terminal_ask')),
  resume_status   TEXT CHECK (resume_status IN ('success', 'failed', 'retrying')),
  retry_count     INT NOT NULL DEFAULT 0,
  error_message   TEXT
);

CREATE TABLE daemon_runs (
  id           SERIAL PRIMARY KEY,
  session_id   TEXT NOT NULL,
  command      TEXT NOT NULL,
  started_at   TIMESTAMPTZ NOT NULL,
  finished_at  TIMESTAMPTZ,
  exit_code    INT,
  stdout_tail  TEXT,
  stderr_tail  TEXT
);

CREATE INDEX idx_history_project_finished ON sessions_history(project_id, finished_at DESC);
CREATE INDEX idx_audit_session ON gate_audit_log(session_id, reached_at DESC);
CREATE INDEX idx_runs_session ON daemon_runs(session_id, started_at DESC);
```

## Session JSON Schema Changes

```json
{
  "slug": "pipeline-dashboard",
  "idea": "...",
  "master_flow": true,
  "repo_root": "/home/user/proj/css-claude",
  "repo_name": "css-claude",
  "current_phase": "review",
  "phases": { /* unchanged */ },
  "gates": {
    "gate2_pre_execute": {
      "state": "pending",
      "source": null,
      "reached_at": "2026-05-28T05:14:23Z",
      "approved_at": null,
      "approved_by": null
    },
    "gate3_pre_pr": { /* same shape */ }
  },
  "retry_counters": { "review": 0, "execute": 0, "verify": 0 }
}
```

- JSON field `slug` is preserved (no rename in the file itself). DB column `sessions_history.session_id` stores the same value — terminology bridge: user-facing label is "session", JSON storage field is `slug`, DB column is `session_id`.
- `repo_root` / `repo_name` populated on first session save by `/css:interview`.
- `gates.<name>` is an object (previously `null`). Legacy sessions without this shape: dashboard treats missing fields as `state: null`.

## CSS Pipeline Command Modifications

### Common: CLI flag rename — `--slug` → `--session`

Scope: all 8 command files (`interview`, `plan`, `review`, `execute`, `verify`, `document`, `pr`, `ship`).

- `argument-hint` updated
- Argument parsing updated
- Help / error / banner text updated to say "session" instead of "slug"
- Internal references to `session.slug` field preserved
- File path templates (e.g., `sessions/{slug}.json`) preserved as-is (kebab id is still a slug)

### `/css:interview` — capture repo metadata + auto-register project (+15 lines)

After creating `<project>/.claude/css/sessions/<id>.json`:

```
repo_root = git -C <project> rev-parse --show-toplevel
repo_name = basename(repo_root)
session.repo_root = repo_root
session.repo_name = repo_name
save_session()

if config.dashboard_enabled:
    flock(projects.json):
        if repo_root not in projects.entries:
            projects.entries.append({
                "repo_root": repo_root,
                "repo_name": repo_name,
                "registered_at": now_iso(),
                "color": null
            })
            write_atomic(projects.json)
```

### `/css:ship` — Gate processing with cross-path support (+40 lines)

Replace step 7 (Gate 2) and step 11 (Gate 3) with the **cross-path branching logic**:

**Resume-mode detection**: the bridge spawns `claude --print` with environment variable `CSS_DASHBOARD_RESUME=1`. The slash command checks this env var via Bash (`[ "$CSS_DASHBOARD_RESUME" = "1" ]`) to distinguish bridge-driven non-interactive resume from user-driven interactive invocation. (Falling back to `tty -s` is unreliable from inside Claude Code's Bash tool, which is itself non-TTY.)

```
# at Gate N
state = session.gates.gateN.state

if state == "approved":
    proceed
    return

is_interactive = $CSS_DASHBOARD_RESUME != "1"

if is_interactive and config.dashboard_enabled:
    answer = AskUserQuestion(
      "Gate N reached" + (" (currently pending dashboard approval — you can also approve here)" if state == "pending" else ""),
      options=[
        "Yes (approve here)",
        "Wait for dashboard",
        "Cancel"
      ]
    )
    if answer == "Yes":
        session.gates.gateN = {state: "approved", source: "terminal_ask", approved_at: now()}
        save_session()
        proceed

    elif answer == "Wait for dashboard":
        if state != "pending":
            session.gates.gateN = {state: "pending", reached_at: now()}
            save_session()
        release_lock()
        exit 0  # graceful

    else:  # Cancel
        release_lock()
        exit 0  # state preserved

elif is_interactive and not config.dashboard_enabled:
    # legacy 2-option AskUserQuestion (unchanged)
    answer = AskUserQuestion(banner, options=["Yes", "Cancel"])
    ...

else:  # non-interactive — spawned via `claude --print` by bridge with CSS_DASHBOARD_RESUME=1
    if state != "approved":
        session.gates.gateN = {state: "pending", reached_at: now()}
        save_session()
    release_lock()
    exit 0
```


### `/css:execute` and `/css:pr` (+10 lines each)

When `master_flow=true`, do not re-prompt for Gate 2 / Gate 3 (already handled in `/css:ship`). When invoked standalone with `dashboard_enabled=true` and a Gate is encountered, follow the same cross-path branching logic.

### Dashboard config file

`~/.claude/css-dashboard/config.json` is created by `install-dashboard.sh` and read by all CSS commands:

```json
{
  "dashboard_enabled": true,
  "dashboard_url": "http://localhost:7421",
  "database_url": "postgresql+asyncpg://css:****@localhost:5432/css_dashboard",
  "claude_cli": "claude",
  "queue_dir": "~/.claude/css-dashboard/queue",
  "default_palette": ["#22c55e", "#a855f7", "#3b82f6", "#f59e0b", "#ef4444", "#06b6d4", "#ec4899"]
}
```

If the file is missing, CSS commands operate in legacy mode (no dashboard interaction).

## Approval Sequence (End-to-End)

```
User drags card from review column to execute column in browser
  │
  ▼
[Browser]  POST /api/sessions/{id}/gates/gate2_pre_execute/approve
  │
  ▼
[FastAPI]  ① Check <project>/.claude/css/locks/<id>.lock — if exists → 409 Conflict
           ② Update <project>/.claude/css/sessions/<id>.json (atomic write):
                gates.gate2_pre_execute.state = "approved"
                gates.gate2_pre_execute.source = "dashboard_drag"
                gates.gate2_pre_execute.approved_at = now()
           ③ Write ~/.claude/css-dashboard/queue/<evt-id>.json:
                { slug, project_root, command: ["claude", "--print", "/css:ship --session X"],
                  callback_url, ... }
           ④ INSERT INTO gate_audit_log (...)
           ⑤ SSE broadcast: gate_approved
  │
  ▼
[bridge]   watchdog on QUEUE_DIR detects new file
           subprocess.run(command, cwd=project_root, timeout=3600)
           POST /api/internal/run-result { event: "started" }
  │
  ▼
[FastAPI]  SSE broadcast: resume_started
  │
  ▼
[claude]   Non-interactive `/css:ship --session X` re-runs:
              session.gates.gate2_pre_execute.state == "approved" → AskUserQuestion skipped
              proceed to execute → TDD → verify → document → Gate 3 → ...
           session JSON updates throughout
  │
  ▼
[watcher]  detects JSON changes → SSE broadcast: session_updated (multiple)
  │
  ▼
[bridge]   `claude --print` exits (code 0)
           POST /api/internal/run-result { event: "finished", exit_code: 0 }
           Move queue file to queue/processed/
  │
  ▼
[FastAPI]  Update daemon_runs row. If next gate now pending → no further action.
           If pipeline finished (pr.status=completed) → trigger archive to sessions_history.
```

**Failure path**: bridge POSTs `event: "failed"` with stderr tail. FastAPI updates `gate_audit_log.resume_status = "failed"`, broadcasts `resume_failed`. UI shows red indicator + retry button in Detail panel. Retry POSTs `/api/sessions/{id}/gates/{gate}/retry` which enqueues a new queue file without changing `gate.state` (still "approved").

## REST API

| Method | Path | Description |
|---|---|---|
| GET | `/api/sessions` | List all active sessions across registered projects |
| GET | `/api/sessions/{id}` | Full session detail |
| GET | `/api/sessions/{id}/artifacts` | List available artifacts (name, mtime, size) |
| GET | `/api/sessions/{id}/artifacts/{name}` | Markdown body of a named artifact (whitelist enforced) |
| POST | `/api/sessions/{id}/gates/{gate}/approve` | Approve gate via drag |
| POST | `/api/sessions/{id}/gates/{gate}/retry` | Re-enqueue resume after failure |
| GET | `/api/projects` | Registered projects with colors |
| PATCH | `/api/projects/{id}` | Update color or other settings |
| GET | `/api/history` | Paginated session archive (filters: project_id, outcome, date range) |
| GET | `/api/sse` | Server-Sent Events stream |
| POST | `/api/internal/run-result` | Bridge callback (started / finished / failed) |

### Artifact whitelist

Per session, artifacts the API will serve:
- `spec` → `session.phases.interview.artifact`
- `plan` → `session.phases.plan.artifact`
- `rich-spec-{task-id}` → from `<project>/.claude/css/plans/T{id}-spec-{session-id}-*.md`
- `exec-log` → newest `<project>/.claude/css/executions/exec-log-{session-id}-*.md`
- `verify` → newest `<project>/.claude/css/verifies/verify-{session-id}-*.md`
- `code-review`, `security-review` → linked from verify report
- `docs` → `<project>/docs/{session-id}/README.md` (after `/css:document` completes)

Path resolution: each name maps to a file resolved within `session.repo_root`. Result of `Path(file).resolve()` must start with `repo_root.resolve()`. Otherwise → 403.

### SSE Event Types

```
event: session_updated     data: { session_id, phase, gates, mtime }
event: gate_reached        data: { session_id, gate, reached_at }
event: gate_approved       data: { session_id, gate, source }
event: resume_started      data: { session_id, run_id, command }
event: resume_failed       data: { session_id, gate, error, retry_count }
event: session_completed   data: { session_id, pr_url, outcome, durations }
event: project_registered  data: { project_id, repo_name, color }
event: connection_health   data: { db, watcher, bridge }   (every 30s heartbeat)
```

## Frontend Components

```
<App>
 ├─ <TopBar>
 │   ├─ <Title>            "CSS Pipeline Dashboard · N active"
 │   ├─ <RepoLegend>       (chips, click to filter)
 │   ├─ <HistoryLink>      → /history
 │   └─ <SettingsButton>   → opens <SettingsModal>
 ├─ <KanbanBoard>          (7 columns)
 │   └─ <Column stage gateAfter?> ← dashed border + ⚠ label when gate pending
 │       └─ <SessionCard× n>
 ├─ <DetailSlideOver>      (right slide-in 320px, GitHub Issues style)
 │   ├─ <SessionHeader>    (color block + id + close)
 │   ├─ <StatusChips>      (repo, phase, gate state)
 │   ├─ <IdeaSection>
 │   ├─ <Timeline>         (per-phase status + duration)
 │   ├─ <ArtifactAccordion>← lazy fetch on expand
 │   └─ <ActionRow>        (Retry / Open in editor)
 ├─ <SettingsModal>        (per-project color picker)
 ├─ <HistoryView route="/history">
 ├─ <ToastContainer>
 └─ <SSEConnection />      (headless; updates Zustand store)
```

### SessionCard visual

- Left 3px stripe in `project.color`
- Title: `session_id` bold
- Subtitle: `repo_name` muted + elapsed (`14m`)
- States:
  - `pending-gate`: 2px amber outline + small "⚠ drag right to approve" hint
  - `resume-failed`: red dot top-right + 1s shake animation
  - `selected`: 2px primary outline (when detail panel open for this card)

### Drag rules (dnd-kit)

| From column | To column | Action |
|---|---|---|
| `review` | `execute` | POST approve gate2_pre_execute (only if card's gate2 is pending) |
| `document` | `pr` | POST approve gate3_pre_pr (only if card's gate3 is pending) |
| any other pair | — | Drop rejected, snap-back, toast "Gates 외 이동은 불가" |

Optimistic UI: card moves on drop, spinner overlay until SSE `resume_started` arrives. On `session_updated` showing next phase, badge clears. On `resume_failed`, card returns to source column with red indicator.

### Artifact accordion

- Each artifact is a collapsed row in the Detail panel
- Click → fetch via `GET /api/sessions/{id}/artifacts/{name}` → render with `react-markdown` + `rehype-highlight` (code) + `rehype-sanitize` (XSS guard)
- Cached in Zustand keyed by `(session_id, name, mtime)`; refetch on mtime change broadcast by SSE

### History view (`/history`)

- Paginated table: finished_at / repo (colored chip) / session_id / outcome / total duration / PR URL
- Filters: project, outcome, date range
- Row click → DetailSlideOver opens (re-using same component) with `source="history"` (no Retry action)

### Settings modal

- Table of `projects`: repo_name | repo_root | current color (color picker) | registered_at
- Color change → PATCH `/api/projects/{id}` → SSE broadcast → all clients refresh palette
- "Auto-assign colors" button (uses `config.default_palette`)

### Accessibility / keyboard

- Tab to focus card; Enter to open detail; Esc to close
- Drag alternative: focused pending-gate card + Space → "Approve Gate" inline button
- All interactive elements have `aria-label`

## Bridge Daemon

`~/.claude/css-dashboard/bin/bridge.py` (~80 LoC). Runs on host as systemd user service.

```python
# pseudocode
import json, subprocess, requests, time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

HOME = Path.home()
QUEUE = HOME / ".claude/css-dashboard/queue"
PROCESSED = QUEUE / "processed"
FAILED = QUEUE / "failed"
RUNS = HOME / ".claude/css-dashboard/runs"

def process_event(path: Path):
    evt = json.loads(path.read_text())
    sid = evt["session_id"]
    pr  = evt["project_root"]
    cmd = evt["command"]                  # list of str — server-constructed, validated
    log = RUNS / f"{evt['id']}.log"

    requests.post(evt["callback_url"], json={"id": evt["id"], "session_id": sid, "event": "started"})

    try:
        env = {**os.environ, "CSS_DASHBOARD_RESUME": "1"}
        with open(log, "w") as f:
            proc = subprocess.run(cmd, cwd=pr, timeout=3600, env=env, stdout=f, stderr=subprocess.STDOUT)
        result = {"id": evt["id"], "session_id": sid, "event": "finished",
                  "exit_code": proc.returncode, "log_path": str(log)}
        requests.post(evt["callback_url"], json=result)
        path.rename(PROCESSED / path.name)
    except Exception as e:
        requests.post(evt["callback_url"], json={
            "id": evt["id"], "session_id": sid, "event": "failed", "error": str(e)
        })
        path.rename(FAILED / path.name)

class Handler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith(".json"): return
        process_event(Path(event.src_path))

def main():
    for d in (QUEUE, PROCESSED, FAILED, RUNS): d.mkdir(parents=True, exist_ok=True)
    for p in QUEUE.glob("*.json"): process_event(p)        # re-process on startup
    obs = Observer(); obs.schedule(Handler(), str(QUEUE), recursive=False); obs.start()
    while True: time.sleep(60)

if __name__ == "__main__": main()
```

systemd unit (`~/.config/systemd/user/css-dashboard-bridge.service`):

```ini
[Unit]
Description=CSS Dashboard Bridge
After=network.target

[Service]
ExecStart=/usr/bin/python3 %h/.claude/css-dashboard/bin/bridge.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

## Testing Strategy

Target: ≥85% line coverage (per CSS pipeline standard).

| Layer | Tools | Scope |
|---|---|---|
| Backend unit | `pytest`, `pytest-asyncio` | Routers, services, file-watcher event handlers (mocked FS) |
| Backend integration | `httpx.AsyncClient`, `testcontainers-postgres` | Real PostgreSQL container, full HTTP stack |
| File watcher | `tmp_path` + synthetic JSON writes | watchdog → SSE event chain |
| Bridge | `subprocess.run` mock + queue fixtures | Queue consumption → callback POST behavior |
| Frontend unit | `vitest`, RTL, `msw` | Components, store transitions |
| Frontend drag | `@dnd-kit` sensors mocked + RTL `fireEvent` | Valid/invalid drop handling, optimistic UI |
| E2E | `Playwright` | Synthetic session JSON → drag → mocked bridge → SSE → UI |
| CSS commands | Golden tests in `tests/fixtures/toy-typescript/` (existing pattern) | Rename, cross-path gate branching, repo capture |

E2E mocks the actual `claude` invocation with a dummy script that updates the session JSON, so the full pipeline can be exercised without API costs.

## Error Handling

| Scenario | Response |
|---|---|
| Corrupted session JSON | Watcher logs ERROR, skips event. Card shows "⚠ corrupted" with last-good snapshot. |
| Legacy session (no `repo_root` / no `gates` object) | Backward-compatible defaults; card shows "(unknown repo)" until next `/css:*` run repopulates. |
| PostgreSQL down | Degraded mode: active sessions still shown (file watch independent of DB). History + settings disabled. Banner: "DB unreachable". |
| Bridge process dies | systemd `Restart=on-failure`. Queue files persist; on restart, process backlog idempotently. |
| Stale lock (CSS crash) | Lock owner PID dead AND session JSON mtime > 5 min → "stale" indicator. Detail panel exposes "force unlock" button. |
| User closes tab mid-drag | Browser optimistic state lost; backend unchanged (POST never fired). No-op. |
| `claude` CLI not in PATH | Bridge captures `FileNotFoundError`, POSTs `resume_failed` with explicit message. UI surfaces clear remedy. |
| LAN disconnect | SSE auto-reconnect (1s/2s/4s/8s backoff). Top banner "재연결 중...". |
| Concurrent projects.json append | `flock` advisory lock serializes. |
| Bridge dies mid-run | Next startup re-processes queue file. Dashboard dedups callbacks via `run_id`. |
| Gate state stuck (approved but phase not advancing) | Detail panel exposes "force advance" / "reset gate" admin actions. |
| Multi-client drag race | First request acquires DB row-level lock + checks gate state; second returns 409. |

## Security

LAN trust assumption (no auth) but the following are still required:

| Concern | Mitigation |
|---|---|
| Path traversal in artifact endpoint | `Path.resolve()` then prefix-check against `session.repo_root`. Whitelist enforced on artifact name. |
| Read-only artifact endpoint | GET only. Whitelist of names. No user-supplied paths in request body. |
| SQL injection | 100% parameterized via SQLAlchemy 2.x async + asyncpg. |
| Command injection in bridge | `cmd` is a list constructed server-side from a fixed template. `session_id` validated `^[a-z0-9-]{1,64}$` before substitution. |
| XSS in markdown | `react-markdown` + `rehype-sanitize` strips raw HTML. `rehype-highlight` is static. |
| DB credentials exposure | `.env` (gitignored) → docker-compose env injection. No hardcoded secrets in compose YAML. |
| File permissions | `~/.claude/css-dashboard/` 700, queue/logs 600. Install script enforces. |
| CSRF | All mutating endpoints check `Origin` header against allowed origins (configurable). SameSite cookies. |

## Deployment

### File structure (new in repo)

```
css-claude/
├── commands/                         # MODIFIED — all 8 (rename + 4 gate-aware)
├── agents/                            # UNCHANGED
├── config/                            # UNCHANGED
├── scripts/
│   ├── install.{ps1,sh}              # existing — add `--with-dashboard` flag
│   ├── install-dashboard.sh           # NEW — Ubuntu
│   └── uninstall-dashboard.sh         # NEW
├── dashboard/                          # NEW (entire directory)
│   ├── README.md
│   ├── docker-compose.yml
│   ├── Dockerfile                     # multi-stage: node build → python runtime
│   ├── .env.example
│   ├── pyproject.toml
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/0001_initial.py
│   ├── backend/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── models.py
│   │   ├── watcher.py
│   │   ├── sse.py
│   │   ├── routers/
│   │   │   ├── sessions.py
│   │   │   ├── projects.py
│   │   │   ├── gates.py
│   │   │   ├── artifacts.py
│   │   │   ├── history.py
│   │   │   └── internal.py
│   │   ├── services/
│   │   │   ├── queue_writer.py
│   │   │   ├── session_reader.py
│   │   │   ├── archive.py
│   │   │   └── project_registry.py
│   │   └── tests/
│   ├── frontend/
│   │   ├── package.json
│   │   ├── vite.config.ts
│   │   ├── tailwind.config.ts
│   │   ├── tsconfig.json
│   │   ├── src/
│   │   │   ├── App.tsx
│   │   │   ├── main.tsx
│   │   │   ├── components/
│   │   │   │   ├── TopBar.tsx
│   │   │   │   ├── KanbanBoard.tsx
│   │   │   │   ├── Column.tsx
│   │   │   │   ├── SessionCard.tsx
│   │   │   │   ├── DetailSlideOver.tsx
│   │   │   │   ├── ArtifactAccordion.tsx
│   │   │   │   ├── SettingsModal.tsx
│   │   │   │   ├── HistoryView.tsx
│   │   │   │   └── ToastContainer.tsx
│   │   │   ├── stores/
│   │   │   │   ├── sessionsStore.ts
│   │   │   │   ├── projectsStore.ts
│   │   │   │   └── uiStore.ts
│   │   │   ├── api/
│   │   │   │   ├── client.ts
│   │   │   │   └── sse.ts
│   │   │   └── types.ts
│   │   └── tests/
│   └── bridge/
│       ├── bridge.py
│       ├── css-dashboard-bridge.service
│       └── tests/
├── docs/
│   ├── superpowers/specs/2026-05-28-pipeline-dashboard-design.md  # THIS FILE
│   ├── superpowers/plans/2026-05-28-pipeline-dashboard.md         # (output of /css:plan)
│   └── pipeline-dashboard/                                         # (output of /css:document)
└── tests/                              # existing fixtures + new dashboard-mode cases
```

### docker-compose.yml (skeleton)

```yaml
services:
  dashboard:
    build: .
    image: css-dashboard:latest
    ports: ["7421:7421"]
    environment:
      - DATABASE_URL=postgresql+asyncpg://css:${DB_PASSWORD}@postgres:5432/css_dashboard
    volumes:
      - ${HOME}/.claude:/host/.claude:rw
      - ${HOME}/projects:/host/projects:ro
    depends_on: [postgres]
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=css
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=css_dashboard
    volumes:
      - css-dashboard-pgdata:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  css-dashboard-pgdata:
```

### Install / upgrade / uninstall

**install-dashboard.sh** (Ubuntu only in v0.1):

1. Verify Docker + docker-compose available
2. Create `~/.claude/css-dashboard/` (perm 700)
3. Generate random DB password → `.env`
4. `docker compose up -d --build`
5. Run alembic migrations
6. Place `bridge.py` + systemd unit; `systemctl --user enable --now css-dashboard-bridge`
7. Write `~/.claude/css-dashboard/config.json` with `dashboard_enabled: true`
8. Print: `Dashboard up at http://<host-ip>:7421`

**uninstall-dashboard.sh**:

1. `systemctl --user disable --now css-dashboard-bridge`
2. `docker compose down [-v]` (volume deletion confirmation prompt)
3. Set `config.json:dashboard_enabled = false` (CSS reverts to legacy mode)
4. Optionally remove `~/.claude/css-dashboard/` (with confirmation)

**Upgrade**: `git pull && bash scripts/install-dashboard.sh --upgrade` — rebuild image, run new migrations.

## Observability

- Backend logs: `structlog` JSON to stdout (captured by `docker compose logs dashboard`)
- Bridge logs: stdout → systemd journal (`journalctl --user -u css-dashboard-bridge`)
- Audit trail: every gate-reached, gate-approved, resume-started, resume-failed, archive event writes a row to `gate_audit_log` or `daemon_runs`
- UI: connection health indicator in TopBar (DB / watcher / bridge — three colored dots)

## Acceptance Criteria

A v0.1 implementation is considered complete when:

1. **Multi-session, multi-project Kanban renders**. With ≥2 active sessions across ≥2 registered repos, dashboard shows correct cards in correct columns with correct repo color stripes.
2. **Card click opens slide-out detail**. Timeline, status chips, idea, artifact accordion (collapsed by default) all render.
3. **Artifact accordion lazy-fetches**. Expanding `spec` fetches and renders markdown; `rich-spec-Txx` fetches the per-task file.
4. **Drag approval works for Gate 2 and Gate 3**. Dragging a pending card from `review`→`execute` (or `document`→`pr`) writes approval to session JSON, enqueues bridge event, and the bridge successfully re-spawns `claude --print '/css:ship --session X'`, which then advances the pipeline.
5. **Cross-path approval**. The same session can be approved at Gate 2 via dashboard drag and Gate 3 via terminal `AskUserQuestion`, in either order.
6. **Lock-based mutual exclusion**. While CSS holds the phase lock (terminal AskUserQuestion in flight), dashboard drag returns 409 Conflict with a clear message.
7. **Drag rule enforcement**. Non-Gate column moves snap back with a toast.
8. **Settings: per-repo color**. Changing a project's color via Settings modal updates all that project's cards (active and history) immediately via SSE.
9. **History view**. A completed pipeline appears in `/history` with phase durations, PR URL, and clickable detail.
10. **Failure recovery**. If bridge invocation fails (`claude` not found / non-zero exit), card shows red indicator, Detail panel exposes Retry, retry re-enqueues and succeeds.
11. **`--slug` → `--session` rename**. All 8 commands accept `--session`; help text and error messages use "session" consistently. Internal JSON `slug` field preserved.
12. **Coverage ≥85%** in backend, frontend, and bridge test suites combined.
13. **install-dashboard.sh from a clean Ubuntu 22.04 VM** stands up the full stack with one command (after manual DB password confirm).
14. **No regression in legacy mode**. With `dashboard_enabled=false`, `/css:ship` behaves identically to current behavior (two-option AskUserQuestion).

## Risks & Open Questions

| Risk | Mitigation |
|---|---|
| `claude --print` non-interactive behavior may not match interactive (output format, hooks fired) | Smoke-test during /css:plan stage; document required Claude Code version |
| Hosts other than Ubuntu (macOS / WSL) | v0.1 explicitly Ubuntu-only. Note in install script. |
| Large session JSON parse cost (very long runs) | JSON stays small (state + phase pointers only). Logs are external. Benchmark in test fixtures. |
| Watchdog missing events on network/SMB-mounted filesystems | Document filesystem requirement: local ext4/btrfs/xfs only |
| User-installed Python versions on host | Bridge needs Python 3.10+. Install script verifies. |
| Container's view of project paths may differ if `$HOME` mapping is unusual | Document conventional setup; allow custom volume config |
| SSE proxying through reverse proxies | Out of scope (LAN direct connection assumed) |

## References

- Parent design: [`docs/specs/2026-05-27-css-pipeline-design.md`](../../specs/2026-05-27-css-pipeline-design.md)
- Project README: [`README.md`](../../../README.md)
- Visual brainstorming mockups: `.superpowers/brainstorm/851-1779912821/content/dashboard-layout*.html` (local only)
