"""T4.1 — Pydantic Settings for dashboard runtime config."""
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    dashboard_port: int = 7421
    dashboard_bind: str = "0.0.0.0"
    host_claude_dir: Path = Path("/host/.claude")
    queue_dir: Path = Field(default_factory=lambda: Path("/host/.claude/css-dashboard/queue"))
    runs_dir: Path = Field(default_factory=lambda: Path("/host/.claude/css-dashboard/runs"))
    projects_json: Path = Field(
        default_factory=lambda: Path("/host/.claude/css-dashboard/projects.json")
    )
    cors_origins: list[str] = ["*"]
    log_level: str = "INFO"
