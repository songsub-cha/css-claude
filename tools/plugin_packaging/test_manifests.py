import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


class PluginManifestTests(unittest.TestCase):
    def _load(self):
        p = REPO / ".claude-plugin" / "plugin.json"
        self.assertTrue(p.exists(), "plugin.json missing")
        return json.loads(p.read_text(encoding="utf-8"))

    def test_name_is_css(self):
        self.assertEqual(self._load()["name"], "css")

    def test_has_version_and_description(self):
        m = self._load()
        self.assertEqual(m["version"], "0.1.0")
        self.assertTrue(m.get("description"))

    def test_omits_component_fields(self):
        # Auto-discovery must own commands/ and agents/.
        m = self._load()
        self.assertNotIn("commands", m)
        self.assertNotIn("agents", m)


class MarketplaceManifestTests(unittest.TestCase):
    def _load(self):
        p = REPO / ".claude-plugin" / "marketplace.json"
        self.assertTrue(p.exists(), "marketplace.json missing")
        return json.loads(p.read_text(encoding="utf-8"))

    def test_name_and_owner(self):
        m = self._load()
        self.assertEqual(m["name"], "css-claude")
        self.assertTrue(m["owner"]["name"])

    def test_lists_css_plugin_at_repo_root(self):
        plugins = self._load()["plugins"]
        entry = next(p for p in plugins if p["name"] == "css")
        self.assertEqual(entry["source"], "./")
