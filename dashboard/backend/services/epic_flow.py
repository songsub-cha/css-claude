"""Phase 2 (dashboard-epic-phase-view-p2) — assemble an Epic -> Phase flow graph.

Pure functions over p1's `EpicGroup`: nodes (one per Phase, carrying the current
Stage + PR status) and dependency edges (from each Phase's `depends_on`). Consumed
by the sessions/projects routers (T7/T8) and, ultimately, the frontend flow view.
"""
from __future__ import annotations

from typing import Optional

from backend.services.session_reader import EpicGroup, ParsedSession


def _pr_fields(session: ParsedSession) -> tuple[str, Optional[str]]:
    """Return (pr_status, pr_url). A present PR artifact means the PR is open."""
    pr = session.phases.get("pr", {}) if isinstance(session.phases, dict) else {}
    if not isinstance(pr, dict):
        pr = {}
    pr_url = pr.get("artifact")
    pr_status = "open" if pr_url else pr.get("status", "pending")
    return pr_status, pr_url


def _node(phase_index: int, phase_label: Optional[str], session: ParsedSession) -> dict:
    pr_status, pr_url = _pr_fields(session)
    return {
        "phase_index": phase_index,
        "phase_label": phase_label,
        "current_stage": session.current_phase,
        "pr_status": pr_status,
        "pr_url": pr_url,
    }


def build_epic_flow(group: EpicGroup) -> dict:
    """Build {epic, nodes, edges} for one Epic group.

    - nodes: one per child Phase (ordered by phase_index). An Epic with no child
      Phases (legacy/single-Phase, D9) yields a single synthetic node at index 1.
    - edges: {"from": d, "to": idx} for every d in each Phase's depends_on.
    - epic: {slug, label} or None for an orphan group (parent Epic missing).
    """
    epic_block = (
        {"slug": group.epic.slug, "label": group.epic.idea or group.epic.slug}
        if group.epic is not None
        else None
    )

    if not group.phases:
        # Legacy / single-Phase Epic: synthesize one node from the Epic itself.
        if group.epic is None:
            return {"epic": None, "nodes": [], "edges": []}
        node = _node(1, group.epic.idea or group.epic.slug, group.epic)
        return {"epic": epic_block, "nodes": [node], "edges": []}

    nodes: list[dict] = []
    edges: list[dict] = []
    for phase in group.phases:
        idx = phase.phase_index if phase.phase_index is not None else 0
        nodes.append(_node(idx, phase.phase_label, phase))
        for dep in phase.depends_on:
            edges.append({"from": dep, "to": idx})

    return {"epic": epic_block, "nodes": nodes, "edges": edges}
