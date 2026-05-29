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

if __name__ == "__main__":
    unittest.main()
