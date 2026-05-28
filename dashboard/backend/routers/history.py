"""T4.16 — GET /api/history: paginated, filterable archive query."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.deps import get_db_session
from backend.models import SessionHistory

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("")
async def list_history(
    project_id: Optional[int] = None,
    outcome: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session),
):
    stmt = select(SessionHistory).order_by(SessionHistory.finished_at.desc())
    cnt_stmt = select(func.count()).select_from(SessionHistory)

    if project_id is not None:
        stmt = stmt.where(SessionHistory.project_id == project_id)
        cnt_stmt = cnt_stmt.where(SessionHistory.project_id == project_id)
    if outcome:
        stmt = stmt.where(SessionHistory.outcome == outcome)
        cnt_stmt = cnt_stmt.where(SessionHistory.outcome == outcome)

    stmt = stmt.limit(limit).offset(offset)

    rows = (await db.execute(stmt)).scalars().all()
    total = (await db.execute(cnt_stmt)).scalar_one()

    return {
        "total": total,
        "items": [
            {
                "id": r.id,
                "project_id": r.project_id,
                "session_id": r.session_id,
                "idea": r.idea,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "finished_at": r.finished_at.isoformat() if r.finished_at else None,
                "outcome": r.outcome,
                "pr_url": r.pr_url,
                "phase_durations": r.phase_durations,
            }
            for r in rows
        ],
    }
