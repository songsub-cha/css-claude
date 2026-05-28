"""Minimal SSE broker stub — T4.5 prerequisite. Formalized in T4.11.

Provides:
  SSEEvent(name, data)  — typed event container
  broker.publish(evt)   — broadcast to all subscribers
  broker.subscribe()    — return asyncio.Queue for one subscriber
  broker.unsubscribe(q) — remove subscriber
"""
import asyncio
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SSEEvent:
    name: str
    data: dict[str, Any] = field(default_factory=dict)


class _SSEBroker:
    def __init__(self) -> None:
        self._subscribers: list[asyncio.Queue[SSEEvent]] = []

    def subscribe(self) -> asyncio.Queue[SSEEvent]:
        q: asyncio.Queue[SSEEvent] = asyncio.Queue()
        self._subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue[SSEEvent]) -> None:
        try:
            self._subscribers.remove(q)
        except ValueError:
            pass

    async def publish(self, event: SSEEvent) -> None:
        for q in list(self._subscribers):
            await q.put(event)


broker = _SSEBroker()
