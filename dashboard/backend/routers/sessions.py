"""T4.6 — GET /api/sessions (list across projects) + GET /api/sessions/{slug}."""
from pathlib import Path

from fastapi import APIRouter, HTTPException

from backend.config import Settings
from backend.services.project_registry import read_projects
from backend.services.session_reader import list_sessions_for_project

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
            })
    return {"sessions": out}


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
