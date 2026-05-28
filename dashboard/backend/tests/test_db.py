"""T3.3: Async engine factory tests — native PG via TEST_DATABASE_URL.

Adapted from rich spec RED scaffold: testcontainers -> TEST_DATABASE_URL (no Docker on Windows dev).
Uses shared pg_engine from conftest.py.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import get_engine, get_session_factory, close_engine


async def test_engine_singleton(pg_async_url: str):
    """get_engine returns the same instance for the same URL (singleton pattern)."""
    e1 = get_engine(pg_async_url)
    e2 = get_engine(pg_async_url)
    assert e1 is e2
    await close_engine()


async def test_engine_recreated_after_close(pg_async_url: str):
    """After close_engine(), get_engine creates a fresh engine."""
    e1 = get_engine(pg_async_url)
    await close_engine()
    e2 = get_engine(pg_async_url)
    assert e1 is not e2
    await close_engine()


async def test_session_factory_yields_active_session(pg_engine):
    """get_session_factory returns a factory whose sessions are active."""
    from backend.db import get_session_factory
    factory = get_session_factory(pg_engine)
    async with factory() as s:
        assert isinstance(s, AsyncSession)
        assert s.is_active
