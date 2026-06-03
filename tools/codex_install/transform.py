"""Pure transforms: Claude CSS command/agent markdown -> Codex CLI text.

No filesystem side effects. Claude source files are never mutated — the
installer reads source text and writes transformed copies under ~/.codex.
"""
from __future__ import annotations

import re

# Prepended to every Codex command prompt. Points the agent at the runtime
# brain that maps Claude tool names (Task/AskUserQuestion/TodoWrite) to Codex.
RUNTIME_POINTER = (
    "> Execution model & tool mapping: read `~/.codex/css/RUNTIME.md` and "
    "follow it before proceeding.\n"
)

# Delimiter whitespace is horizontal-only ([ \t]*, not \s*): with re.DOTALL,
# \s* would swallow the blank line after the closing ---, truncating the body.
# [ \t]* keeps the body (incl. its leading newline) verbatim.
_FRONTMATTER_RE = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*\n", re.DOTALL)


def split_frontmatter(text):
    """Return ({key: value}, body) or (None, text) when there is no frontmatter."""
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return None, text
    fields = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    return fields, text[m.end():]


def transform_command(text):
    """Claude command .md -> Codex prompt text.

    Keeps only the `description` frontmatter key, prepends the RUNTIME pointer,
    preserves the body (including `$ARGUMENTS`) verbatim.
    """
    fields, body = split_frontmatter(text)
    out = ""
    if fields and fields.get("description"):
        out += f"---\ndescription: {fields['description']}\n---\n"
    out += RUNTIME_POINTER + "\n" + body
    return out


def transform_agent(text):
    """Claude agent .md -> (name, body). Strips the whole frontmatter block.

    Raises ValueError if there is no frontmatter `name:`.
    """
    fields, body = split_frontmatter(text)
    if not fields or "name" not in fields:
        raise ValueError("agent file missing frontmatter 'name'")
    return fields["name"], body


def build_index(name_to_path):
    """Return a name-sorted {name: relative_path} for deterministic index.json."""
    return {name: name_to_path[name] for name in sorted(name_to_path)}
