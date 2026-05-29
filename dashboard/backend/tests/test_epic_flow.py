"""Phase 2 (dashboard-epic-phase-view-p2) — epic_flow graph assembly (T6)."""
from pathlib import Path

from backend.services.session_reader import ParsedSession, EpicGroup
from backend.services.epic_flow import build_epic_flow


def _phase(slug, idx, depends_on, *, stage="execute", pr_status="pending", pr_url=None):
    pr = {"status": pr_status}
    if pr_url:
        pr["artifact"] = pr_url
    return ParsedSession(
        slug=slug, idea="", repo_root="/r", repo_name="r",
        current_phase=stage, phases={"pr": pr}, gates={}, master_flow=False,
        file_path=Path(slug), mtime=0.0,
        kind="phase", parent_slug="epic-x", phase_index=idx,
        phase_label=f"label-{idx}", depends_on=depends_on,
    )


def _epic(slug="epic-x", stage="review"):
    return ParsedSession(
        slug=slug, idea="the epic", repo_root="/r", repo_name="r",
        current_phase=stage, phases={}, gates={}, master_flow=True,
        file_path=Path(slug), mtime=0.0, kind="epic",
    )


def test_build_flow_nodes_and_edges():
    group = EpicGroup(epic=_epic(), phases=[
        _phase("epic-x-p1", 1, []),
        _phase("epic-x-p2", 2, [1]),
        _phase("epic-x-p3", 3, [2]),
    ])
    flow = build_epic_flow(group)
    assert flow["epic"]["slug"] == "epic-x"
    assert [n["phase_index"] for n in flow["nodes"]] == [1, 2, 3]
    assert flow["nodes"][0]["phase_label"] == "label-1"
    assert flow["nodes"][0]["current_stage"] == "execute"
    assert flow["edges"] == [{"from": 1, "to": 2}, {"from": 2, "to": 3}]


def test_pr_status_open_when_artifact_present():
    group = EpicGroup(epic=_epic(), phases=[
        _phase("epic-x-p1", 1, [], pr_status="completed",
               pr_url="https://github.com/x/y/pull/3"),
    ])
    node = build_epic_flow(group)["nodes"][0]
    assert node["pr_status"] == "open"
    assert node["pr_url"] == "https://github.com/x/y/pull/3"


def test_legacy_single_phase_epic_one_node_no_edges():
    # epic only, no child phases -> synthetic single node, no edges
    group = EpicGroup(epic=_epic(slug="old-feat", stage="plan"), phases=[])
    flow = build_epic_flow(group)
    assert flow["epic"]["slug"] == "old-feat"
    assert len(flow["nodes"]) == 1
    assert flow["nodes"][0]["phase_index"] == 1
    assert flow["nodes"][0]["current_stage"] == "plan"
    assert flow["edges"] == []


def test_orphan_group_epic_none():
    group = EpicGroup(epic=None, phases=[_phase("ghost-p1", 1, [])])
    flow = build_epic_flow(group)
    assert flow["epic"] is None
    assert [n["phase_index"] for n in flow["nodes"]] == [1]
    assert flow["edges"] == []
