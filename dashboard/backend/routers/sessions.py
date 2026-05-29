"""T4.6 — GET /api/sessions (list across projects) + GET /api/sessions/{slug}.

Phase 2 (dashboard-epic-phase-view-p2): GET /api/sessions/epics returns the
hierarchical Epic -> Phase flow graph, and the flat list gains the hierarchy
fields (flat-with-parent-ref).
"""
from pathlib import Path

from fastapi import APIRouter, HTTPException

from backend.config import Settings
from backend.services.project_registry import read_projects
from backend.services.epic_flow import build_epic_flow
from backend.services.session_reader import (
    group_sessions_by_epic,
    list_sessions_for_project,
)

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def _settings() -> Settings:
    return Settings()


@router.get("")
async def list_sessions():
    s = _settings()
    out = []
    for proj in read_projects(s.projects_json):
        for sess in list_sessions_for_project(Path(proj.repo_root)):
            out.append({
                "slug": sess.slug,
                "idea": sess.idea,
                "repo_root": sess.repo_root,
                "repo_name": sess.repo_name,
                "current_phase": sess.current_phase,
                "phases": sess.phases,
                "gates": sess.gates,
                "mtime": sess.mtime,
                # Epic/Phase hierarchy (flat-with-parent-ref)
                "kind": sess.kind,
                "parent_slug": sess.parent_slug,
                "phase_index": sess.phase_index,
                "phase_label": sess.phase_label,
                "depends_on": sess.depends_on,
            })
    return {"sessions": out}


@router.get("/epics")
async def list_epics():
    """Hierarchical Epic -> Phase view: one entry per Epic with its flow graph.

    Declared before /{slug} so the literal `epics` path is not captured as a slug.
    """
    s = _settings()
    out = []
    for proj in read_projects(s.projects_json):
        sessions = list_sessions_for_project(Path(proj.repo_root))
        for key, group in group_sessions_by_epic(sessions).items():
            ref = group.epic or (group.phases[0] if group.phases else None)
            out.append({
                "slug": key,
                "repo_root": ref.repo_root if ref else proj.repo_root,
                "repo_name": ref.repo_name if ref else proj.repo_name,
                "flow": build_epic_flow(group),
            })
    return {"epics": out}


@router.get("/{slug}")
async def get_session(slug: str):
    s = _settings()
    for proj in read_projects(s.projects_json):
        for sess in list_sessions_for_project(Path(proj.repo_root)):
            if sess.slug == slug:
                return {
                    "slug": sess.slug,
                    "idea": sess.idea,
                    "repo_root": sess.repo_root,
                    "repo_name": sess.repo_name,
                    "current_phase": sess.current_phase,
                    "phases": sess.phases,
                    "gates": sess.gates,
                    "mtime": sess.mtime,
                    "master_flow": sess.master_flow,
                }
    raise HTTPException(404, f"session {slug!r} not found")
