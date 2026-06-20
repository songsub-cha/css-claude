from __future__ import annotations

import unittest
from pathlib import Path

from agent_registry.rich_spec import RichSpecError, validate_rich_spec

FX = Path(__file__).parent / "fixtures"


class RichSpecTests(unittest.TestCase):
    def test_valid_phase_artifact(self):
        result = validate_rich_spec(
            (FX / "valid_phase_rich_spec.md").read_text(encoding="utf-8"),
            expected_task_id="02",
            expected_phase=2,
        )
        self.assertEqual(result["specialist"], "css-api-specialist")

    def test_valid_single_session_artifact(self):
        result = validate_rich_spec(
            (FX / "valid_single_rich_spec.md").read_text(encoding="utf-8"),
            expected_task_id="01",
            expected_phase=1,
        )
        self.assertEqual(result["phase"], "1")

    def test_missing_required_fields_rejected(self):
        text = (FX / "valid_single_rich_spec.md").read_text(encoding="utf-8")
        for field in ("Phase: 1", "RED command:", "GREEN command:"):
            with self.subTest(field=field), self.assertRaises(RichSpecError):
                validate_rich_spec(
                    text.replace(field, "removed:", 1),
                    expected_task_id="01",
                    expected_phase=1,
                )

    def test_wrong_task_id_rejected(self):
        with self.assertRaises(RichSpecError):
            validate_rich_spec(
                (FX / "valid_phase_rich_spec.md").read_text(encoding="utf-8"),
                expected_task_id="99",
                expected_phase=2,
            )

    def test_duplicate_task_id_rejected(self):
        text = (FX / "valid_single_rich_spec.md").read_text(encoding="utf-8")
        with self.assertRaises(RichSpecError):
            validate_rich_spec(
                text.replace("## Task 01", "## Task 01\n## Task 01", 1),
                expected_task_id="01",
                expected_phase=1,
            )

    def test_advisory_rejected_as_executable(self):
        with self.assertRaises(RichSpecError):
            validate_rich_spec(
                (FX / "advisory_security.md").read_text(encoding="utf-8"),
                expected_task_id="01",
                expected_phase=1,
            )

    def test_executable_spec_with_advisory_in_slug_accepted(self):
        # Regression: a legitimate plans/ artifact whose slug contains "advisory"
        # (e.g. an "advisory-dashboard" feature) must NOT be misread as an
        # advisory report. Advisory detection keys off the reviews/ directory.
        text = (FX / "valid_single_rich_spec.md").read_text(encoding="utf-8").replace(
            "ARTIFACT=.claude/css/plans/small-idea-T01.md",
            "ARTIFACT=.claude/css/plans/advisory-dashboard-T01.md",
        )
        result = validate_rich_spec(text, expected_task_id="01", expected_phase=1)
        self.assertEqual(
            result["artifact"], ".claude/css/plans/advisory-dashboard-T01.md")

    def test_expected_artifact_match_accepted(self):
        validate_rich_spec(
            (FX / "valid_phase_rich_spec.md").read_text(encoding="utf-8"),
            expected_task_id="02",
            expected_phase=2,
            expected_artifact=".claude/css/plans/epic-p2-T02.md",
        )

    def test_expected_artifact_mismatch_rejected(self):
        with self.assertRaises(RichSpecError):
            validate_rich_spec(
                (FX / "valid_phase_rich_spec.md").read_text(encoding="utf-8"),
                expected_task_id="02",
                expected_phase=2,
                expected_artifact=".claude/css/plans/wrong-path.md",
            )

    def test_decoy_artifact_in_body_is_ignored(self):
        # A stray "ARTIFACT=" line inside a GREEN/RED block must NOT be mistaken
        # for the spec's artifact: only the final line is authoritative. Here the
        # decoy points at reviews/, which would wrongly trip advisory detection
        # if the parser keyed off the first match instead of the last line.
        text = (FX / "valid_single_rich_spec.md").read_text(encoding="utf-8").replace(
            "export function App() { return <main /> }",
            "export function App() { return <main /> }\n"
            "ARTIFACT=.claude/css/reviews/decoy.md",
        )
        result = validate_rich_spec(text, expected_task_id="01", expected_phase=1)
        self.assertEqual(result["artifact"], ".claude/css/plans/small-idea-T01.md")

    def test_empty_red_or_green_command_rejected(self):
        base = (FX / "valid_single_rich_spec.md").read_text(encoding="utf-8")
        for original in (
            "RED command: npm test -- App.test.tsx",
            "GREEN command: npm test -- App.test.tsx",
        ):
            label = original.split(":", 1)[0]
            with self.subTest(label=label), self.assertRaises(RichSpecError):
                validate_rich_spec(
                    base.replace(original, f"{label}:", 1),
                    expected_task_id="01",
                    expected_phase=1,
                )


if __name__ == "__main__":
    unittest.main()
