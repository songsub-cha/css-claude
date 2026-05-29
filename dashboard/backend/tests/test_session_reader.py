"""T4.3 — session_reader tests (css-async-coder spec)."""
import json
from pathlib import Path
from backend.services.session_reader import parse_session_file, list_sessions_for_project


def make_session(tmp_path: Path, slug: str, phase: str) -> Path:
    d = tmp_path / ".claude" / "css" / "sessions"
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{slug}.json"
    f.write_text(json.dumps({
        "slug": slug,
        "idea": "x",
        "master_flow": True,
        "repo_root": str(tmp_path),
        "repo_name": tmp_path.name,
        "current_phase": phase,
        "phases": {p: {"status": "pending"} for p in
                   ["interview", "plan", "review", "execute", "verify", "document", "pr"]},
        "gates": {"gate2_pre_execute": None, "gate3_pre_pr": None},
    }))
    return f


def test_parse_session_file(tmp_path):
    f = make_session(tmp_path, "feat-x", "plan")
    p = parse_session_file(f)
    assert p.slug == "feat-x" and p.current_phase == "plan" and p.repo_name == tmp_path.name


def test_list_sessions_for_project(tmp_path):
    make_session(tmp_path, "feat-a", "review")
    make_session(tmp_path, "feat-b", "execute")
    assert sorted(s.slug for s in list_sessions_for_project(tmp_path)) == ["feat-a", "feat-b"]


def test_corrupted_json_returns_none(tmp_path):
    d = tmp_path / ".claude/css/sessions"
    d.mkdir(parents=True)
    (d / "broken.json").write_text("{not json")
    assert parse_session_file(d / "broken.json") is None
