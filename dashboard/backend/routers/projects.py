"""T4.5 — GET /api/projects + PATCH /api/projects/{id} with hex validation + SSE F2.

Phase 2 (dashboard-epic-phase-view-p2): GET /api/projects/epics groups each
project's Epic -> Phase flow graphs (filesystem-backed; does not touch the DB).
"""
import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import Settings
from backend.deps import get_db_session
from backend.models import Project
from backend.services.epic_flow import build_epic_flow
from backend.services.project_registry import read_projects
from backend.services.session_reader import (
    group_sessions_by_epic,
    list_sessions_for_project,
)
from backend.sse import SSEEvent, broker

HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("/epics")
async def list_project_epics():
    """Per-project Epic grouping with flow graphs (filesystem; no DB)."""
    settings = Settings()
    out = []
    for proj in read_projects(settings.projects_json):
        sessions = list_sessions_for_project(Path(proj.repo_root))
        epics = [
            {"slug": key, "flow": build_epic_flow(group)}
            for key, group in group_sessions_by_epic(sessions).items()
        ]
        out.append({
            "repo_name": proj.repo_name,
            "repo_root": proj.repo_root,
            "epics": epics,
        })
    return {"projects": out}


class ProjectOut(BaseModel):
    id: int
    repo_root: str
    repo_name: str
    color: str


class ProjectPatch(BaseModel):
    color: str

    @field_validator("color")
    @classmethod
    def hex_only(cls, v: str) -> str:
        if not HEX_RE.match(v):
            raise ValueError("color must be a 6-digit hex string like #RRGGBB")
        return v


@router.get("")
async def list_projects(db: AsyncSession = Depends(get_db_session)):
    rows = (await db.execute(select(Project).order_by(Project.id))).scalars().all()
    return {
        "projects": [
            ProjectOut(
                id=p.id,
                repo_root=p.repo_root,
                repo_name=p.repo_name,
                color=p.color,
            ).model_dump()
            for p in rows
        ]
    }


@router.patch("/{project_id}")
async def patch_project(
    project_id: int,
    body: ProjectPatch,
    db: AsyncSession = Depends(get_db_session),
):
    p = await db.get(Project, project_id)
    if p is None:
        raise HTTPException(404, "project not found")
    p.color = body.color
    await db.commit()
    await db.refresh(p)

    # F2: broadcast project color change as SSE event
    await broker.publish(
        SSEEvent(
            "project_registered",
            {
                "project_id": p.id,
                "repo_name": p.repo_name,
                "color": p.color,
            },
        )
    )

    return ProjectOut(
        id=p.id,
        repo_root=p.repo_root,
        repo_name=p.repo_name,
        color=p.color,
    ).model_dump()
