"""T4.10 RED scaffold — gates router: approve + lock-held 409 + gate_approved SSE (F1)."""
import json
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from backend.main import app


def _setup(tmp_path, gate_state):
    repo = tmp_path / "alpha"
    repo.mkdir()
    s = repo / ".claude/css/sessions"
    s.mkdir(parents=True)
    (s / "feat-x.json").write_text(
        json.dumps(
            {
                "slug": "feat-x",
                "idea": "i",
                "master_flow": True,
                "repo_root": str(repo),
                "repo_name": "alpha",
                "current_phase": "review",
                "phases": {},
                "gates": {"gate2_pre_execute": {"state": gate_state}},
            }
        )
    )
    pj = tmp_path / "projects.json"
    pj.write_text(
        json.dumps(
            {
                "projects": [
                    {
                        "repo_root": str(repo),
                        "repo_name": "alpha",
                        "registered_at": "x",
                        "color": "#22c55e",
                    }
                ]
            }
        )
    )
    return repo, pj


async def test_approve_pending_gate(tmp_path, monkeypatch):
    import asyncio
    from backend.sse import broker

    repo, pj = _setup(tmp_path, "pending")
    qdir = tmp_path / "queue"
    qdir.mkdir()
    monkeypatch.setenv("PROJECTS_JSON", str(pj))
    monkeypatch.setenv("QUEUE_DIR", str(qdir))
    q = broker.subscribe()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post(
            "/api/sessions/feat-x/gates/gate2_pre_execute/approve",
            headers={"Origin": "http://test"},
        )
    assert r.status_code == 200
    sj = json.loads((repo / ".claude/css/sessions/feat-x.json").read_text())
    assert sj["gates"]["gate2_pre_execute"]["state"] == "approved"
    assert sj["gates"]["gate2_pre_execute"]["source"] == "dashboard_drag"
    assert len(list(qdir.glob("*.json"))) == 1
    evt = await asyncio.wait_for(q.get(), 1.0)
    broker.unsubscribe(q)
    assert evt.name == "gate_approved"  # F1


async def test_approve_lock_held_returns_409(tmp_path, monkeypatch):
    repo, pj = _setup(tmp_path, "pending")
    locks = repo / ".claude/css/locks"
    locks.mkdir(parents=True)
    (locks / "feat-x.lock").write_text("{}")
    monkeypatch.setenv("PROJECTS_JSON", str(pj))
    monkeypatch.setenv("QUEUE_DIR", str(tmp_path / "queue"))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post(
            "/api/sessions/feat-x/gates/gate2_pre_execute/approve",
            headers={"Origin": "http://test"},
        )
    assert r.status_code == 409
