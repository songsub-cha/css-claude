from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class PipelineCommandContractTests(unittest.TestCase):
    def test_ship_to_phase_uses_session_argument(self):
        self.assertIn("/css:phase --session", read("commands/ship.md"))

    def test_phase_is_runtime_self_contained(self):
        text = read("commands/phase.md")
        self.assertNotIn("tools/css_schema", text)
        self.assertIn("strictly increasing", text)
        self.assertIn("single_phase:true", text)

    def test_execute_has_self_contained_language_detection(self):
        text = read("commands/execute.md")
        self.assertNotIn("Language Detection Logic", text)
        for marker in ("pyproject.toml", "package.json", "build.gradle", "go.mod"):
            self.assertIn(marker, text)

    def test_single_phase_path_is_detailed_and_rich(self):
        self.assertIn("single_phase == true", read("commands/plan.md"))
        self.assertIn("single-Phase Epic", read("commands/review.md"))
        self.assertIn("detailed plan", read("commands/ship.md"))

    def test_new_sessions_start_as_phase_candidates_but_legacy_stays_legacy(self):
        text = read("commands/interview.md") + read("commands/ship.md")
        self.assertIn('kind:"epic"', text)
        self.assertIn("single_phase:false", text)
        self.assertIn("kind-less", text)

    def test_review_requires_phasing_for_candidate_epic(self):
        self.assertIn("phases.phasing.status == completed", read("commands/review.md"))

    def test_child_commands_resolve_parent_spec(self):
        for rel in (
            "commands/plan.md",
            "commands/review.md",
            "commands/verify.md",
            "commands/document.md",
            "commands/pr.md",
        ):
            self.assertIn("parent_session", read(rel), rel)

    def test_child_pr_defaults_to_phase_base_branch(self):
        self.assertIn("session.base_branch", read("commands/pr.md"))

    def test_master_flow_gate3_is_not_prompted_twice(self):
        text = read("commands/pr.md") + read("agents/pr-creator.md")
        self.assertIn("gate3_approved", text)
        self.assertIn("do not ask again", text)

    def test_stage_commands_keep_dashboard_active_tracking(self):
        for rel in (
            "commands/plan.md",
            "commands/review.md",
            "commands/execute.md",
            "commands/verify.md",
            "commands/document.md",
            "commands/pr.md",
        ):
            self.assertIn("active_epic", read(rel), rel)

    def test_documenter_honors_phase_docs_path(self):
        text = read("commands/document.md") + read("agents/documenter.md")
        self.assertIn("docs/{parent_slug}/p{phase_index}/README.md", text)
        self.assertIn("supplied `docs_path`", text)

    def test_execute_and_verify_use_recorded_rich_specs(self):
        for rel in ("commands/execute.md", "commands/verify.md"):
            text = read(rel)
            self.assertIn("session.phases.review.rich_specs", text)
            self.assertIn("legacy", text)

    def test_advisories_are_separate_from_executable_specs(self):
        text = read("commands/review.md") + read("agents/reviewer.md")
        self.assertIn("advisories", text)
        self.assertIn("non-executable", text)


class SpecialistContractTests(unittest.TestCase):
    def test_db_profiles_are_polyglot(self):
        text = read("agents/db-specialist.md")
        for marker in ("Python SQLAlchemy", "Java/Kotlin JPA", "Node/TypeScript TypeORM"):
            self.assertIn(marker, text)

    def test_infra_commands_are_non_mutating(self):
        text = read("agents/infra-engineer.md")
        self.assertIn("must be non-mutating", text)
        self.assertIn("Never use apply", text)

    def test_prompt_requires_deterministic_harness(self):
        text = read("agents/prompt-engineer.md")
        self.assertIn("deterministic local acceptance harness", text)
        self.assertIn("VERDICT=LOOPBACK_TO_PLAN", text)

    def test_leaf_reviewers_are_write_blocked_and_orchestrator_persists(self):
        # Pure advisory leaves cannot touch the filesystem at all; they return
        # their report and the dispatching agent persists it.
        for rel in (
            "agents/architect.md",
            "agents/security-reviewer.md",
            "agents/code-reviewer.md",
        ):
            text = read(rel)
            self.assertIn("disallowedTools: [Write, Edit]", text, rel)
            self.assertIn("Return your", text, rel)
            self.assertNotIn("Write only", text, rel)
        # The dispatchers persist the returned reports, so they retain Write.
        reviewer = read("agents/reviewer.md")
        self.assertIn("disallowedTools: [Edit]", reviewer)
        self.assertNotIn("disallowedTools: [Write, Edit]", reviewer)
        for rel in ("agents/reviewer.md", "agents/verifier.md"):
            self.assertIn("persist", read(rel).lower(), rel)


if __name__ == "__main__":
    unittest.main()
