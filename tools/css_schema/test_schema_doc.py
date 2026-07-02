"""Keep docs/session-schema.md — the human-readable schema reference — in sync
with the field names the commands, gh_sync, and the machine schema rely on."""
from __future__ import annotations

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DOC = REPO / "docs" / "session-schema.md"

# Field names that appear in command prompts, gh_sync.sh reads, or schema.py.
CONTRACT_MARKERS = (
    "rich_specs",
    "advisories",
    "findings",
    "commit_count",
    "test_summary",
    "coverage_pct",
    "gates.gate2_pre_execute",
    "gates.gate3_pre_pr",
    "retries",
    "base_branch",
    "language_profile",
    "phase_manifest",
    "parent_session",
    "_active.json",
    "last-writer-wins",
    "locks/{slug}-{stage}.lock",
    "worktree_parent",
    "coverage_threshold",
    "max_loopback_attempts",
    "tdd_self_heal_max",
)


class SchemaDocTests(unittest.TestCase):
    def test_doc_exists(self):
        self.assertTrue(DOC.exists(), "docs/session-schema.md is missing")

    def test_doc_covers_contract_fields(self):
        text = DOC.read_text(encoding="utf-8")
        for marker in CONTRACT_MARKERS:
            self.assertIn(marker, text, f"session-schema.md missing {marker!r}")


if __name__ == "__main__":
    unittest.main()
