"""T4.10 — POST /api/sessions/{slug}/gates/{gate}/approve + /retry.

Features:
- 400 if gate name is not in ALLOWED_GATES
- 404 if session not found
- 409 if <repo>/.claude/css/locks/<slug>.lock exists (pipeline busy)
- Atomically rewrites session JSON gate state to "approved"
- Enqueues resume event via queue_writer
- F1: publishes gate_approved SSE event via broker
- Inserts GateAuditLog row
- /retry: re-enqueues without changing gate state
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import Settings
from backend.deps import get_db_session
from backend.models import GateAuditLog
from backend.services.project_registry import read_projects
from backend.services.queue_writer import enqueue_resume
from backend.services.session_reader import list_sessions_for_project
from backend.sse import SSEEvent, broker

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sessions", tags=["gates"])

ALLOWED_GATES = {"gate2_pre_execute", "gate3_pre_pr"}


def _settings() -> Settings:
    return Settings()


def _find_session(slug: str, settings: Settings):
    """Return (ParsedSession, repo_root_path) or raise HTTPException 404."""
    for proj in read_projects(settings.projects_json):
        for sess in list_sessions_for_project(Path(proj.repo_root)):
            if sess.slug == slug:
                return sess, Path(proj.repo_root)
    raise HTTPException(404, f"session {slug!r} not found")


def _check_lock(repo_root: Path, slug: str) -> None:
    """Raise 409 if a lock file exists for this session."""
    lock_path = repo_root / ".claude" / "css" / "locks" / f"{slug}.lock"
    if lock_path.exists():
        raise HTTPException(409, f"session {slug!r} is locked — pipeline is busy")


def _atomic_write_session(session_file: Path, data: dict) -> None:
    """Write session JSON atomically via tmp→replace."""
    tmp = session_file.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.replace(tmp, session_file)


@router.post("/{slug}/gates/{gate}/approve")
async def approve_gate(
    slug: str,
    gate: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Approve a gate: update session JSON, enqueue resume, emit SSE, insert audit log."""
    if gate not in ALLOWED_GATES:
        raise HTTPException(400, f"unknown gate {gate!r}; allowed: {sorted(ALLOWED_GATES)}")

    s = _settings()
    sess, repo_root = _find_session(slug, s)

    _check_lock(repo_root, slug)

    # Load current session JSON for atomic rewrite
    session_file = repo_root / ".claude" / "css" / "sessions" / f"{slug}.json"
    session_data = json.loads(session_file.read_text(encoding="utf-8"))

    now = datetime.now(timezone.utc).isoformat()
    gate_entry = session_data.get("gates", {}).get(gate) or {}
    reached_at = gate_entry.get("reached_at") or now

    # Update gate state
    if "gates" not in session_data:
        session_data["gates"] = {}
    session_data["gates"][gate] = {
        "state": "approved",
        "source": "dashboard_drag",
        "reached_at": reached_at,
        "approved_at": now,
        "approved_by": "dashboard",
    }

    _atomic_write_session(session_file, session_data)

    # Determine queue dir from env override (test injection) or settings
    queue_dir_env = os.environ.get("QUEUE_DIR")
    queue_dir = Path(queue_dir_env) if queue_dir_env else s.queue_dir

    evt_id = enqueue_resume(
        queue_dir=queue_dir,
        session_id=slug,
        project_root=str(repo_root),
        callback_url="http://localhost:7421/api/internal/run-result",
    )

    # F1: broadcast gate_approved SSE event
    await broker.publish(
        SSEEvent(
            "gate_approved",
            {
                "session_id": slug,
                "gate": gate,
                "source": "dashboard_drag",
            },
        )
    )

    # Insert GateAuditLog
    audit = GateAuditLog(
        session_id=slug,
        gate=gate,
        reached_at=datetime.fromisoformat(reached_at),
        approved_at=datetime.fromisoformat(now),
        approval_source="dashboard_drag",
        resume_status="retrying",
    )
    db.add(audit)
    await db.commit()

    return {"approved": True, "event_id": evt_id, "gate": gate}


@router.post("/{slug}/gates/{gate}/retry")
async def retry_gate(
    slug: str,
    gate: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Re-enqueue a resume event without changing the gate state."""
    if gate not in ALLOWED_GATES:
        raise HTTPException(400, f"unknown gate {gate!r}; allowed: {sorted(ALLOWED_GATES)}")

    s = _settings()
    sess, repo_root = _find_session(slug, s)

    _check_lock(repo_root, slug)

    queue_dir_env = os.environ.get("QUEUE_DIR")
    queue_dir = Path(queue_dir_env) if queue_dir_env else s.queue_dir

    evt_id = enqueue_resume(
        queue_dir=queue_dir,
        session_id=slug,
        project_root=str(repo_root),
        callback_url="http://localhost:7421/api/internal/run-result",
    )

    # Update retry count in audit log (best effort)
    try:
        audit = GateAuditLog(
            session_id=slug,
            gate=gate,
            reached_at=datetime.now(timezone.utc),
            resume_status="retrying",
        )
        db.add(audit)
        await db.commit()
    except Exception as e:
        log.warning("gate retry audit insert failed: %s", e)

    return {"retried": True, "event_id": evt_id, "gate": gate}
