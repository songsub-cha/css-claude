# tools/css_schema/test_derive.py
import unittest
from css_schema.derive import should_phase, phase_slug, phase_branch, base_branch_for

MANIFEST = [
    {"idx": 1, "label": "foundation", "batches": [1, 2], "depends_on": []},
    {"idx": 2, "label": "api",        "batches": [3],    "depends_on": [1]},
    {"idx": 3, "label": "ui",         "batches": [4, 5], "depends_on": [2]},
]

class TestDerive(unittest.TestCase):
    def test_should_phase_threshold(self):
        self.assertFalse(should_phase(20, 4))   # at limit -> single session
        self.assertTrue(should_phase(21, 1))    # task_count > 20
        self.assertTrue(should_phase(5, 5))     # batch_count > 4

    def test_phase_slug_and_branch(self):
        self.assertEqual(phase_slug("epic-x", 2), "epic-x-p2")
        self.assertEqual(phase_branch("epic-x", 2), "css/epic-x/p2")

    def test_base_branch_independent_phase_uses_epic_base(self):
        self.assertEqual(base_branch_for(MANIFEST, 1, "epic-x"), "main")

    def test_base_branch_dependent_phase_stacks_on_latest_dep(self):
        self.assertEqual(base_branch_for(MANIFEST, 3, "epic-x"), "css/epic-x/p2")

    def test_base_branch_custom_epic_base(self):
        self.assertEqual(base_branch_for(MANIFEST, 1, "epic-x", epic_base="develop"), "develop")

if __name__ == "__main__":
    unittest.main()
