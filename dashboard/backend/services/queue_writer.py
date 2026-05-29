"""T4.9 — queue writer with session_id validation (command injection guard).

enqueue_resume() atomically writes a JSON event file into queue_dir.
session_id is validated against ^[a-z0-9-]{1,64}$ to prevent command injection.
"""
from __future__ import annotations

import json
import os
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path

SESSION_ID_RE = re.compile(r"^[a-z0-9-]{1,64}$")


def enqueue_resume(
    *,
    queue_dir: Path,
    session_id: str,
    project_root: str,
    callback_url: str,
) -> str:
    """Write a resume-event JSON file into queue_dir and return the event id.

    Raises ValueError if session_id does not match the safe regex.
    Uses atomic tmp→replace to avoid partial reads by the queue consumer.
    """
    if not SESSION_ID_RE.match(session_id):
        raise ValueError(
            f"session_id {session_id!r} is invalid — must match ^[a-z0-9-]{{1,64}}$"
        )

    evt_id = f"evt-{secrets.token_hex(8)}"
    payload = {
        "id": evt_id,
        "session_id": session_id,
        "project_root": project_root,
        "command": ["claude", "--print", f"/css:ship --session {session_id}"],
        "callback_url": callback_url,
        "enqueued_at": datetime.now(timezone.utc).isoformat(),
    }

    queue_dir = Path(queue_dir)
    queue_dir.mkdir(parents=True, exist_ok=True)

    tmp_path = queue_dir / f".{evt_id}.json.tmp"
    final_path = queue_dir / f"{evt_id}.json"

    tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.replace(tmp_path, final_path)

    return evt_id
