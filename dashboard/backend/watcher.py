"""T4.13 — Watchdog-based session JSON watcher with SSE dispatch.

Bridges watchdog's thread-based events into the asyncio event loop via
asyncio.run_coroutine_threadsafe.

F1: emits gate_reached when a gate state transitions to 'pending'.
"""
from __future__ import annotations

import asyncio
import threading
from pathlib import Path
from typing import Optional

import structlog
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from backend.services.session_reader import parse_session_file
from backend.sse import SSEEvent, broker

log = structlog.get_logger()

# Track previous gate states per slug for F1 gate_reached detection.
# {slug: {gate_name: previous_state_or_None}}
_prev_gates: dict[str, dict[str, Optional[str]]] = {}
_prev_gates_lock = threading.Lock()


def _path_is_session(p: Path) -> bool:
    """Return True if path is under .claude/css/sessions/*.json (not _active.json)."""
    s = str(p).replace("\\", "/")
    return (
        "/.claude/css/sessions/" in s
        and p.suffix == ".json"
        and p.name != "_active.json"
    )


class _Handler(FileSystemEventHandler):
    """Watchdog event handler — dispatches coroutines into the asyncio loop."""

    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        p = Path(str(event.src_path))
        if not _path_is_session(p):
            return
        asyncio.run_coroutine_threadsafe(self._handle(p, event.event_type), self._loop)

    async def _handle(self, p: Path, etype: str) -> None:
        parsed = parse_session_file(p)
        if parsed is None:
            return

        await broker.publish(SSEEvent(
            name="session_updated",
            data={
                "slug": parsed.slug,
                "phase": parsed.current_phase,
                "gates": parsed.gates,
                "mtime": parsed.mtime,
            },
        ))

        # F1: detect gate state transition → "pending"
        with _prev_gates_lock:
            prev = _prev_gates.get(parsed.slug, {})
            new_prev: dict[str, Optional[str]] = {}
            for gate_name, gate_val in parsed.gates.items():
                current_state = gate_val.get("state") if isinstance(gate_val, dict) else gate_val
                old_state = prev.get(gate_name)
                new_prev[gate_name] = current_state
                if current_state == "pending" and old_state != "pending":
                    # Schedule outside the lock to avoid blocking
                    asyncio.ensure_future(broker.publish(SSEEvent(
                        name="gate_reached",
                        data={"slug": parsed.slug, "gate": gate_name},
                    )))
            _prev_gates[parsed.slug] = new_prev


class SessionWatcher:
    """Wraps a watchdog Observer, scheduled on watch_root recursively."""

    def __init__(self, watch_root: Path) -> None:
        self.watch_root = watch_root
        self.observer: Optional[Observer] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def start(self) -> None:
        self._loop = asyncio.get_event_loop()
        self.observer = Observer()
        self.observer.schedule(_Handler(self._loop), str(self.watch_root), recursive=True)
        self.observer.start()
        log.info("watcher.started", root=str(self.watch_root))

    def stop(self) -> None:
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=2)
            log.info("watcher.stopped")
