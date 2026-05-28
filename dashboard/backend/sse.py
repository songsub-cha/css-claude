"""T4.11 — SSE broker, formalized.

Provides:
  SSEEvent(name, data)    — typed event container
  SSEBroker               — fan-out broker with bounded per-subscriber queues
  broker                  — module-level singleton (imported by routers)

Drop-on-full: slow consumers are silently dropped (put_nowait + QueueFull swallowed)
so a stalled browser tab never blocks the event loop.
"""
from __future__ import annotations

import asyncio
from asyncio import QueueFull
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SSEEvent:
    name: str
    data: dict[str, Any] = field(default_factory=dict)


class SSEBroker:
    """Fan-out SSE broker.

    Each subscriber gets its own bounded asyncio.Queue.
    publish() uses put_nowait() and silently drops events for full queues
    (slow consumer protection).
    """

    def __init__(self) -> None:
        self._subs: set[asyncio.Queue[SSEEvent]] = set()

    def subscribe(self, maxsize: int = 100) -> asyncio.Queue[SSEEvent]:
        """Create and register a new subscriber queue, then return it."""
        q: asyncio.Queue[SSEEvent] = asyncio.Queue(maxsize=maxsize)
        self._subs.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue[SSEEvent]) -> None:
        """Remove a subscriber queue (idempotent)."""
        self._subs.discard(q)

    async def publish(self, evt: SSEEvent) -> None:
        """Broadcast event to all subscribers; drop on full (non-blocking)."""
        for q in list(self._subs):
            try:
                q.put_nowait(evt)
            except QueueFull:
                pass  # slow consumer — drop event silently


# Module-level singleton used by routers and watcher
broker = SSEBroker()
