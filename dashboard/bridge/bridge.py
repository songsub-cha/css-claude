"""
CSS Pipeline Dashboard — Bridge Daemon (host-side queue consumer).

Watches ~/.claude/css-dashboard/queue/ for *.json event files written by the
backend's queue_writer.  For each event:
  1. POST callback "started"
  2. subprocess.run(cmd, cwd=project_root, env={**os.environ, CSS_DASHBOARD_RESUME="1"}, ...)
  3. POST callback "finished" (with exit_code) or "failed" (on exception)
  4. Move event file to processed/ or failed/

main() also replays any backlog left in queue/ on startup (idempotent restart).
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import urllib.request
from pathlib import Path

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
except ImportError:  # pragma: no cover
    FileSystemEventHandler = object  # type: ignore[assignment,misc]
    Observer = None  # type: ignore[assignment]

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants — replaced by monkeypatch in tests
# ---------------------------------------------------------------------------
_BASE = Path.home() / ".claude" / "css-dashboard"
QUEUE: Path = _BASE / "queue"
PROCESSED: Path = QUEUE / "processed"
FAILED: Path = QUEUE / "failed"
RUNS: Path = _BASE / "runs"


# ---------------------------------------------------------------------------
# Callback helper
# ---------------------------------------------------------------------------

def _post_callback(url: str, payload: dict) -> None:
    """POST JSON payload to callback_url.  Best-effort — swallow all errors."""
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10):
            pass
    except Exception as exc:  # noqa: BLE001
        log.warning("_post_callback failed (url=%s): %s", url, exc)


# ---------------------------------------------------------------------------
# Core processor
# ---------------------------------------------------------------------------

def process_event(path: Path) -> None:
    """Process a single queue event file end-to-end."""
    try:
        event = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        log.error("Failed to parse event file %s: %s", path, exc)
        return

    evt_id: str = event.get("id", path.stem)
    session_id: str = event.get("session_id", "unknown")
    project_root: str = event.get("project_root", str(Path.home()))
    command: list[str] = event.get("command", [])
    callback_url: str = event.get("callback_url", "")

    log_file = RUNS / f"{evt_id}.log"
    RUNS.mkdir(parents=True, exist_ok=True)

    log.info("process_event: start evt=%s session=%s", evt_id, session_id)

    # POST started
    _post_callback(callback_url, {
        "event": "started",
        "id": evt_id,
        "session_id": session_id,
    })

    try:
        env = {**os.environ, "CSS_DASHBOARD_RESUME": "1"}
        with open(log_file, "w", encoding="utf-8") as lf:
            result = subprocess.run(
                command,
                cwd=project_root,
                env=env,
                timeout=3600,
                stdout=lf,
                stderr=subprocess.STDOUT,
            )
        exit_code = result.returncode
        log.info("process_event: finished evt=%s exit_code=%d", evt_id, exit_code)

        # POST finished (regardless of exit code)
        _post_callback(callback_url, {
            "event": "finished",
            "id": evt_id,
            "session_id": session_id,
            "exit_code": exit_code,
        })

        # Move to processed
        PROCESSED.mkdir(parents=True, exist_ok=True)
        dest = PROCESSED / path.name
        path.rename(dest)
        log.info("process_event: moved to processed/ evt=%s", evt_id)

    except subprocess.TimeoutExpired as exc:
        log.error("process_event: timeout evt=%s: %s", evt_id, exc)
        _post_callback(callback_url, {
            "event": "failed",
            "id": evt_id,
            "session_id": session_id,
            "reason": "timeout",
        })
        FAILED.mkdir(parents=True, exist_ok=True)
        path.rename(FAILED / path.name)

    except FileNotFoundError as exc:
        log.error("process_event: command not found evt=%s: %s", evt_id, exc)
        _post_callback(callback_url, {
            "event": "failed",
            "id": evt_id,
            "session_id": session_id,
            "reason": f"command_not_found: {exc}",
        })
        FAILED.mkdir(parents=True, exist_ok=True)
        path.rename(FAILED / path.name)

    except Exception as exc:  # noqa: BLE001
        log.error("process_event: unexpected error evt=%s: %s", evt_id, exc)
        _post_callback(callback_url, {
            "event": "failed",
            "id": evt_id,
            "session_id": session_id,
            "reason": str(exc),
        })
        FAILED.mkdir(parents=True, exist_ok=True)
        try:
            path.rename(FAILED / path.name)
        except Exception:  # noqa: BLE001
            pass


# ---------------------------------------------------------------------------
# Watchdog handler
# ---------------------------------------------------------------------------

class _Handler(FileSystemEventHandler):  # type: ignore[misc]
    def on_created(self, event) -> None:
        src = Path(event.src_path)
        if src.suffix == ".json" and src.parent == QUEUE:
            log.info("_Handler.on_created: %s", src)
            process_event(src)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Start bridge daemon: replay backlog, then watch for new events."""
    for d in (QUEUE, PROCESSED, FAILED, RUNS):
        d.mkdir(parents=True, exist_ok=True)

    # Replay backlog (idempotent restart)
    backlog = sorted(QUEUE.glob("*.json"))
    if backlog:
        log.info("main: replaying %d backlog events", len(backlog))
        for p in backlog:
            process_event(p)

    if Observer is None:  # pragma: no cover
        log.error("watchdog not installed; bridge daemon cannot start")
        return

    handler = _Handler()
    observer = Observer()
    observer.schedule(handler, str(QUEUE), recursive=False)
    observer.start()
    log.info("main: watching %s", QUEUE)
    try:
        observer.join()
    except KeyboardInterrupt:
        observer.stop()
        observer.join()
        log.info("main: bridge daemon stopped")


if __name__ == "__main__":  # pragma: no cover
    main()
