"""T4.14 — Archive a completed CSS session to the sessions_history table."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Project, SessionHistory
from backend.services.session_reader import ParsedSession


async def archive_completed_session(
    db: AsyncSession, parsed: ParsedSession
) -> SessionHistory:
    """Insert (or create project + insert) a SessionHistory row.

    Returns the new row (already flushed, caller must commit).
    """
    # Look up project by repo_root; create it if absent.
    proj = (
        await db.execute(
            select(Project).where(Project.repo_root == parsed.repo_root)
        )
    ).scalar_one_or_none()

    if proj is None:
        proj = Project(repo_root=parsed.repo_root, repo_name=parsed.repo_name)
        db.add(proj)
        await db.flush()  # populate proj.id

    # Derive outcome from PR phase status.
    outcome = (
        "completed"
        if parsed.phases.get("pr", {}).get("status") == "completed"
        else "failed"
    )
    pr_url = (
        parsed.phases.get("pr", {}).get("artifact")
        if outcome == "completed"
        else None
    )

    # started_at from interview completed_at, fallback to now.
    started_at_str = (
        parsed.phases.get("interview", {}).get("completed_at")
        or datetime.now(timezone.utc).isoformat()
    )
    started_at = datetime.fromisoformat(started_at_str.replace("Z", "+00:00"))

    # Build per-phase duration map.
    phases = ["interview", "plan", "review", "execute", "verify", "document", "pr"]
    durations = {
        ph: parsed.phases.get(ph, {}).get("duration_seconds", 0)
        for ph in phases
    }

    row = SessionHistory(
        project_id=proj.id,
        session_id=parsed.slug,
        idea=parsed.idea,
        started_at=started_at,
        finished_at=datetime.now(timezone.utc),
        final_phase=parsed.current_phase,
        outcome=outcome,
        pr_url=pr_url,
        phase_durations=durations,
        snapshot={
            "slug": parsed.slug,
            "phases": parsed.phases,
            "gates": parsed.gates,
        },
    )
    db.add(row)
    await db.flush()
    return row
