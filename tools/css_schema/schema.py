"""Validation for Epic/Phase session JSON, phase_manifest, and _active.json."""
from __future__ import annotations


class SchemaError(ValueError):
    """Raised when a CSS session/manifest artifact violates the contract."""


def validate_manifest(manifest: object) -> None:
    if not isinstance(manifest, list) or not manifest:
        raise SchemaError("phase_manifest must be a non-empty list")
    seen: set[int] = set()
    for p in manifest:
        if not isinstance(p, dict):
            raise SchemaError("each phase must be an object")
        idx = p.get("idx")
        if not isinstance(idx, int) or idx < 1:
            raise SchemaError(f"phase idx must be int >= 1, got {idx!r}")
        if idx in seen:
            raise SchemaError(f"duplicate phase idx {idx}")
        seen.add(idx)
        if not isinstance(p.get("label"), str) or not p["label"].strip():
            raise SchemaError(f"phase {idx} needs a non-empty label")
        if not isinstance(p.get("batches"), list) or not p["batches"]:
            raise SchemaError(f"phase {idx} needs a non-empty batches list")
        deps = p.get("depends_on", [])
        if not isinstance(deps, list):
            raise SchemaError(f"phase {idx} depends_on must be a list")
        for d in deps:
            if d not in seen or d >= idx:
                # must reference an already-seen, strictly-smaller idx -> acyclic
                raise SchemaError(
                    f"phase {idx} depends_on {d}: must be an existing smaller idx")
