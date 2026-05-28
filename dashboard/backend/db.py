"""Async SQLAlchemy engine factory with singleton pattern.

Provides:
  - get_engine(url): returns a module-level singleton AsyncEngine
  - get_session_factory(engine): returns an async_sessionmaker for the given engine
  - close_engine(): disposes the singleton engine and resets the internal reference
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Module-level singleton engine
_engine: AsyncEngine | None = None


def get_engine(url: str) -> AsyncEngine:
    """Return the singleton AsyncEngine, creating it if necessary.

    Parameters
    ----------
    url:
        asyncpg connection URL, e.g.
        ``postgresql+asyncpg://user:pass@host:port/dbname``

    Returns
    -------
    AsyncEngine
        The module-level singleton engine.
    """
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            url,
            pool_pre_ping=True,
            pool_size=10,
        )
    return _engine


def get_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Return an async_sessionmaker bound to *engine*.

    Parameters
    ----------
    engine:
        The AsyncEngine to bind sessions to.

    Returns
    -------
    async_sessionmaker[AsyncSession]
        A factory that produces ``AsyncSession`` instances.
    """
    return async_sessionmaker(
        engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )


async def close_engine() -> None:
    """Dispose the singleton engine and reset the internal reference.

    Safe to call even if the engine was never created (no-op in that case).
    """
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
