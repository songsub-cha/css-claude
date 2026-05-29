# tools/css_schema/test_schema.py
import unittest
from css_schema.schema import validate_manifest, SchemaError

VALID = [
    {"idx": 1, "label": "foundation", "batches": [1, 2], "depends_on": []},
    {"idx": 2, "label": "api",        "batches": [3],    "depends_on": [1]},
]

class TestManifest(unittest.TestCase):
    def test_valid_manifest_passes(self):
        validate_manifest(VALID)  # should not raise

    def test_empty_manifest_rejected(self):
        with self.assertRaises(SchemaError):
            validate_manifest([])

    def test_duplicate_idx_rejected(self):
        bad = [dict(VALID[0]), dict(VALID[0])]
        with self.assertRaises(SchemaError):
            validate_manifest(bad)

    def test_empty_batches_rejected(self):
        bad = [{"idx": 1, "label": "x", "batches": [], "depends_on": []}]
        with self.assertRaises(SchemaError):
            validate_manifest(bad)

    def test_forward_dependency_rejected(self):
        # depends_on must reference a smaller idx (acyclic + topological)
        bad = [{"idx": 1, "label": "x", "batches": [1], "depends_on": [2]},
               {"idx": 2, "label": "y", "batches": [2], "depends_on": []}]
        with self.assertRaises(SchemaError):
            validate_manifest(bad)

    def test_unknown_dependency_rejected(self):
        bad = [{"idx": 1, "label": "x", "batches": [1], "depends_on": [9]}]
        with self.assertRaises(SchemaError):
            validate_manifest(bad)

from css_schema.schema import validate_session

class TestSession(unittest.TestCase):
    def test_epic_session_ok(self):
        validate_session({"slug": "e", "kind": "epic",
                          "phases": {"interview": {"status": "completed"}}})

    def test_phase_session_ok(self):
        validate_session({"slug": "e-p1", "kind": "phase", "parent_slug": "e",
                          "phase_index": 1, "depends_on": [], "base_branch": "main",
                          "phases": {"execute": {"status": "pending"}}})

    def test_legacy_session_without_kind_treated_as_epic(self):
        # backward compat (D9): no 'kind' -> valid single-Phase epic
        validate_session({"slug": "old", "phases": {"interview": {"status": "completed"}}})

    def test_phase_session_missing_parent_rejected(self):
        with self.assertRaises(SchemaError):
            validate_session({"slug": "e-p1", "kind": "phase",
                              "phase_index": 1, "base_branch": "main", "phases": {}})

    def test_bad_kind_rejected(self):
        with self.assertRaises(SchemaError):
            validate_session({"slug": "e", "kind": "nonsense", "phases": {}})

    def test_missing_slug_rejected(self):
        with self.assertRaises(SchemaError):
            validate_session({"kind": "epic", "phases": {}})

import json, pathlib
from css_schema.schema import validate_active

FX = pathlib.Path(__file__).parent / "fixtures"

class TestActiveAndFixtures(unittest.TestCase):
    def test_active_minimal(self):
        validate_active({"latest_slug": "e"})

    def test_active_with_epic_and_phase(self):
        validate_active({"latest_slug": "e-p1", "active_epic": "e", "active_phase": 1})

    def test_active_requires_latest_slug(self):
        with self.assertRaises(SchemaError):
            validate_active({})

    def test_fixtures_are_valid(self):
        validate_manifest(json.loads((FX / "valid_manifest.json").read_text(encoding="utf-8")))
        validate_session(json.loads((FX / "epic_session.json").read_text(encoding="utf-8")))
        validate_session(json.loads((FX / "phase_session.json").read_text(encoding="utf-8")))

if __name__ == "__main__":
    unittest.main()
