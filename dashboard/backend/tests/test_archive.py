"""T4.14 RED — archive_completed_session inserts SessionHistory row into DB."""
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from backend.models import Project, SessionHistory
from backend.services.archive import archive_completed_session
from backend.services.session_reader import ParsedSession


@pytest.mark.asyncio
async def test_archive_inserts_history_row(pg_engine):
    sm = async_sessionmaker(pg_engine, expire_on_commit=False)
    async with sm() as s:
        p = Project(repo_root="/r", repo_name="r", color="#fff")
        s.add(p)
        await s.commit()
        await s.refresh(p)

    parsed = ParsedSession(
        slug="feat-x",
        idea="i",
        repo_root="/r",
        repo_name="r",
        current_phase="pr",
        phases={
            "interview": {"status": "completed", "completed_at": "2026-01-01T00:00:00Z"},
            "pr":        {"status": "completed", "artifact": "https://gh.com/pr/1"},
        },
        gates={},
        master_flow=True,
        file_path=Path("/tmp/x.json"),
        mtime=0,
    )

    async with sm() as s:
        row = await archive_completed_session(s, parsed)
        await s.commit()
        assert row.outcome == "completed"
        assert row.pr_url == "https://gh.com/pr/1"

    async with sm() as s:
        rows = (
            await s.execute(
                select(SessionHistory).where(SessionHistory.session_id == "feat-x")
            )
        ).scalars().all()
        assert len(rows) == 1
