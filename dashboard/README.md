# CSS Pipeline Dashboard

Local-hosted dashboard for visualizing CSS pipeline progress across multiple projects, with drag-and-drop Gate approval.

See [design spec](../docs/superpowers/specs/2026-05-28-pipeline-dashboard-design.md) for full design.

## Quick start (Ubuntu 22.04)

```bash
bash scripts/install-dashboard.sh
```

Open `http://<host-ip>:7421` from any LAN browser.

## Tech stack

- Backend: FastAPI + SQLAlchemy async + watchdog
- Frontend: React 19 + Vite + TailwindCSS v4 + dnd-kit
- Database: PostgreSQL 16
- Orchestration: docker-compose
- Bridge daemon: Python systemd user service (runs on host)
