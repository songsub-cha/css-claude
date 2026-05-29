"""T4.1 — Pydantic Settings tests (executor-direct)."""
import os
from backend.config import Settings


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://a:b@c/d")
    monkeypatch.setenv("DASHBOARD_PORT", "7777")
    s = Settings()
    assert s.database_url == "postgresql+asyncpg://a:b@c/d"
    assert s.dashboard_port == 7777
    assert s.queue_dir.name == "queue"


def test_defaults():
    s = Settings(database_url="postgresql+asyncpg://x:y@z/w")
    assert s.dashboard_port == 7421
    assert s.dashboard_bind == "0.0.0.0"
    assert s.cors_origins == ["*"]
