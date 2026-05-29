"""T4.3 — Session JSON reader with corruption tolerance.

Phase 1 (dashboard-epic-phase-view-p1): parse the Epic/Phase hierarchy fields
(kind/parent_slug/phase_index/phase_label/depends_on) with legacy fallback (D9),
and group child Phase sessions under their parent Epic for the flow view.
"""
import json
from dataclasses import dataclass, field
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
    # Epic/Phase hierarchy (D1/D9). Legacy sessions (no `kind`) default to a
    # single-Phase Epic: kind="epic", parent_slug=None, depends_on=[].
    kind: str = "epic"
    parent_slug: Optional[str] = None
    phase_index: Optional[int] = None
    phase_label: Optional[str] = None
    depends_on: list = field(default_factory=list)

    @property
    def gate2_state(self) -> Optional[str]:
        g = self.gates.get("gate2_pre_execute")
        return (g or {}).get("state") if isinstance(g, dict) else None

    @property
    def gate3_state(self) -> Optional[str]:
        g = self.gates.get("gate3_pre_pr")
        return (g or {}).get("state") if isinstance(g, dict) else None

    @property
    def is_phase(self) -> bool:
        return self.kind == "phase"


@dataclass
class EpicGroup:
    """An Epic and its child Phases (ordered by phase_index). `epic` is None when
    only orphan phases were found (parent Epic file missing/corrupt)."""
    epic: Optional[ParsedSession]
    phases: list = field(default_factory=list)


def parse_session_file(path: Path) -> Optional[ParsedSession]:
    """Parse a session JSON file, returning None on any error."""
    try:
        data = json.loads(path.read_text())
        depends_on = data.get("depends_on", [])
        if not isinstance(depends_on, list):
            depends_on = []
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
            kind=data.get("kind", "epic"),
            parent_slug=data.get("parent_slug"),
            phase_index=data.get("phase_index"),
            phase_label=data.get("phase_label"),
            depends_on=depends_on,
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


def group_sessions_by_epic(sessions: list[ParsedSession]) -> dict[str, "EpicGroup"]:
    """Group parsed sessions into Epic → [child Phases] (D1).

    - Each non-phase session (`kind != "phase"`) becomes an Epic group keyed by
      its slug. A legacy (`kind`-less) session is its own single-Phase Epic (D9).
    - Each phase session attaches to the group keyed by its `parent_slug`; if that
      parent Epic was never seen (missing/corrupt file), an orphan group with
      `epic=None` is created so the phase still surfaces (corruption tolerance).
    - Phases within a group are ordered by `phase_index` (None sorts last).
    """
    groups: dict[str, EpicGroup] = {}

    # First pass: register every Epic so phases can find their parent.
    for s in sessions:
        if not s.is_phase:
            groups.setdefault(s.slug, EpicGroup(epic=s))

    # Second pass: attach phases to their parent (or an orphan group).
    for s in sessions:
        if not s.is_phase:
            continue
        key = s.parent_slug or s.slug
        group = groups.setdefault(key, EpicGroup(epic=None))
        group.phases.append(s)

    for group in groups.values():
        group.phases.sort(
            key=lambda p: p.phase_index if p.phase_index is not None else float("inf")
        )
    return groups
