"""T4.8 RED scaffold — artifacts router tests (cache-first from api-specialist spec)."""
import json
from httpx import AsyncClient, ASGITransport
from backend.main import app


async def test_artifact_content_spec(tmp_path, monkeypatch):
    repo = tmp_path / "alpha"
    spec = repo / "docs/specs/x.md"
    spec.parent.mkdir(parents=True)
    spec.write_text("# hello")
    sd = repo / ".claude/css/sessions"
    sd.mkdir(parents=True)
    (sd / "feat-x.json").write_text(json.dumps({
        "slug": "feat-x", "idea": "i", "master_flow": True,
        "repo_root": str(repo), "repo_name": "alpha", "current_phase": "plan",
        "phases": {"interview": {"artifact": "docs/specs/x.md"}},
        "gates": {},
    }))
    pj = tmp_path / "projects.json"
    pj.write_text(json.dumps({"projects": [
        {"repo_root": str(repo), "repo_name": "alpha", "registered_at": "x", "color": "#22c55e"},
    ]}))
    monkeypatch.setenv("PROJECTS_JSON", str(pj))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/api/sessions/feat-x/artifacts/spec")
    assert r.status_code == 200 and "# hello" in r.json()["content_md"]


async def test_artifact_traversal_returns_403(tmp_path, monkeypatch):
    repo = tmp_path / "alpha"
    repo.mkdir()
    sd = repo / ".claude/css/sessions"
    sd.mkdir(parents=True)
    (sd / "feat-x.json").write_text(json.dumps({
        "slug": "feat-x", "idea": "i", "master_flow": True,
        "repo_root": str(repo), "repo_name": "alpha", "current_phase": "plan",
        "phases": {"interview": {"artifact": "../../etc/passwd"}},
        "gates": {},
    }))
    pj = tmp_path / "projects.json"
    pj.write_text(json.dumps({"projects": [
        {"repo_root": str(repo), "repo_name": "alpha", "registered_at": "x", "color": "#22c55e"},
    ]}))
    monkeypatch.setenv("PROJECTS_JSON", str(pj))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/api/sessions/feat-x/artifacts/spec")
    assert r.status_code == 403
