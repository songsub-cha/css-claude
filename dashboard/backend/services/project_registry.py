"""T4.4 — projects.json reader."""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ProjectEntry:
    repo_root: str
    repo_name: str
    registered_at: str
    color: Optional[str]


def read_projects(projects_json: Path) -> list[ProjectEntry]:
    """Read projects from projects.json, returning empty list if missing or corrupt."""
    if not projects_json.exists():
        return []
    try:
        data = json.loads(projects_json.read_text())
        return [
            ProjectEntry(
                repo_root=p["repo_root"],
                repo_name=p["repo_name"],
                registered_at=p.get("registered_at", ""),
                color=p.get("color"),
            )
            for p in data.get("projects", [])
        ]
    except (json.JSONDecodeError, KeyError, OSError):
        return []
