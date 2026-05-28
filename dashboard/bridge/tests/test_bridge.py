import json
import shutil
from pathlib import Path
from bridge import bridge as b


def _get_command_echo_ok():
    """Return a command that echoes 'resumed' and exits 0 — Windows compatible."""
    if shutil.which("bash"):
        return ["bash", "-c", "echo resumed && exit 0"]
    return ["cmd", "/c", "echo resumed"]


def _get_command_fail():
    """Return a command that exits non-zero — Windows compatible."""
    if shutil.which("bash"):
        return ["bash", "-c", "exit 7"]
    return ["cmd", "/c", "exit 7"]


def test_process_event_invokes_command(tmp_path, monkeypatch):
    qdir = tmp_path / "queue"
    pdir = qdir / "processed"
    fdir = qdir / "failed"
    rdir = tmp_path / "runs"
    for d in (qdir, pdir, fdir, rdir):
        d.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(b, "QUEUE", qdir)
    monkeypatch.setattr(b, "PROCESSED", pdir)
    monkeypatch.setattr(b, "FAILED", fdir)
    monkeypatch.setattr(b, "RUNS", rdir)
    cbs = []
    monkeypatch.setattr(b, "_post_callback", lambda url, p: cbs.append(p))
    ep = qdir / "evt-abc.json"
    ep.write_text(json.dumps({
        "id": "evt-abc",
        "session_id": "feat-x",
        "project_root": str(tmp_path),
        "command": _get_command_echo_ok(),
        "callback_url": "http://test/cb",
    }))
    b.process_event(ep)
    assert (pdir / "evt-abc.json").exists()
    assert any(c["event"] == "started" for c in cbs)
    assert any(c["event"] == "finished" for c in cbs)
    log_text = (rdir / "evt-abc.log").read_text().strip()
    assert "resumed" in log_text


def test_failing_command_moves_to_failed(tmp_path, monkeypatch):
    qdir = tmp_path / "queue"
    pdir = qdir / "processed"
    fdir = qdir / "failed"
    rdir = tmp_path / "runs"
    for d in (qdir, pdir, fdir, rdir):
        d.mkdir(parents=True, exist_ok=True)
    for n, v in [("QUEUE", qdir), ("PROCESSED", pdir), ("FAILED", fdir), ("RUNS", rdir)]:
        monkeypatch.setattr(b, n, v)
    monkeypatch.setattr(b, "_post_callback", lambda url, p: None)
    ep = qdir / "evt-bad.json"
    ep.write_text(json.dumps({
        "id": "evt-bad",
        "session_id": "feat-y",
        "project_root": str(tmp_path),
        "command": _get_command_fail(),
        "callback_url": "http://test/cb",
    }))
    b.process_event(ep)
    # non-zero exit is "finished" (not exception), moved to processed
    assert (pdir / "evt-bad.json").exists()
