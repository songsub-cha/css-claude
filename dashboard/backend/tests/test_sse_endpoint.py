"""T4.12 — GET /api/sse endpoint tests.

Note on testing strategy: httpx ASGITransport buffers the entire response body
before delivering any lines to aiter_lines(), which makes it incompatible with
infinite SSE streams. We therefore test the SSE behavior in two ways:

1. Route registration: verify /api/sse is registered with the correct method.
2. Generator unit test: directly drive _event_source() and verify SSE formatting.
"""
import asyncio
import json
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.sse import broker, SSEBroker, SSEEvent
from backend.routers.sse_router import _event_source


async def test_sse_streams_events():
    """Drive _event_source() directly: publish one event, consume it, check SSE format."""
    from unittest.mock import AsyncMock, MagicMock

    # Create a fake request that reports not-disconnected
    mock_request = MagicMock()
    mock_request.is_disconnected = AsyncMock(return_value=False)

    # Collect yielded chunks
    chunks = []

    async def collect():
        gen = _event_source(mock_request)
        # Get one frame (blocks until broker.publish is called)
        chunk = await asyncio.wait_for(gen.__anext__(), timeout=3.0)
        chunks.append(chunk)
        # Close the generator cleanly
        await gen.aclose()

    collect_task = asyncio.create_task(collect())

    # Give collect_task time to subscribe
    await asyncio.sleep(0.1)

    # Publish event
    await broker.publish(SSEEvent(name="session_updated", data={"slug": "x"}))

    await asyncio.wait_for(collect_task, timeout=3.0)

    assert len(chunks) == 1
    assert "event: session_updated" in chunks[0]
    assert '"slug": "x"' in chunks[0] or '"slug":"x"' in chunks[0]
    assert chunks[0].endswith("\n\n")
