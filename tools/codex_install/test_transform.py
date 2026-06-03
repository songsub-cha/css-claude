"""Unit tests for the Codex install transforms (no filesystem side effects)."""
from __future__ import annotations

import unittest

from codex_install.transform import (
    RUNTIME_POINTER,
    build_index,
    split_frontmatter,
    transform_agent,
    transform_command,
)

_COMMAND = """---
description: Master pipeline — runs interview -> pr
argument-hint: "[--session <name>] <idea>"
---

# /css:ship

Do the thing with $ARGUMENTS.
"""

_AGENT = """---
name: css-reviewer
description: Plan reviewer (CSS pipeline, opus)
model: opus
disallowedTools: [Write, Edit]
css_stages: [review]
adapted_from: oh-my-claudecode/agents/code-reviewer.md
---

<Agent_Prompt>
  <Role>You are CSS-Reviewer.</Role>
</Agent_Prompt>
"""


class CommandTransformTests(unittest.TestCase):
    def test_split_frontmatter_returns_fields_and_body(self):
        fields, body = split_frontmatter(_COMMAND)
        self.assertEqual(fields["description"], "Master pipeline — runs interview -> pr")
        self.assertTrue(body.startswith("\n# /css:ship"))

    def test_split_frontmatter_none_when_absent(self):
        fields, body = split_frontmatter("# no frontmatter\n")
        self.assertIsNone(fields)
        self.assertEqual(body, "# no frontmatter\n")

    def test_command_drops_argument_hint_keeps_description(self):
        out = transform_command(_COMMAND)
        self.assertIn("description: Master pipeline", out)
        self.assertNotIn("argument-hint", out)

    def test_command_prepends_pointer_and_preserves_body(self):
        out = transform_command(_COMMAND)
        self.assertIn(RUNTIME_POINTER.strip(), out)
        self.assertIn("# /css:ship", out)
        self.assertIn("$ARGUMENTS", out)


class AgentTransformTests(unittest.TestCase):
    def test_agent_extracts_name(self):
        name, _ = transform_agent(_AGENT)
        self.assertEqual(name, "css-reviewer")

    def test_agent_strips_entire_frontmatter(self):
        _, body = transform_agent(_AGENT)
        self.assertFalse(body.lstrip().startswith("---"))
        for key in ("model:", "disallowedTools:", "css_stages:", "adapted_from:"):
            self.assertNotIn(key, body)
        self.assertIn("<Agent_Prompt>", body)

    def test_agent_without_name_raises(self):
        with self.assertRaises(ValueError):
            transform_agent("---\ndescription: x\n---\nbody\n")

    def test_build_index_is_sorted(self):
        idx = build_index({"css-z": "agents/z.md", "css-a": "agents/a.md"})
        self.assertEqual(list(idx), ["css-a", "css-z"])
        self.assertEqual(idx["css-a"], "agents/a.md")
