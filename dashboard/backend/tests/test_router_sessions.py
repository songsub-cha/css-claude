"""T4.6 RED scaffold — sessions router tests (cache-first from api-specialist spec)."""
import json
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from backend.main import app


def _make_proj(tmp_path: Path, repo_name: str, slug: str, phase: str) -> Path:
    s = tmp_path / repo_name / ".claude/css/sessions"
    s.mkdir(parents=True, exist_ok=True)
    (s / f"{slug}.json").write_text(
        json.dumps({
            "slug": slug, "idea": "i", "master_flow": True,
            "repo_root": str(tmp_path / repo_name), "repo_name": repo_name,
            "current_phase": phase, "phases": {}, "gates": {},
        })
    )
    return tmp_path / repo_name


async def test_get_sessions_aggregates(tmp_path, monkeypatch):
    p1 = _make_proj(tmp_path, "alpha", "feat-x", "review")
    p2 = _make_proj(tmp_path, "beta", "feat-y", "execute")
    pj = tmp_path / "projects.json"
    pj.write_text(json.dumps({"projects": [
        {"repo_root": str(p1), "repo_name": "alpha", "registered_at": "x", "color": "#22c55e"},
        {"repo_root": str(p2), "repo_name": "beta", "registered_at": "y", "color": "#a855f7"},
    ]}))
    monkeypatch.setenv("PROJECTS_JSON", str(pj))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/api/sessions")
    assert sorted(s["slug"] for s in r.json()["sessions"]) == ["feat-x", "feat-y"]


async def test_get_session_detail(tmp_path, monkeypatch):
    p = _make_proj(tmp_path, "alpha", "feat-x", "review")
    pj = tmp_path / "projects.json"
    pj.write_text(json.dumps({"projects": [
        {"repo_root": str(p), "repo_name": "alpha", "registered_at": "x", "color": "#22c55e"},
    ]}))
    monkeypatch.setenv("PROJECTS_JSON", str(pj))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/api/sessions/feat-x")
    assert r.json()["slug"] == "feat-x" and r.json()["repo_name"] == "alpha"
