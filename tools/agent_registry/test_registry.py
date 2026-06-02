"""Tests for agent_registry: frontmatter/dispatch/README parsing + the live
consistency guard that keeps the Domain Dispatch routing in sync with the
agent files and the README specialist tables."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_registry.registry import (
    check_consistency,
    domain_specialists,
    parse_agent_files,
    parse_dispatch_specialists,
    parse_readme_specialists,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

_AGENT = """---
name: {name}
model: sonnet
css_stages: [{stages}]
---

<Agent_Prompt>body</Agent_Prompt>
"""

_EXECUTOR = """---
name: css-executor
---
<Domain_Dispatch_Table>
| Pattern | Specialist | Spec |
|---|---|---|
{rows}
If a task matches multiple rows, pick the dominant.
</Domain_Dispatch_Table>
"""

_README = "# Title\n\n| 에이전트 | 영역 | 모델 |\n|---|---|---|\n{rows}\n"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _make_repo(root: Path, agents, dispatch, readme_ko, readme_en) -> None:
    """agents: {name: stages_csv}; dispatch/readme_*: iterable of css-* names."""
    for name, stages in agents.items():
        _write(root / "agents" / f"{name}.md", _AGENT.format(name=name, stages=stages))
    rows = "\n".join(f"| HTTP {n} | `{n}` | `{n[4:]}-spec.md` |" for n in dispatch)
    _write(root / "agents" / "executor.md", _EXECUTOR.format(rows=rows))
    _write(root / "README.md",
           _README.format(rows="\n".join(f"| `{n}` | area | sonnet |" for n in readme_ko)))
    _write(root / "README.en.md",
           _README.format(rows="\n".join(f"| `{n}` | area | sonnet |" for n in readme_en)))


class ParseTests(unittest.TestCase):
    def test_parse_agent_files_extracts_frontmatter(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _write(root / "agents" / "a.md", _AGENT.format(name="css-a", stages="review, execute"))
            _write(root / "agents" / "b.md", _AGENT.format(name="css-b", stages="execute"))
            _write(root / "agents" / "no-fm.md", "no frontmatter here\n")
            agents = parse_agent_files(root / "agents")
        self.assertEqual(set(agents), {"css-a", "css-b"})  # no-fm skipped
        self.assertEqual(agents["css-a"]["css_stages"], ["review", "execute"])
        self.assertEqual(agents["css-a"]["model"], "sonnet")

    def test_domain_specialists_requires_review_and_execute(self):
        agents = {
            "css-a": {"css_stages": ["review", "execute"], "model": "sonnet", "path": ""},
            "css-b": {"css_stages": ["execute"], "model": "sonnet", "path": ""},
            "css-c": {"css_stages": ["review"], "model": "opus", "path": ""},
        }
        self.assertEqual(domain_specialists(agents), {"css-a"})

    def test_parse_dispatch_only_within_table(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "executor.md"
            _write(p, _EXECUTOR.format(rows="| x | `css-foo` | `foo-spec.md` |"))
            self.assertEqual(parse_dispatch_specialists(p), {"css-foo"})

    def test_parse_readme_only_first_cell_css_names(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "README.md"
            # First-cell css name counts; a css name in a later cell must not.
            _write(p, "| ① | `/css:x` | `css-executor` |\n| `css-foo` | area | sonnet |\n")
            self.assertEqual(parse_readme_specialists(p), {"css-foo"})


class ConsistencyTests(unittest.TestCase):
    def test_consistent_repo_with_advisory_extra(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _make_repo(
                root,
                agents={"css-spec1": "review, execute", "css-proc": "execute",
                        "css-arch": "review"},
                dispatch=["css-spec1"],
                readme_ko=["css-spec1", "css-arch"],  # advisory arch allowed
                readme_en=["css-spec1", "css-arch"],
            )
            self.assertEqual(check_consistency(root), [])

    def test_broken_repo_reports_each_gap(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _make_repo(
                root,
                agents={"css-spec1": "review, execute", "css-spec2": "review, execute"},
                dispatch=["css-spec1", "css-ghostdispatch"],
                readme_ko=["css-spec1", "css-ghostko"],
                readme_en=["css-spec1"],
            )
            errors = "\n".join(check_consistency(root))
        self.assertIn("css-spec2", errors)            # missing from dispatch + READMEs
        self.assertIn("css-ghostdispatch", errors)    # dispatch -> no domain agent
        self.assertIn("css-ghostko", errors)          # README -> no agent file
        self.assertIn("Domain_Dispatch_Table", errors)

    def test_live_repo_is_consistent(self):
        """The real repo must stay in sync (agents <-> dispatch <-> README)."""
        self.assertEqual(check_consistency(REPO_ROOT), [])


if __name__ == "__main__":
    unittest.main()
