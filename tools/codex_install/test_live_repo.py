"""Tests against the real repo: RUNTIME.md lint + transform of live sources."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from codex_install.installer import install

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


class LiveInstallTests(unittest.TestCase):
    def test_install_real_repo(self):
        with tempfile.TemporaryDirectory() as d:
            dest = Path(d)
            summary = install(REPO_ROOT, dest)
            # Counts match the live source tree.
            n_cmds = len(list((REPO_ROOT / "commands").glob("*.md")))
            n_agents = len(list((REPO_ROOT / "agents").glob("*.md")))
            self.assertEqual(summary["commands"], n_cmds)
            self.assertEqual(summary["agents"], n_agents)
            # ship prompt exists and preserves the shared state path + args.
            ship = (dest / "prompts" / "css-ship.md").read_text(encoding="utf-8")
            self.assertIn(".claude/css/", ship)
            self.assertIn("$ARGUMENTS", ship)
            # index.json covers exactly the agent set; every agent body has no
            # leftover frontmatter.
            index = json.loads((dest / "css" / "agents" / "index.json").read_text(encoding="utf-8"))
            self.assertEqual(len(index), n_agents)
            for rel in index.values():
                body = (dest / "css" / rel).read_text(encoding="utf-8")
                self.assertFalse(body.lstrip().startswith("---"))

    def test_real_sources_unchanged_after_install(self):
        def h(p):
            return hashlib.sha256(p.read_bytes()).hexdigest()

        before = {p: h(p) for p in (REPO_ROOT / "commands").glob("*.md")}
        before.update({p: h(p) for p in (REPO_ROOT / "agents").glob("*.md")})
        with tempfile.TemporaryDirectory() as d:
            install(REPO_ROOT, Path(d))
        after = {p: h(p) for p in before}
        self.assertEqual(after, before)
