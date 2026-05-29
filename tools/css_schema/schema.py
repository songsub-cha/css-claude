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


_VALID_KINDS = {"epic", "phase"}
_PHASE_REQUIRED = ("parent_slug", "phase_index", "base_branch")


def validate_session(obj: dict) -> None:
    if not isinstance(obj, dict):
        raise SchemaError("session must be an object")
    if not obj.get("slug"):
        raise SchemaError("session requires a non-empty slug")
    kind = obj.get("kind", "epic")  # D9: legacy (no kind) -> epic
    if kind not in _VALID_KINDS:
        raise SchemaError(f"kind must be one of {_VALID_KINDS}, got {kind!r}")
    if "phases" not in obj or not isinstance(obj["phases"], dict):
        raise SchemaError("session requires a 'phases' object")
    if "phase_manifest" in obj:
        validate_manifest(obj["phase_manifest"])
    if kind == "phase":
        for f in _PHASE_REQUIRED:
            if f not in obj:
                raise SchemaError(f"phase session missing required field {f!r}")
        if not isinstance(obj["phase_index"], int) or obj["phase_index"] < 1:
            raise SchemaError("phase_index must be int >= 1")
        if not isinstance(obj.get("depends_on", []), list):
            raise SchemaError("depends_on must be a list")


def validate_active(obj: dict) -> None:
    if not isinstance(obj, dict) or not obj.get("latest_slug"):
        raise SchemaError("_active.json requires a non-empty latest_slug")
    if "active_phase" in obj and not isinstance(obj["active_phase"], int):
        raise SchemaError("active_phase must be an int when present")
