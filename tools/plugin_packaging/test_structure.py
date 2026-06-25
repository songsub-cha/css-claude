import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


class ComponentDiscoveryTests(unittest.TestCase):
    def test_no_locale_files_in_components(self):
        for d in ("commands", "agents"):
            stray = sorted(p.name for p in (REPO / d).glob("*.ko.md"))
            self.assertEqual(stray, [], f"{d}/ still has locale files: {stray}")

    def test_component_md_have_plain_stems(self):
        # Plugin auto-discovery derives the command/agent name from the stem.
        for d in ("commands", "agents"):
            for p in (REPO / d).glob("*.md"):
                self.assertNotIn(".", p.stem, f"{p.name} has a dotted stem")

    def test_i18n_holds_translations(self):
        self.assertEqual(len(list((REPO / "i18n" / "commands").glob("*.ko.md"))), 9)
        self.assertEqual(len(list((REPO / "i18n" / "agents").glob("*.ko.md"))), 21)


class DocsTests(unittest.TestCase):
    def test_readmes_document_plugin_install(self):
        for name in ("README.md", "README.en.md"):
            text = (REPO / name).read_text(encoding="utf-8")
            self.assertIn("/plugin marketplace add", text, f"{name} missing plugin install")
            self.assertIn("css@css-claude", text, f"{name} missing install target")
