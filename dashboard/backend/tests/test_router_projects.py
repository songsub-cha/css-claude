"""T4.5 RED scaffold — projects router tests (cache-first from api-specialist spec)."""
import json
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.models import Project
from sqlalchemy.ext.asyncio import async_sessionmaker


async def test_get_projects_empty(pg_engine):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/api/projects")
    assert r.status_code == 200 and r.json() == {"projects": []}


async def test_patch_project_color(pg_engine):
    sm = async_sessionmaker(pg_engine, expire_on_commit=False)
    async with sm() as s:
        p = Project(repo_root="/r", repo_name="r", color="#000000")
        s.add(p)
        await s.commit()
        await s.refresh(p)
        pid = p.id
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.patch(
            f"/api/projects/{pid}",
            json={"color": "#22c55e"},
            headers={"Origin": "http://test"},
        )
    assert r.status_code == 200 and r.json()["color"] == "#22c55e"


# T8: GET /api/projects/epics — per-project Epic grouping (filesystem, no DB)
def _seed_project(tmp_path: Path, repo_name: str) -> Path:
    repo = tmp_path / repo_name
    s = repo / ".claude/css/sessions"
    s.mkdir(parents=True, exist_ok=True)

    def write(slug, phase, **h):
        body = {
            "slug": slug, "idea": f"idea-{slug}", "master_flow": True,
            "repo_root": str(repo), "repo_name": repo_name,
            "current_phase": phase, "phases": {}, "gates": {},
        }
        body.update(h)
        (s / f"{slug}.json").write_text(json.dumps(body))

    write("epic-x", "review", kind="epic")
    write("epic-x-p1", "execute",
          kind="phase", parent_slug="epic-x", phase_index=1, depends_on=[])
    return repo


async def test_get_projects_epics_grouped_per_project(tmp_path, monkeypatch):
    r1 = _seed_project(tmp_path, "alpha")
    r2 = _seed_project(tmp_path, "beta")
    pj = tmp_path / "projects.json"
    pj.write_text(json.dumps({"projects": [
        {"repo_root": str(r1), "repo_name": "alpha", "registered_at": "x", "color": "#22c55e"},
        {"repo_root": str(r2), "repo_name": "beta", "registered_at": "y", "color": "#a855f7"},
    ]}))
    monkeypatch.setenv("PROJECTS_JSON", str(pj))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/api/projects/epics")
    assert r.status_code == 200
    projects = {p["repo_name"]: p for p in r.json()["projects"]}
    assert set(projects) == {"alpha", "beta"}
    alpha_epics = {e["slug"] for e in projects["alpha"]["epics"]}
    assert "epic-x" in alpha_epics
    epic = next(e for e in projects["alpha"]["epics"] if e["slug"] == "epic-x")
    assert [n["phase_index"] for n in epic["flow"]["nodes"]] == [1]


async def test_patch_invalid_color_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.patch(
            "/api/projects/1",
            json={"color": "javascript:alert(1)"},
            headers={"Origin": "http://test"},
        )
    assert r.status_code == 422


# F2: PATCH broadcasts project_registered SSE
async def test_patch_broadcasts_sse(pg_engine):
    import asyncio
    from backend.sse import broker

    sm = async_sessionmaker(pg_engine, expire_on_commit=False)
    async with sm() as s:
        p = Project(repo_root="/r2", repo_name="r2", color="#000")
        s.add(p)
        await s.commit()
        await s.refresh(p)
        pid = p.id
    q = broker.subscribe()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.patch(
            f"/api/projects/{pid}",
            json={"color": "#ef4444"},
            headers={"Origin": "http://test"},
        )
    evt = await asyncio.wait_for(q.get(), 1.0)
    broker.unsubscribe(q)
    assert evt.name == "project_registered" and evt.data["color"] == "#ef4444"
