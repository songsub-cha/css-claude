"""Shared pytest fixtures for dashboard backend tests.

T3.3 adaptation: native PG via TEST_DATABASE_URL (no Docker on Windows dev).
Uses pytest_asyncio.fixture(loop_scope="module") to share one event loop
across all async module-scoped fixtures and tests (pytest-asyncio >= 1.x).
"""
import os
import concurrent.futures
import pytest
import pytest_asyncio

from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from alembic.config import Config
from alembic import command


# ── URL helpers ────────────────────────────────────────────────────────────────

def get_test_database_url() -> str | None:
    """Return TEST_DATABASE_URL env var if set (sync postgresql:// form)."""
    return os.environ.get("TEST_DATABASE_URL")


def to_asyncpg_url(url: str) -> str:
    """Convert any postgresql URL variant to postgresql+asyncpg://..."""
    if url.startswith("postgresql+asyncpg://"):
        return url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql+psycopg2://"):
        return url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    return url


# ── Schema reset ───────────────────────────────────────────────────────────────

async def reset_schema(async_url: str) -> None:
    """Drop and recreate public schema for clean test isolation (asyncpg direct)."""
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


def run_alembic_upgrade(async_url: str) -> None:
    """Run Alembic upgrade head in a fresh thread (avoids nested asyncio.run conflicts)."""
    def _do():
        cfg = Config()
        cfg.set_main_option("script_location", "alembic")
        cfg.set_main_option("sqlalchemy.url", async_url)
        command.upgrade(cfg, "head")

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        pool.submit(_do).result()


# ── pg_async_url: resolve DB URL once per module ───────────────────────────────

@pytest.fixture(scope="module")
def pg_async_url() -> str:
    """Resolve the asyncpg URL for this test run (env var or testcontainers)."""
    env_url = get_test_database_url()
    if env_url:
        return to_asyncpg_url(env_url)

    try:
        from testcontainers.postgres import PostgresContainer
    except ImportError:
        pytest.skip("testcontainers not installed and TEST_DATABASE_URL not set")

    try:
        with PostgresContainer("postgres:16-alpine") as pg:
            raw = pg.get_connection_url()
            return to_asyncpg_url(raw)
    except Exception as exc:
        pytest.skip(f"Docker unavailable and TEST_DATABASE_URL not set: {exc}")


# ── pg_engine: module-scoped async engine shared across all tests ──────────────

@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def pg_engine(pg_async_url: str) -> AsyncEngine:
    """
    Module-scoped async engine fixture (loop_scope="module" ensures all tests
    share one event loop, keeping asyncpg connections valid across tests).

    Resets the public schema and runs Alembic upgrade head before yielding.
    Disposes the engine after the module's tests complete.
    """
    await reset_schema(pg_async_url)
    run_alembic_upgrade(pg_async_url)

    engine = create_async_engine(pg_async_url, pool_pre_ping=True)
    yield engine
    await engine.dispose()
