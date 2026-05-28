"""T4.5 — Shared FastAPI dependencies."""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import Settings
from backend.db import get_engine, get_session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    settings = Settings()
    engine = get_engine(settings.database_url)
    factory = get_session_factory(engine)
    async with factory() as s:
        yield s
