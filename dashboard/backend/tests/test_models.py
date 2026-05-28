"""T3.2: SQLAlchemy ORM model tests — native PG via TEST_DATABASE_URL.

Adapted from rich spec RED scaffold: testcontainers -> TEST_DATABASE_URL (no Docker on Windows dev).
Uses shared pg_engine fixture from conftest.py (module-scoped, single event loop).
"""
import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncEngine

from backend.models import Project, SessionHistory, GateAuditLog, DaemonRun


async def test_project_crud(pg_engine: AsyncEngine):
    sm = async_sessionmaker(pg_engine, expire_on_commit=False)
    async with sm() as s:
        p = Project(repo_root="/home/user/proj", repo_name="proj", color="#22c55e")
        s.add(p)
        await s.commit()
        await s.refresh(p)
        assert p.id is not None
        assert p.color == "#22c55e"
        assert p.repo_name == "proj"


async def test_session_history_jsonb(pg_engine: AsyncEngine):
    sm = async_sessionmaker(pg_engine, expire_on_commit=False)
    async with sm() as s:
        p = Project(repo_root="/home/user/proj2", repo_name="proj2")
        s.add(p)
        await s.commit()
        await s.refresh(p)

        h = SessionHistory(
            project_id=p.id,
            session_id="feat-x",
            idea="x",
            started_at=datetime.now(timezone.utc),
            final_phase="pr",
            outcome="completed",
            phase_durations={"interview": 720},
            snapshot={"slug": "feat-x"},
        )
        s.add(h)
        await s.commit()
        await s.refresh(h)
        assert h.phase_durations["interview"] == 720
        assert h.snapshot["slug"] == "feat-x"


async def test_gate_audit_log_constraints(pg_engine: AsyncEngine):
    sm = async_sessionmaker(pg_engine, expire_on_commit=False)
    async with sm() as s:
        p = Project(repo_root="/home/user/proj3", repo_name="proj3")
        s.add(p)
        await s.commit()
        await s.refresh(p)

        g = GateAuditLog(
            project_id=p.id,
            session_id="sess-1",
            gate="gate2_pre_execute",
            reached_at=datetime.now(timezone.utc),
            retry_count=0,
        )
        s.add(g)
        await s.commit()
        await s.refresh(g)
        assert g.id is not None
        assert g.gate == "gate2_pre_execute"


async def test_daemon_run_model(pg_engine: AsyncEngine):
    sm = async_sessionmaker(pg_engine, expire_on_commit=False)
    async with sm() as s:
        d = DaemonRun(
            session_id="sess-1",
            command="claude --print '/css:ship --session feat-x'",
            started_at=datetime.now(timezone.utc),
        )
        s.add(d)
        await s.commit()
        await s.refresh(d)
        assert d.id is not None
        assert d.exit_code is None  # not yet finished
