"""T4.11 RED scaffold — SSEBroker: fan-out, unsubscribe, bounded drop-on-full."""
import asyncio
import pytest
from backend.sse import SSEBroker, SSEEvent


async def test_broker_fans_out_to_multiple_subscribers():
    b = SSEBroker()
    q1 = b.subscribe()
    q2 = b.subscribe()
    await b.publish(SSEEvent(name="session_updated", data={"slug": "x"}))
    e1 = await asyncio.wait_for(q1.get(), 0.5)
    e2 = await asyncio.wait_for(q2.get(), 0.5)
    assert e1.name == "session_updated" and e2.data["slug"] == "x"


async def test_unsubscribe_removes_queue():
    b = SSEBroker()
    q = b.subscribe()
    b.unsubscribe(q)
    await b.publish(SSEEvent(name="x", data={}))
    assert q.empty()
