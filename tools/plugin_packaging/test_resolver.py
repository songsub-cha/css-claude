import os
import shutil
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SHIP = REPO / "commands" / "ship.md"

RESOLVER = (
    'CSS_PLUGIN_DIR="${CLAUDE_PLUGIN_ROOT}"; '
    'CSS_PLUGIN_DIR="${CSS_PLUGIN_DIR:-$HOME/.claude/css}"; '
    'printf "%s" "${CSS_LIB:-$CSS_PLUGIN_DIR/lib}"'
)


class ShipResolverTests(unittest.TestCase):
    def test_ship_embeds_dual_mode_resolver(self):
        text = SHIP.read_text(encoding="utf-8")
        self.assertIn('CSS_PLUGIN_DIR="${CLAUDE_PLUGIN_ROOT}"', text)
        self.assertIn('CSS_PLUGIN_DIR="${CSS_PLUGIN_DIR:-$HOME/.claude/css}"', text)
        self.assertIn('"${CSS_LIB:-$CSS_PLUGIN_DIR/lib}/gh_sync.sh"', text)

    def test_ship_never_assigns_install_dir_to_css_root(self):
        # gh_sync.sh reads CSS_ROOT as the *project* root for session lookup;
        # ship must not reuse that name for the plugin/install dir.
        text = SHIP.read_text(encoding="utf-8")
        self.assertNotIn('CSS_ROOT="${CLAUDE_PLUGIN_ROOT}"', text)
        self.assertNotIn('CSS_ROOT="${CSS_ROOT:-', text)

    def _resolve(self, **overrides):
        bash = shutil.which("bash")
        if bash is None:
            self.skipTest("bash not available")
        env = dict(os.environ)
        env.pop("CSS_LIB", None)
        env.pop("CLAUDE_PLUGIN_ROOT", None)
        env.pop("CSS_PLUGIN_DIR", None)
        env.update(overrides)
        return subprocess.run(
            [bash, "-c", RESOLVER], capture_output=True, text=True, env=env
        ).stdout

    def test_plugin_mode(self):
        self.assertEqual(
            self._resolve(CLAUDE_PLUGIN_ROOT="/x/plug", HOME="/home/u"), "/x/plug/lib"
        )

    def test_script_mode(self):
        self.assertEqual(self._resolve(HOME="/home/u"), "/home/u/.claude/css/lib")

    def test_explicit_css_lib_wins(self):
        self.assertEqual(
            self._resolve(CSS_LIB="/custom/lib", CLAUDE_PLUGIN_ROOT="/x/plug"),
            "/custom/lib",
        )
