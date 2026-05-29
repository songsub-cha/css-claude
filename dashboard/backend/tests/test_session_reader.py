"""T4.3 — session_reader tests (css-async-coder spec).

Phase 1 (dashboard-epic-phase-view-p1) additions: Epic/Phase hierarchy parsing
(T3) and grouping child Phases under their Epic (T4).
"""
import json
from pathlib import Path
from backend.services.session_reader import (
    parse_session_file,
    list_sessions_for_project,
    group_sessions_by_epic,
    EpicGroup,
)


def make_session(tmp_path: Path, slug: str, phase: str, **hierarchy) -> Path:
    """Write a session JSON. Extra hierarchy kwargs (kind/parent_slug/phase_index/
    phase_label/depends_on) are merged in when provided; omitting them yields a
    legacy (pre-hierarchy) session for backward-compat tests."""
    d = tmp_path / ".claude" / "css" / "sessions"
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{slug}.json"
    body = {
        "slug": slug,
        "idea": "x",
        "master_flow": True,
        "repo_root": str(tmp_path),
        "repo_name": tmp_path.name,
        "current_phase": phase,
        "phases": {p: {"status": "pending"} for p in
                   ["interview", "plan", "review", "execute", "verify", "document", "pr"]},
        "gates": {"gate2_pre_execute": None, "gate3_pre_pr": None},
    }
    body.update(hierarchy)
    f.write_text(json.dumps(body))
    return f


def test_parse_session_file(tmp_path):
    f = make_session(tmp_path, "feat-x", "plan")
    p = parse_session_file(f)
    assert p.slug == "feat-x" and p.current_phase == "plan" and p.repo_name == tmp_path.name


def test_list_sessions_for_project(tmp_path):
    make_session(tmp_path, "feat-a", "review")
    make_session(tmp_path, "feat-b", "execute")
    assert sorted(s.slug for s in list_sessions_for_project(tmp_path)) == ["feat-a", "feat-b"]


def test_corrupted_json_returns_none(tmp_path):
    d = tmp_path / ".claude/css/sessions"
    d.mkdir(parents=True)
    (d / "broken.json").write_text("{not json")
    assert parse_session_file(d / "broken.json") is None


# ── T3: Epic/Phase hierarchy parsing (legacy-tolerant) ──────────────────────────

def test_parse_phase_session_fields(tmp_path):
    f = make_session(
        tmp_path, "epic-x-p2", "execute",
        kind="phase", parent_slug="epic-x", phase_index=2,
        phase_label="API layer", depends_on=[1],
    )
    p = parse_session_file(f)
    assert p.kind == "phase"
    assert p.parent_slug == "epic-x"
    assert p.phase_index == 2
    assert p.phase_label == "API layer"
    assert p.depends_on == [1]
    assert p.is_phase is True


def test_parse_legacy_session_defaults_to_epic(tmp_path):
    # D9: a session with no `kind` renders as a single-Phase Epic.
    f = make_session(tmp_path, "old-feat", "plan")
    p = parse_session_file(f)
    assert p.kind == "epic"
    assert p.parent_slug is None
    assert p.phase_index is None
    assert p.depends_on == []
    assert p.is_phase is False


# ── T4: group child Phases under their Epic ─────────────────────────────────────

def test_group_sessions_by_epic(tmp_path):
    make_session(tmp_path, "epic-x", "review", kind="epic")
    make_session(tmp_path, "epic-x-p2", "execute",
                 kind="phase", parent_slug="epic-x", phase_index=2, depends_on=[1])
    make_session(tmp_path, "epic-x-p1", "verify",
                 kind="phase", parent_slug="epic-x", phase_index=1, depends_on=[])
    sessions = list_sessions_for_project(tmp_path)
    groups = group_sessions_by_epic(sessions)

    assert isinstance(groups["epic-x"], EpicGroup)
    g = groups["epic-x"]
    assert g.epic is not None and g.epic.slug == "epic-x"
    # phases ordered by phase_index
    assert [p.phase_index for p in g.phases] == [1, 2]


def test_legacy_session_forms_single_phase_epic_group(tmp_path):
    # D9: a lone legacy session is its own Epic group with no child phases.
    make_session(tmp_path, "old-feat", "plan")
    groups = group_sessions_by_epic(list_sessions_for_project(tmp_path))
    assert "old-feat" in groups
    assert groups["old-feat"].epic.slug == "old-feat"
    assert groups["old-feat"].phases == []


def test_orphan_phase_does_not_crash(tmp_path):
    # Corruption tolerance: a phase whose parent Epic file is missing still
    # surfaces under a group keyed by its parent_slug (epic=None).
    make_session(tmp_path, "ghost-p1", "execute",
                 kind="phase", parent_slug="ghost", phase_index=1, depends_on=[])
    groups = group_sessions_by_epic(list_sessions_for_project(tmp_path))
    assert "ghost" in groups
    assert groups["ghost"].epic is None
    assert [p.slug for p in groups["ghost"].phases] == ["ghost-p1"]
