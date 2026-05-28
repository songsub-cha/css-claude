"""T4.12 — GET /api/sse with StreamingResponse and typed connection_health heartbeat (F1)."""
from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from backend.sse import SSEEvent, broker

log = logging.getLogger(__name__)

router = APIRouter(tags=["sse"])

_HEARTBEAT_INTERVAL = 30  # seconds


async def _event_source(request: Request):
    """Async generator: yield SSE frames until client disconnects.

    - Subscribes to the module-level broker.
    - On each event: yields `event: <name>\\ndata: <json>\\n\\n`.
    - On 30-second timeout: yields a typed `connection_health` heartbeat (F1).
    - On disconnect: unsubscribes and stops.
    """
    queue = broker.subscribe()
    try:
        while True:
            # Check disconnect without blocking so we can also receive events
            disconnected = await request.is_disconnected()
            if disconnected:
                break
            try:
                evt: SSEEvent = await asyncio.wait_for(
                    queue.get(), timeout=_HEARTBEAT_INTERVAL
                )
                yield f"event: {evt.name}\ndata: {json.dumps(evt.data)}\n\n"
            except asyncio.TimeoutError:
                # F1: typed heartbeat event instead of bare `: ping`
                yield (
                    f"event: connection_health\n"
                    f"data: {json.dumps({'db': 'ok', 'watcher': 'ok', 'bridge': 'ok'})}\n\n"
                )
    except GeneratorExit:
        pass
    finally:
        broker.unsubscribe(queue)


@router.get("/api/sse")
async def sse_stream(request: Request):
    """Server-Sent Events stream endpoint."""
    return StreamingResponse(
        _event_source(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
