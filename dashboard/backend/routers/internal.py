"""T4.15 — Bridge callback router: POST /api/internal/run-result.

Handles start/finish/fail events from the host-side bridge daemon.
On 'started': inserts a DaemonRun row + publishes resume_started SSE.
On 'finished'/'failed': updates latest run row + publishes session_completed (F1) or resume_failed.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.deps import get_db_session
from backend.models import DaemonRun
from backend.sse import SSEEvent, broker

router = APIRouter(prefix="/api/internal", tags=["internal"])


class RunResult(BaseModel):
    id: str
    session_id: str
    event: Literal["started", "finished", "failed"]
    exit_code: Optional[int] = None
    error: Optional[str] = None
    log_path: Optional[str] = None


@router.post("/run-result", status_code=204)
async def run_result(
    body: RunResult,
    db: AsyncSession = Depends(get_db_session),
) -> None:
    now = datetime.now(timezone.utc)

    if body.event == "started":
        db.add(
            DaemonRun(
                session_id=body.session_id,
                command="claude --print",
                started_at=now,
            )
        )
        await db.commit()
        await broker.publish(
            SSEEvent(
                name="resume_started",
                data={"session_id": body.session_id, "run_id": body.id},
            )
        )
    else:
        # Locate the latest DaemonRun for this session and update it.
        row = (
            await db.execute(
                select(DaemonRun)
                .where(DaemonRun.session_id == body.session_id)
                .order_by(DaemonRun.id.desc())
                .limit(1)
            )
        ).scalar_one_or_none()

        if row is not None:
            row.finished_at = now
            row.exit_code = body.exit_code if body.exit_code is not None else 0
            row.stderr_tail = (body.error or "")[:2000]
            await db.commit()

        # Publish SSE: session_completed (F1) on clean finish, resume_failed otherwise.
        is_clean = body.event == "finished" and (body.exit_code or 0) == 0
        evt_name = "session_completed" if is_clean else "resume_failed"
        await broker.publish(
            SSEEvent(
                name=evt_name,
                data={"session_id": body.session_id, "error": body.error},
            )
        )
