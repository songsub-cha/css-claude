"""T4.4 — project_registry tests (executor-direct)."""
import json
from pathlib import Path
from backend.services.project_registry import read_projects, ProjectEntry


def test_read_projects(tmp_path):
    pj = tmp_path / "projects.json"
    pj.write_text(json.dumps({"projects": [
        {"repo_root": "/p1", "repo_name": "p1", "registered_at": "2026-01-01T00:00:00Z", "color": None},
        {"repo_root": "/p2", "repo_name": "p2", "registered_at": "2026-01-02T00:00:00Z", "color": "#22c55e"},
    ]}))
    entries = read_projects(pj)
    assert len(entries) == 2
    assert entries[0].repo_root == "/p1"
    assert entries[1].color == "#22c55e"


def test_missing_file_returns_empty(tmp_path):
    assert read_projects(tmp_path / "nope.json") == []
