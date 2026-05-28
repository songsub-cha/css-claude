"""T4.16 RED — GET /api/history with pagination and filters."""
from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from backend.main import app
from backend.models import Project, SessionHistory


@pytest.mark.asyncio
async def test_history_pagination(pg_engine):
    sm = async_sessionmaker(pg_engine, expire_on_commit=False)
    async with sm() as s:
        p = Project(repo_root="/h", repo_name="h")
        s.add(p)
        await s.commit()
        await s.refresh(p)
        for i in range(25):
            s.add(
                SessionHistory(
                    project_id=p.id,
                    session_id=f"s{i}",
                    idea="i",
                    started_at=datetime.now(timezone.utc),
                    final_phase="pr",
                    outcome="completed",
                    phase_durations={},
                    snapshot={},
                )
            )
        await s.commit()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        r = await c.get("/api/history?limit=10")

    assert r.status_code == 200
    j = r.json()
    assert len(j["items"]) == 10
    assert j["total"] >= 25
