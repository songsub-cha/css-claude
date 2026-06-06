"""Validation for task-scoped executable CSS Rich Specs."""
from __future__ import annotations

import re
from pathlib import Path


class RichSpecError(ValueError):
    """Raised when an executable Rich Spec violates the canonical contract."""


REQUIRED_FIELDS = (
    "Specialist:",
    "Phase:",
    "Files:",
    "Verification mode: command",
    "RED scaffold:",
    "RED command:",
    "GREEN template:",
    "GREEN command:",
    "Edge cases:",
    "Depends-on:",
    "Cross_Domain_Notes:",
)


def validate_rich_spec(
    text: str, *, expected_task_id: str, expected_phase: int
) -> dict[str, str]:
    """Validate one task-scoped artifact and return its core identity fields."""
    if "advisory-" in text.lower():
        raise RichSpecError("advisory reports are not executable Rich Specs")
    heading = f"## Task {expected_task_id}"
    if text.count(heading) != 1:
        raise RichSpecError(f"missing task heading {heading!r}")
    for field in REQUIRED_FIELDS:
        if field not in text:
            raise RichSpecError(f"missing required field {field!r}")
    phase = re.search(r"^Phase:\s*(\d+)\s*$", text, re.MULTILINE)
    if not phase or int(phase.group(1)) != expected_phase:
        raise RichSpecError(f"expected Phase: {expected_phase}")
    artifact = re.search(r"^ARTIFACT=(\S+)\s*$", text, re.MULTILINE)
    if not artifact:
        raise RichSpecError("missing final ARTIFACT=<path>")
    if text.rstrip().splitlines()[-1] != f"ARTIFACT={artifact.group(1)}":
        raise RichSpecError("ARTIFACT line must be final")
    specialist = re.search(r"^Specialist:\s*(\S+)\s*$", text, re.MULTILINE)
    if not specialist:
        raise RichSpecError("Specialist must name one agent")
    return {
        "task_id": expected_task_id,
        "phase": phase.group(1),
        "specialist": specialist.group(1),
        "artifact": artifact.group(1),
    }


def validate_rich_spec_file(
    path: str | Path, *, expected_task_id: str, expected_phase: int
) -> dict[str, str]:
    return validate_rich_spec(
        Path(path).read_text(encoding="utf-8"),
        expected_task_id=expected_task_id,
        expected_phase=expected_phase,
    )
