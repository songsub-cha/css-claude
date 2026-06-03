"""Tests against the real repo: RUNTIME.md lint + transform of live sources."""
from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


class RuntimeDocTests(unittest.TestCase):
    def test_runtime_doc_has_required_mappings(self):
        text = (REPO_ROOT / "codex" / "RUNTIME.md").read_text(encoding="utf-8")
        for anchor in (
            "spawn_agent", "wait_agent", "close_agent", "update_plan",
            "AskUserQuestion", "git-common-dir", "index.json",
            ".claude/css/", "단일 모델",
        ):
            self.assertIn(anchor, text, f"RUNTIME.md missing anchor: {anchor}")
