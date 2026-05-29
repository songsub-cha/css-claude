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


# ── T7: GET /api/sessions/epics (hierarchical Epic -> Phase flow) ───────────────

def _write_session(repo: Path, slug: str, phase: str, **hierarchy) -> None:
    s = repo / ".claude/css/sessions"
    s.mkdir(parents=True, exist_ok=True)
    body = {
        "slug": slug, "idea": f"idea-{slug}", "master_flow": True,
        "repo_root": str(repo), "repo_name": repo.name,
        "current_phase": phase, "phases": {}, "gates": {},
    }
    body.update(hierarchy)
    (s / f"{slug}.json").write_text(json.dumps(body))


async def test_get_sessions_epics_hierarchical(tmp_path, monkeypatch):
    repo = tmp_path / "alpha"
    _write_session(repo, "epic-x", "review", kind="epic")
    _write_session(repo, "epic-x-p1", "verify",
                   kind="phase", parent_slug="epic-x", phase_index=1, depends_on=[])
    _write_session(repo, "epic-x-p2", "execute",
                   kind="phase", parent_slug="epic-x", phase_index=2, depends_on=[1])
    pj = tmp_path / "projects.json"
    pj.write_text(json.dumps({"projects": [
        {"repo_root": str(repo), "repo_name": "alpha", "registered_at": "x", "color": "#22c55e"},
    ]}))
    monkeypatch.setenv("PROJECTS_JSON", str(pj))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/api/sessions/epics")
    assert r.status_code == 200
    epics = {e["slug"]: e for e in r.json()["epics"]}
    assert "epic-x" in epics
    ex = epics["epic-x"]
    assert ex["repo_name"] == "alpha"
    assert [n["phase_index"] for n in ex["flow"]["nodes"]] == [1, 2]
    assert ex["flow"]["edges"] == [{"from": 1, "to": 2}]


async def test_get_sessions_epics_legacy_single_phase(tmp_path, monkeypatch):
    repo = tmp_path / "beta"
    _write_session(repo, "old-feat", "plan")  # no kind -> legacy epic
    pj = tmp_path / "projects.json"
    pj.write_text(json.dumps({"projects": [
        {"repo_root": str(repo), "repo_name": "beta", "registered_at": "y", "color": "#a855f7"},
    ]}))
    monkeypatch.setenv("PROJECTS_JSON", str(pj))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/api/sessions/epics")
    epics = {e["slug"]: e for e in r.json()["epics"]}
    assert "old-feat" in epics
    assert len(epics["old-feat"]["flow"]["nodes"]) == 1
