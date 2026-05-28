"""T4.3 — Session JSON reader with corruption tolerance."""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import structlog

log = structlog.get_logger()


@dataclass
class ParsedSession:
    slug: str
    idea: str
    repo_root: str
    repo_name: str
    current_phase: str
    phases: dict
    gates: dict
    master_flow: bool
    file_path: Path
    mtime: float

    @property
    def gate2_state(self) -> Optional[str]:
        g = self.gates.get("gate2_pre_execute")
        return (g or {}).get("state") if isinstance(g, dict) else None

    @property
    def gate3_state(self) -> Optional[str]:
        g = self.gates.get("gate3_pre_pr")
        return (g or {}).get("state") if isinstance(g, dict) else None


def parse_session_file(path: Path) -> Optional[ParsedSession]:
    """Parse a session JSON file, returning None on any error."""
    try:
        data = json.loads(path.read_text())
        return ParsedSession(
            slug=data["slug"],
            idea=data.get("idea", ""),
            repo_root=data.get("repo_root", ""),
            repo_name=data.get("repo_name", "(unknown)"),
            current_phase=data.get("current_phase", "interview"),
            phases=data.get("phases", {}),
            gates=data.get("gates", {}),
            master_flow=data.get("master_flow", False),
            file_path=path,
            mtime=path.stat().st_mtime,
        )
    except (json.JSONDecodeError, KeyError, FileNotFoundError, OSError) as e:
        log.warning("session_reader.parse_failed", path=str(path), error=str(e))
        return None


def list_sessions_for_project(project_root: Path) -> list[ParsedSession]:
    """List all valid session files under <project_root>/.claude/css/sessions/."""
    sessions_dir = project_root / ".claude" / "css" / "sessions"
    if not sessions_dir.exists():
        return []
    out = []
    for f in sessions_dir.glob("*.json"):
        if f.name == "_active.json":
            continue
        parsed = parse_session_file(f)
        if parsed:
            out.append(parsed)
    return out
