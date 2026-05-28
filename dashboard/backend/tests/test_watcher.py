"""T4.13 RED — SessionWatcher emits session_updated SSE event on JSON file write."""
import asyncio
import json
import pytest
import pytest_asyncio
from pathlib import Path

from backend.watcher import SessionWatcher
from backend.sse import broker


async def _consume_until(name: str, timeout: float = 3.0):
    """Subscribe to SSE broker and wait for an event with the given name."""
    q = broker.subscribe()
    try:
        end = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < end:
            try:
                evt = await asyncio.wait_for(q.get(), timeout=0.5)
            except asyncio.TimeoutError:
                continue
            if evt.name == name:
                return evt
    finally:
        broker.unsubscribe(q)
    raise AssertionError(f"event '{name}' not received within {timeout}s")


@pytest.mark.asyncio
async def test_watcher_emits_session_updated_on_write(tmp_path):
    repo = tmp_path / "alpha"
    s = repo / ".claude" / "css" / "sessions"
    s.mkdir(parents=True)
    w = SessionWatcher(watch_root=tmp_path)
    w.start()
    try:
        await asyncio.sleep(0.2)
        (s / "feat-x.json").write_text(json.dumps({
            "slug": "feat-x",
            "current_phase": "plan",
            "phases": {},
            "gates": {},
            "repo_root": str(repo),
            "repo_name": "alpha",
            "idea": "",
        }))
        evt = await _consume_until("session_updated")
        assert evt.data["slug"] == "feat-x"
    finally:
        w.stop()
