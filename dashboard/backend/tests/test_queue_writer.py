"""T4.9 RED scaffold — queue_writer: enqueue_resume + session_id validation."""
import json
import pytest
from pathlib import Path
from backend.services.queue_writer import enqueue_resume


def test_enqueue_writes_valid_event(tmp_path):
    qdir = tmp_path / "queue"
    qdir.mkdir()
    evt_id = enqueue_resume(
        queue_dir=qdir,
        session_id="feat-x",
        project_root="/home/user/repo",
        callback_url="http://localhost:7421/api/internal/run-result",
    )
    files = list(qdir.glob("*.json"))
    assert len(files) == 1
    p = json.loads(files[0].read_text())
    assert p["id"] == evt_id and p["session_id"] == "feat-x"
    assert p["command"] == ["claude", "--print", "/css:ship --session feat-x"]
    assert p["project_root"] == "/home/user/repo"


def test_enqueue_rejects_unsafe_session_id(tmp_path):
    with pytest.raises(ValueError):
        enqueue_resume(
            queue_dir=tmp_path,
            session_id="x; rm -rf /",
            project_root="/r",
            callback_url="http://x",
        )
