"""T4.11 RED scaffold — SSEBroker: fan-out, unsubscribe, bounded drop-on-full.

Phase 2 (dashboard-epic-phase-view-p2): diff_phase_events (T9) derives
phase_started / phase_pr_opened / phase_completed from a phase session.
"""
import asyncio
from pathlib import Path

import pytest
from backend.sse import SSEBroker, SSEEvent
from backend.services.session_reader import ParsedSession
from backend.watcher import diff_phase_events


def _phase(stage_statuses, pr=None, *, kind="phase", phase_index=2):
    phases = {k: {"status": v} for k, v in stage_statuses.items()}
    if pr is not None:
        phases["pr"] = pr
    return ParsedSession(
        slug="epic-x-p2", idea="", repo_root="/r", repo_name="r",
        current_phase="execute", phases=phases, gates={}, master_flow=False,
        file_path=Path("x"), mtime=0.0, kind=kind, parent_slug="epic-x",
        phase_index=phase_index, phase_label="API", depends_on=[1],
    )


def test_phase_started_emitted_once():
    s = _phase({"execute": "in_progress"})
    events, state = diff_phase_events({}, s)
    started = [e for e in events if e.name == "phase_started"]
    assert len(started) == 1
    assert started[0].data == {"slug": "epic-x-p2", "parent_slug": "epic-x", "phase_index": 2}
    # idempotent: same parsed + returned state -> no duplicate
    events2, _ = diff_phase_events(state, s)
    assert events2 == []


def test_phase_pr_opened_and_completed():
    s = _phase({"execute": "completed"},
               pr={"status": "completed", "artifact": "https://gh/x/y/pull/3"})
    events, state = diff_phase_events({}, s)
    names = {e.name for e in events}
    assert {"phase_pr_opened", "phase_completed"} <= names
    pe = next(e for e in events if e.name == "phase_pr_opened")
    assert pe.data["pr_url"] == "https://gh/x/y/pull/3"
    events2, _ = diff_phase_events(state, s)
    assert events2 == []


def test_epic_or_legacy_session_emits_no_phase_events():
    s = _phase({"execute": "in_progress"}, kind="epic")
    events, state = diff_phase_events({}, s)
    assert events == [] and state == {}


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
