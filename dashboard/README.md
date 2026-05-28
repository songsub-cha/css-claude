# CSS Pipeline Dashboard

Local-hosted dashboard for visualizing CSS pipeline progress across multiple projects, with drag-and-drop Gate approval.

See [design spec](../docs/superpowers/specs/2026-05-28-pipeline-dashboard-design.md) and [implementation plan](../docs/superpowers/plans/2026-05-28-pipeline-dashboard.md) for full design.

## Quick start (Ubuntu 22.04)

```bash
bash scripts/install-dashboard.sh
```

Open `http://<host-ip>:7421` from any LAN browser.

## Install / Uninstall

### Install

```bash
# From the repo root:
bash scripts/install-dashboard.sh
```

The script will:
1. Create `~/.claude/css-dashboard/` directory structure
2. Copy the bridge daemon to `~/.claude/css-dashboard/bin/bridge.py`
3. Install and enable the systemd user service `css-dashboard-bridge.service`
4. Generate a random `DB_PASSWORD` and write `dashboard/.env`
5. Run `docker compose up -d --build` to start the stack
6. Run `alembic upgrade head` inside the container to apply DB migrations

### Uninstall

```bash
bash scripts/uninstall-dashboard.sh
```

You will be prompted whether to delete the PostgreSQL data volume (deletes all session history).

## Architecture

```
Browser (any LAN device)
    │ HTTP :7421
    ▼
[Nginx / Uvicorn] ← React static build (served from /static)
    │
    ├── FastAPI routers (/api/*)
    │       ├── GET  /api/sessions          — active session list
    │       ├── GET  /api/sessions/{slug}   — session detail + gate state
    │       ├── POST /api/sessions/{slug}/gates/{gate}/approve — Gate drag
    │       ├── GET  /api/sse               — Server-Sent Events stream
    │       ├── GET  /api/history           — completed session log
    │       └── PATCH /api/projects/{id}   — per-project color
    │
    ├── SQLAlchemy async → PostgreSQL 16
    │
    └── SessionWatcher (watchdog) → reads <project>/.claude/css/sessions/*.json

[Bridge daemon] (host systemd user service)
    ├── Polls ~/.claude/css-dashboard/queue/ for approval files
    └── Spawns: claude --print '/css:ship --session <slug>' (env CSS_DASHBOARD_RESUME=1)
```

## Drag-and-drop Gate approval

The Kanban board supports two Gate transitions via drag:

| Drag direction | Gate triggered |
|----------------|---------------|
| review → execute | Gate 2 (pre-execute approval) |
| document → pr | Gate 3 (pre-PR approval) |

Dragging a card to any non-Gate column is rejected with a toast warning. Only cards in `pending` gate state can be dragged across the gate boundary.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Dashboard not reachable at :7421 | Docker stack not running | `cd dashboard && docker compose up -d` |
| Cards not updating | Bridge daemon not running | `systemctl --user status css-dashboard-bridge` |
| Gate drag has no effect | Session gate state not `pending` | Check `~/.claude/css/sessions/<slug>.json` |
| Alembic errors on startup | Schema out of date | `docker compose exec dashboard alembic upgrade head` |
| `DB_PASSWORD` not set | `.env` missing | Re-run `install-dashboard.sh` or copy from `.env.example` |

## Tech stack

- Backend: FastAPI + SQLAlchemy async + watchdog
- Frontend: React 19 + Vite + TailwindCSS v4 + dnd-kit
- Database: PostgreSQL 16
- Orchestration: docker-compose
- Bridge daemon: Python systemd user service (runs on host)
- Tests: pytest + pytest-asyncio + testcontainers-postgres (backend), vitest + msw + @testing-library/react (frontend), Playwright (E2E)
