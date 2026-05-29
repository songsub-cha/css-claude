"""T4.8 — GET /api/sessions/{slug}/artifacts (list + content with traversal guard)."""
from pathlib import Path

from fastapi import APIRouter, HTTPException

from backend.services.artifact_reader import (
    ArtifactForbidden,
    ArtifactNotFound,
    WHITELIST,
    resolve_artifact_path,
)
from backend.routers.sessions import get_session

router = APIRouter(prefix="/api/sessions", tags=["artifacts"])


@router.get("/{slug}/artifacts")
async def list_artifacts(slug: str):
    session = await get_session(slug)
    candidates = list(WHITELIST)

    # Discover rich-spec names from .claude/css/plans
    plans_dir = Path(session["repo_root"]) / ".claude/css/plans"
    if plans_dir.exists():
        for p in plans_dir.glob(f"*-spec-{slug}-*.md"):
            task_id = p.name.split("-spec-")[0]
            candidates.append(f"rich-spec-{task_id}")

    available = []
    for name in candidates:
        try:
            resolved = resolve_artifact_path(session, name)
            stat = resolved.stat()
            available.append({
                "name": name,
                "path": str(resolved),
                "size": stat.st_size,
                "mtime": stat.st_mtime,
            })
        except (ArtifactNotFound, ArtifactForbidden):
            continue

    return {"artifacts": available}


@router.get("/{slug}/artifacts/{name}")
async def get_artifact(slug: str, name: str):
    session = await get_session(slug)
    try:
        path = resolve_artifact_path(session, name)
    except ArtifactForbidden:
        raise HTTPException(403, "artifact path is outside repo_root")
    except ArtifactNotFound:
        raise HTTPException(404, f"artifact {name!r} not found")

    stat = path.stat()
    return {
        "name": name,
        "path": str(path),
        "content_md": path.read_text(encoding="utf-8"),
        "size": stat.st_size,
        "mtime": stat.st_mtime,
    }
