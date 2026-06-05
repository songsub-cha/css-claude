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
            "skills", "spawn_agent", "wait_agent", "close_agent", "update_plan",
            "AskUserQuestion", "git-common-dir", "index.json", ".claude/css/",
            "single session model",
        ):
            self.assertIn(anchor, text, f"RUNTIME.md missing anchor: {anchor}")


class LiveInstallTests(unittest.TestCase):
    def test_install_real_repo(self):
        with tempfile.TemporaryDirectory() as h:
            home = Path(h)
            codex_home = home / ".codex"
            skills_home = home / ".agents" / "skills"
            summary = install(REPO_ROOT, codex_home, skills_home=skills_home)
            n_cmds = len(list((REPO_ROOT / "commands").glob("*.md")))
            n_agents = len(list((REPO_ROOT / "agents").glob("*.md")))
            self.assertEqual(n_cmds, 9)
            self.assertEqual(summary["skills"], n_cmds)
            self.assertEqual(summary["agents"], n_agents)

            skill_dirs = [p for p in skills_home.iterdir() if p.is_dir()]
            self.assertEqual(len(skill_dirs), n_cmds)
            ship = (skills_home / "css-ship" / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("name: css-ship", ship)
            self.assertIn("description:", ship)
            self.assertIn(".claude/css/", ship)
            self.assertIn("$ARGUMENTS", ship)
            self.assertNotIn("argument-hint", ship)

            index = json.loads((codex_home / "css" / "agents" / "index.json").read_text(encoding="utf-8"))
            self.assertEqual(len(index), n_agents)
            for rel in index.values():
                body = (codex_home / "css" / rel).read_text(encoding="utf-8")
                self.assertFalse(body.lstrip().startswith("---"))

    def test_real_sources_unchanged_after_install(self):
        def h(p):
            return hashlib.sha256(p.read_bytes()).hexdigest()

        before = {p: h(p) for p in (REPO_ROOT / "commands").glob("*.md")}
        before.update({p: h(p) for p in (REPO_ROOT / "agents").glob("*.md")})
        with tempfile.TemporaryDirectory() as home:
            install(REPO_ROOT, Path(home) / ".codex", skills_home=Path(home) / ".agents" / "skills")
        after = {p: h(p) for p in before}
        self.assertEqual(after, before)
