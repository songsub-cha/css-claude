"""Pure derivation helpers for Epic/Phase slugs, branches, and the phasing trigger."""
from __future__ import annotations


def should_phase(task_count: int, batch_count: int) -> bool:
    """True when an idea is large enough to split into Phases (D7)."""
    return task_count > 20 or batch_count > 4


def phase_slug(epic_slug: str, idx: int) -> str:
    return f"{epic_slug}-p{idx}"


def phase_branch(epic_slug: str, idx: int) -> str:
    return f"css/{epic_slug}/p{idx}"


def _find_phase(manifest: list[dict], idx: int) -> dict:
    for p in manifest:
        if p["idx"] == idx:
            return p
    raise KeyError(f"phase idx {idx} not in manifest")


def base_branch_for(manifest: list[dict], idx: int, epic_slug: str,
                    epic_base: str = "main") -> str:
    """Branch a Phase forks from. Independent (depends_on=[]) -> epic_base;
    otherwise stack on the highest-indexed dependency (linear stack)."""
    deps = _find_phase(manifest, idx).get("depends_on", [])
    if not deps:
        return epic_base
    return phase_branch(epic_slug, max(deps))
