"""T3.1: Migration test — adapted for native PG via TEST_DATABASE_URL (no Docker on Windows dev).

When TEST_DATABASE_URL is set (sync postgresql:// URL), converts it to asyncpg URL for Alembic.
Otherwise attempts testcontainers (requires Docker); skips if Docker unavailable.

Adaptation note: testcontainers -> native PG via TEST_DATABASE_URL (no Docker on Windows dev).
"""
import asyncio
import os
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from alembic.config import Config
from alembic import command


def _get_env_url() -> str | None:
    return os.environ.get("TEST_DATABASE_URL")


def _to_asyncpg_url(url: str) -> str:
    """Ensure URL uses postgresql+asyncpg:// scheme."""
    if url.startswith("postgresql+asyncpg://"):
        return url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql+psycopg2://"):
        return url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    return url


def _reset_schema(async_url: str) -> None:
    """Drop and recreate public schema for test isolation (asyncpg direct connection)."""
    async def _do_reset():
        import asyncpg
        from sqlalchemy.engine import make_url
        u = make_url(async_url)
        conn = await asyncpg.connect(
            host=u.host or "localhost",
            port=u.port or 5432,
            user=u.username,
            password=u.password,
            database=u.database,
        )
        try:
            await conn.execute("DROP SCHEMA public CASCADE")
            await conn.execute("CREATE SCHEMA public")
        finally:
            await conn.close()

    asyncio.run(_do_reset())


def _make_alembic_cfg(async_url: str) -> Config:
    """Create Alembic Config pointing at our alembic/ directory with the given asyncpg URL."""
    cfg = Config()
    cfg.set_main_option("script_location", "alembic")
    cfg.set_main_option("sqlalchemy.url", async_url)
    return cfg


@pytest.fixture(scope="module")
def alembic_async_url():
    """Provide asyncpg DB URL; reset schema before yielding for clean state."""
    env_url = _get_env_url()
    if env_url:
        async_url = _to_asyncpg_url(env_url)
        _reset_schema(async_url)
        yield async_url
    else:
        # Fallback: testcontainers (requires Docker)
        try:
            from testcontainers.postgres import PostgresContainer
        except ImportError:
            pytest.skip("testcontainers not installed and TEST_DATABASE_URL not set")
            return
        try:
            with PostgresContainer("postgres:16-alpine") as pg:
                raw = pg.get_connection_url()
                async_url = _to_asyncpg_url(raw)
                _reset_schema(async_url)
                yield async_url
        except Exception as exc:
            pytest.skip(f"Docker unavailable and TEST_DATABASE_URL not set: {exc}")


def test_initial_migration_creates_all_tables(alembic_async_url):
    """Alembic upgrade head must create exactly 4 app tables + alembic_version."""
    cfg = _make_alembic_cfg(alembic_async_url)
    command.upgrade(cfg, "head")

    async def check():
        engine = create_async_engine(alembic_async_url)
        async with engine.connect() as conn:
            rows = await conn.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema='public' ORDER BY table_name"
            ))
            tables = sorted(r[0] for r in rows)
        await engine.dispose()
        return tables

    result = asyncio.run(check())
    assert result == [
        "alembic_version",
        "daemon_runs",
        "gate_audit_log",
        "projects",
        "sessions_history",
    ]


def test_downgrade_removes_tables(alembic_async_url):
    """Alembic downgrade base must remove all 4 app tables."""
    cfg = _make_alembic_cfg(alembic_async_url)
    command.downgrade(cfg, "base")

    async def check():
        engine = create_async_engine(alembic_async_url)
        async with engine.connect() as conn:
            rows = await conn.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema='public' ORDER BY table_name"
            ))
            tables = sorted(r[0] for r in rows)
        await engine.dispose()
        return tables

    result = asyncio.run(check())
    # After downgrade to base, only alembic_version bookkeeping table remains
    assert result == ["alembic_version"]


def test_upgrade_after_downgrade(alembic_async_url):
    """Idempotency: downgrade then upgrade must restore all tables."""
    cfg = _make_alembic_cfg(alembic_async_url)
    command.upgrade(cfg, "head")

    async def check():
        engine = create_async_engine(alembic_async_url)
        async with engine.connect() as conn:
            rows = await conn.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema='public' ORDER BY table_name"
            ))
            tables = sorted(r[0] for r in rows)
        await engine.dispose()
        return tables

    result = asyncio.run(check())
    assert result == [
        "alembic_version",
        "daemon_runs",
        "gate_audit_log",
        "projects",
        "sessions_history",
    ]
