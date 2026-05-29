"""T4.5 RED scaffold — projects router tests (cache-first from api-specialist spec)."""
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
