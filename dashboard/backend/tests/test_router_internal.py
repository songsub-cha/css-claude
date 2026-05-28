"""T4.15 RED — POST /api/internal/run-result inserts DaemonRun and updates exit code."""
from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from backend.main import app
from backend.models import DaemonRun


@pytest.mark.asyncio
async def test_run_started_inserts(pg_engine):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        r = await c.post(
            "/api/internal/run-result",
            json={"id": "evt-abc", "session_id": "feat-x", "event": "started"},
            headers={"Origin": "http://test"},
        )
    assert r.status_code == 204

    sm = async_sessionmaker(pg_engine, expire_on_commit=False)
    async with sm() as s:
        rows = (
            await s.execute(
                select(DaemonRun).where(DaemonRun.session_id == "feat-x")
            )
        ).scalars().all()
        assert len(rows) == 1
        assert rows[0].exit_code is None


@pytest.mark.asyncio
async def test_run_finished_updates_exit_code(pg_engine):
    sm = async_sessionmaker(pg_engine, expire_on_commit=False)
    async with sm() as s:
        s.add(
            DaemonRun(
                session_id="feat-y",
                command="claude --print",
                started_at=datetime.now(timezone.utc),
            )
        )
        await s.commit()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        r = await c.post(
            "/api/internal/run-result",
            json={"id": "evt-y", "session_id": "feat-y", "event": "finished", "exit_code": 0},
            headers={"Origin": "http://test"},
        )
    assert r.status_code == 204

    async with sm() as s:
        rows = (
            await s.execute(
                select(DaemonRun).where(DaemonRun.session_id == "feat-y")
            )
        ).scalars().all()
        assert rows[-1].exit_code == 0
