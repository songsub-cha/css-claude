"""Installer tests: layout, idempotency, config guard, source untouched."""
from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from codex_install.__main__ import main as cli_main
from codex_install.installer import install

_CMD = "---\ndescription: stage\nargument-hint: x\n---\n\n# /css:demo\nuse .claude/css/ and $ARGUMENTS\n"
_AGENT = "---\nname: css-demo\nmodel: opus\ncss_stages: [review]\n---\n\n<Agent_Prompt>body</Agent_Prompt>\n"
_CONFIG = '{"k": 1}\n'
_RUNTIME = "# RUNTIME\nskills / spawn_agent / wait_agent / update_plan / AskUserQuestion / git-common-dir / index.json\n"


def _make_source(root: Path) -> None:
    (root / "commands").mkdir(parents=True)
    (root / "agents").mkdir(parents=True)
    (root / "config").mkdir(parents=True)
    (root / "codex").mkdir(parents=True)
    (root / "commands" / "demo.md").write_text(_CMD, encoding="utf-8")
    (root / "agents" / "demo.md").write_text(_AGENT, encoding="utf-8")
    (root / "config" / "default-config.json").write_text(_CONFIG, encoding="utf-8")
    (root / "codex" / "RUNTIME.md").write_text(_RUNTIME, encoding="utf-8")


def _tree_hashes(root: Path) -> dict:
    return {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*")) if p.is_file()
    }


class InstallerTests(unittest.TestCase):
    def test_install_creates_expected_layout(self):
        with tempfile.TemporaryDirectory() as s, tempfile.TemporaryDirectory() as h:
            src, home = Path(s), Path(h)
            codex_home = home / ".codex"
            skills_home = home / ".agents" / "skills"
            _make_source(src)
            summary = install(src, codex_home, skills_home=skills_home)
            self.assertEqual(summary, {"skills": 1, "agents": 1, "config_written": True})
            self.assertTrue((skills_home / "css-demo" / "SKILL.md").exists())
            self.assertTrue((codex_home / "css" / "agents" / "demo.md").exists())
            self.assertTrue((codex_home / "css" / "agents" / "index.json").exists())
            self.assertTrue((codex_home / "css" / "RUNTIME.md").exists())
            self.assertTrue((codex_home / "css" / "config.json").exists())

    def test_idempotent(self):
        with tempfile.TemporaryDirectory() as s, tempfile.TemporaryDirectory() as h:
            src, home = Path(s), Path(h)
            codex_home = home / ".codex"
            skills_home = home / ".agents" / "skills"
            _make_source(src)
            install(src, codex_home, skills_home=skills_home)
            first = _tree_hashes(home)
            install(src, codex_home, skills_home=skills_home)
            self.assertEqual(_tree_hashes(home), first)

    def test_config_not_overwritten_without_force(self):
        with tempfile.TemporaryDirectory() as s, tempfile.TemporaryDirectory() as h:
            src, home = Path(s), Path(h)
            codex_home = home / ".codex"
            skills_home = home / ".agents" / "skills"
            _make_source(src)
            install(src, codex_home, skills_home=skills_home)
            cfg = codex_home / "css" / "config.json"
            cfg.write_text('{"local": true}\n', encoding="utf-8")
            install(src, codex_home, skills_home=skills_home)  # no force
            self.assertIn("local", cfg.read_text(encoding="utf-8"))
            install(src, codex_home, force=True, skills_home=skills_home)
            self.assertNotIn("local", cfg.read_text(encoding="utf-8"))

    def test_source_files_untouched(self):
        with tempfile.TemporaryDirectory() as s, tempfile.TemporaryDirectory() as h:
            src, home = Path(s), Path(h)
            _make_source(src)
            before = _tree_hashes(src)
            install(src, home / ".codex", skills_home=home / ".agents" / "skills")
            self.assertEqual(_tree_hashes(src), before)
            self.assertIn("model: opus", (src / "agents" / "demo.md").read_text(encoding="utf-8"))

    def test_transformed_skill_preserves_state_path_and_args(self):
        with tempfile.TemporaryDirectory() as s, tempfile.TemporaryDirectory() as h:
            src, home = Path(s), Path(h)
            codex_home = home / ".codex"
            skills_home = home / ".agents" / "skills"
            _make_source(src)
            install(src, codex_home, skills_home=skills_home)
            skill = (skills_home / "css-demo" / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("name: css-demo", skill)
            self.assertIn("description: stage", skill)
            self.assertIn(".claude/css/", skill)
            self.assertIn("$ARGUMENTS", skill)
            self.assertNotIn("argument-hint", skill)


class CliTests(unittest.TestCase):
    def test_cli_main_installs(self):
        with tempfile.TemporaryDirectory() as s, tempfile.TemporaryDirectory() as h:
            src, home = Path(s), Path(h)
            codex_home = home / ".codex"
            skills_home = home / ".agents" / "skills"
            _make_source(src)
            rc = cli_main([
                "--source", str(src),
                "--dest", str(codex_home),
                "--skills-dir", str(skills_home),
            ])
            self.assertEqual(rc, 0)
            self.assertTrue((skills_home / "css-demo" / "SKILL.md").exists())
