# CSS Codex CLI Compatibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the CSS pipeline runnable from OpenAI Codex CLI by installing transformed prompts + agent data files + a runtime mapping doc into `~/.codex`, without modifying any Claude Code source.

**Architecture:** A new tested Python package `tools/codex_install/` holds pure transform functions and an idempotent installer. Thin `scripts/install-codex.{sh,ps1}` wrappers invoke it. A new static `codex/RUNTIME.md` is the "execution brain" that tells the Codex agent how to map Claude tool names (`Task`, `AskUserQuestion`, `TodoWrite`) to Codex behavior, with a hybrid `spawn_agent`↔sequential fallback. Claude's `commands/`, `agents/`, and existing installers are never touched; session state stays at `<project>/.claude/css/` so sessions resume across both tools.

**Tech Stack:** Python 3.12 stdlib (`unittest`, `pathlib`, `re`, `json`, `argparse`, `shutil`), Bash, PowerShell. No third-party deps.

**Spec:** `docs/superpowers/specs/2026-06-03-css-codex-compat-design.md` (commit `29a7c36`). Decisions D1–D6.

---

## File Structure

**New files:**
- `codex/RUNTIME.md` — static execution brain (tool mapping, hybrid dispatch, env detection, handoff). Source of the file copied to `~/.codex/css/RUNTIME.md`.
- `tools/codex_install/__init__.py` — package marker.
- `tools/codex_install/transform.py` — pure functions: `split_frontmatter`, `transform_command`, `transform_agent`, `build_index`, and the `RUNTIME_POINTER` constant. No filesystem access.
- `tools/codex_install/installer.py` — `install(source_root, codex_home, force)`: transform + copy into `~/.codex`. Writes only under `codex_home`.
- `tools/codex_install/__main__.py` — argparse CLI: `python -m codex_install --source --dest [--force]`.
- `tools/codex_install/test_transform.py` — unit tests for transforms.
- `tools/codex_install/test_installer.py` — install layout / idempotency / config-guard / source-untouched tests (tempdir).
- `tools/codex_install/test_live_repo.py` — runs against the real repo: counts, index coverage, state-path preservation, RUNTIME.md lint.
- `scripts/install-codex.sh` — Ubuntu/Git-Bash installer wrapper.
- `scripts/install-codex.ps1` — Windows installer wrapper.

**Modified files:**
- `docs/installation.md` + `docs/installation.ko.md` — add a Codex CLI section.
- `README.md` + `README.en.md` — one line pointing to Codex install.

**Untouched (regression-guarded):** `commands/*.md`, `agents/*.md`, `scripts/install.sh`, `scripts/install.ps1`, `config/`.

---

## Task 1: `transform.py` — frontmatter split + command transform

**Files:**
- Create: `tools/codex_install/__init__.py`
- Create: `tools/codex_install/transform.py`
- Test: `tools/codex_install/test_transform.py`

- [ ] **Step 1: Create the package marker**

Create `tools/codex_install/__init__.py`:

```python
"""Transform Claude Code CSS sources into Codex CLI artifacts (install-time)."""
```

- [ ] **Step 2: Write the failing test for `transform_command`**

Create `tools/codex_install/test_transform.py`:

```python
"""Unit tests for the Codex install transforms (no filesystem side effects)."""
from __future__ import annotations

import unittest

from codex_install.transform import (
    RUNTIME_POINTER,
    split_frontmatter,
    transform_command,
)

_COMMAND = """---
description: Master pipeline — runs interview -> pr
argument-hint: "[--session <name>] <idea>"
---

# /css:ship

Do the thing with $ARGUMENTS.
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
        # Body (heading + the $ARGUMENTS line) preserved verbatim.
        self.assertIn("# /css:ship", out)
        self.assertIn("$ARGUMENTS", out)
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `cd tools && python -m unittest codex_install.test_transform -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'codex_install.transform'` (or ImportError).

- [ ] **Step 4: Implement `split_frontmatter` + `transform_command`**

Create `tools/codex_install/transform.py`:

```python
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

_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


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
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `cd tools && python -m unittest codex_install.test_transform -v`
Expected: PASS (4 tests).

- [ ] **Step 6: Commit**

```bash
git add tools/codex_install/__init__.py tools/codex_install/transform.py tools/codex_install/test_transform.py
git commit -m "feat(codex): command transform + frontmatter split"
```

---

## Task 2: `transform.py` — agent transform + index builder

**Files:**
- Modify: `tools/codex_install/transform.py`
- Test: `tools/codex_install/test_transform.py`

- [ ] **Step 1: Write the failing tests for `transform_agent` + `build_index`**

Append to `tools/codex_install/test_transform.py`:

```python
from codex_install.transform import build_index, transform_agent

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


class AgentTransformTests(unittest.TestCase):
    def test_agent_extracts_name(self):
        name, _ = transform_agent(_AGENT)
        self.assertEqual(name, "css-reviewer")

    def test_agent_strips_entire_frontmatter(self):
        _, body = transform_agent(_AGENT)
        self.assertFalse(body.lstrip().startswith("---"))
        for key in ("model:", "disallowedTools:", "css_stages:", "adapted_from:"):
            self.assertNotIn(key, body)
        self.assertIn("<Agent_Prompt>", body)  # body preserved

    def test_agent_without_name_raises(self):
        with self.assertRaises(ValueError):
            transform_agent("---\ndescription: x\n---\nbody\n")

    def test_build_index_is_sorted(self):
        idx = build_index({"css-z": "agents/z.md", "css-a": "agents/a.md"})
        self.assertEqual(list(idx), ["css-a", "css-z"])
        self.assertEqual(idx["css-a"], "agents/a.md")
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd tools && python -m unittest codex_install.test_transform -v`
Expected: FAIL — `ImportError: cannot import name 'transform_agent'`.

- [ ] **Step 3: Implement `transform_agent` + `build_index`**

Append to `tools/codex_install/transform.py`:

```python
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
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd tools && python -m unittest codex_install.test_transform -v`
Expected: PASS (8 tests total).

- [ ] **Step 5: Commit**

```bash
git add tools/codex_install/transform.py tools/codex_install/test_transform.py
git commit -m "feat(codex): agent transform (strip frontmatter) + index builder"
```

---

## Task 3: `installer.py` — orchestration (transform + copy)

**Files:**
- Create: `tools/codex_install/installer.py`
- Test: `tools/codex_install/test_installer.py`

- [ ] **Step 1: Write the failing test**

Create `tools/codex_install/test_installer.py`:

```python
"""Installer tests: layout, idempotency, config guard, source untouched."""
from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from codex_install.installer import install

_CMD = "---\ndescription: stage\nargument-hint: x\n---\n\n# /css:demo\nuse .claude/css/ and $ARGUMENTS\n"
_AGENT = "---\nname: css-demo\nmodel: opus\ncss_stages: [review]\n---\n\n<Agent_Prompt>body</Agent_Prompt>\n"
_CONFIG = '{"k": 1}\n'
_RUNTIME = "# RUNTIME\nspawn_agent / wait_agent / update_plan / AskUserQuestion / git-common-dir / index.json\n"


def _make_source(root: Path) -> None:
    (root / "commands").mkdir(parents=True)
    (root / "agents").mkdir(parents=True)
    (root / "config").mkdir(parents=True)
    (root / "codex").mkdir(parents=True)
    (root / "commands" / "demo.md").write_text(_CMD, encoding="utf-8")
    (root / "agents" / "demo.md").write_text(_AGENT, encoding="utf-8")
    (root / "config" / "default-config.json").write_text(_CONFIG, encoding="utf-8")
    (root / "codex" / "RUNTIME.md").write_text(_RUNTIME, encoding="utf-8")


def _tree_hashes(root: Path) -> dict:
    return {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*")) if p.is_file()
    }


class InstallerTests(unittest.TestCase):
    def test_install_creates_expected_layout(self):
        with tempfile.TemporaryDirectory() as s, tempfile.TemporaryDirectory() as d:
            src, dest = Path(s), Path(d)
            _make_source(src)
            summary = install(src, dest)
            self.assertEqual(summary, {"commands": 1, "agents": 1, "config_written": True})
            self.assertTrue((dest / "prompts" / "css-demo.md").exists())
            self.assertTrue((dest / "css" / "agents" / "demo.md").exists())
            self.assertTrue((dest / "css" / "agents" / "index.json").exists())
            self.assertTrue((dest / "css" / "RUNTIME.md").exists())
            self.assertTrue((dest / "css" / "config.json").exists())

    def test_idempotent(self):
        with tempfile.TemporaryDirectory() as s, tempfile.TemporaryDirectory() as d:
            src, dest = Path(s), Path(d)
            _make_source(src)
            install(src, dest)
            first = _tree_hashes(dest)
            install(src, dest)
            self.assertEqual(_tree_hashes(dest), first)

    def test_config_not_overwritten_without_force(self):
        with tempfile.TemporaryDirectory() as s, tempfile.TemporaryDirectory() as d:
            src, dest = Path(s), Path(d)
            _make_source(src)
            install(src, dest)
            cfg = dest / "css" / "config.json"
            cfg.write_text('{"local": true}\n', encoding="utf-8")
            install(src, dest)  # no force
            self.assertIn("local", cfg.read_text(encoding="utf-8"))
            install(src, dest, force=True)
            self.assertNotIn("local", cfg.read_text(encoding="utf-8"))

    def test_source_files_untouched(self):
        with tempfile.TemporaryDirectory() as s, tempfile.TemporaryDirectory() as d:
            src, dest = Path(s), Path(d)
            _make_source(src)
            before = _tree_hashes(src)
            install(src, dest)
            self.assertEqual(_tree_hashes(src), before)
            # The source agent still carries the Claude-only model: key.
            self.assertIn("model: opus", (src / "agents" / "demo.md").read_text(encoding="utf-8"))

    def test_transformed_prompt_preserves_state_path_and_args(self):
        with tempfile.TemporaryDirectory() as s, tempfile.TemporaryDirectory() as d:
            src, dest = Path(s), Path(d)
            _make_source(src)
            install(src, dest)
            prompt = (dest / "prompts" / "css-demo.md").read_text(encoding="utf-8")
            self.assertIn(".claude/css/", prompt)   # shared state path preserved
            self.assertIn("$ARGUMENTS", prompt)
            self.assertNotIn("argument-hint", prompt)
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd tools && python -m unittest codex_install.test_installer -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'codex_install.installer'`.

- [ ] **Step 3: Implement the installer**

Create `tools/codex_install/installer.py`:

```python
"""Install CSS Codex artifacts into ~/.codex (transform + copy).

Single source of truth = the repo's commands/ and agents/. This module writes
only under `codex_home`, so the Claude Code install is never affected.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from codex_install.transform import build_index, transform_agent, transform_command


def install(source_root, codex_home, force=False):
    """Transform repo CSS sources into Codex artifacts under `codex_home`.

    Returns {"commands": int, "agents": int, "config_written": bool}.
    Idempotent: re-running regenerates identical files; config.json is only
    written when missing or force=True (matching the Claude installer).
    """
    source_root = Path(source_root)
    codex_home = Path(codex_home)
    prompts_dir = codex_home / "prompts"
    css_dir = codex_home / "css"
    agents_dir = css_dir / "agents"
    for d in (prompts_dir, agents_dir):
        d.mkdir(parents=True, exist_ok=True)

    cmd_count = 0
    for md in sorted((source_root / "commands").glob("*.md")):
        out = transform_command(md.read_text(encoding="utf-8"))
        (prompts_dir / f"css-{md.stem}.md").write_text(out, encoding="utf-8")
        cmd_count += 1

    index = {}
    for md in sorted((source_root / "agents").glob("*.md")):
        name, body = transform_agent(md.read_text(encoding="utf-8"))
        (agents_dir / md.name).write_text(body, encoding="utf-8")
        index[name] = f"agents/{md.name}"
    (agents_dir / "index.json").write_text(
        json.dumps(build_index(index), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    shutil.copyfile(source_root / "codex" / "RUNTIME.md", css_dir / "RUNTIME.md")

    dst_config = css_dir / "config.json"
    config_written = False
    if force or not dst_config.exists():
        shutil.copyfile(source_root / "config" / "default-config.json", dst_config)
        config_written = True

    return {"commands": cmd_count, "agents": len(index), "config_written": config_written}
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd tools && python -m unittest codex_install.test_installer -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add tools/codex_install/installer.py tools/codex_install/test_installer.py
git commit -m "feat(codex): idempotent installer (transform + copy into ~/.codex)"
```

---

## Task 4: `__main__.py` — CLI entry point

**Files:**
- Create: `tools/codex_install/__main__.py`
- Test: `tools/codex_install/test_installer.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tools/codex_install/test_installer.py`:

```python
from codex_install.__main__ import main as cli_main


class CliTests(unittest.TestCase):
    def test_cli_main_installs(self):
        with tempfile.TemporaryDirectory() as s, tempfile.TemporaryDirectory() as d:
            src, dest = Path(s), Path(d)
            _make_source(src)
            rc = cli_main(["--source", str(src), "--dest", str(dest)])
            self.assertEqual(rc, 0)
            self.assertTrue((dest / "prompts" / "css-demo.md").exists())
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd tools && python -m unittest codex_install.test_installer.CliTests -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'codex_install.__main__'`.

- [ ] **Step 3: Implement the CLI**

Create `tools/codex_install/__main__.py`:

```python
"""CLI: python -m codex_install --source <repo> --dest <~/.codex> [--force]."""
from __future__ import annotations

import argparse
from pathlib import Path

from codex_install.installer import install


def main(argv=None):
    repo_default = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(prog="codex_install")
    parser.add_argument("--source", default=str(repo_default),
                        help="css-claude repo root (default: inferred)")
    parser.add_argument("--dest", default=str(Path.home() / ".codex"),
                        help="Codex home (default: ~/.codex)")
    parser.add_argument("--force", action="store_true",
                        help="overwrite existing config.json")
    args = parser.parse_args(argv)
    summary = install(args.source, args.dest, force=args.force)
    print(f"Installed {summary['commands']} prompts, {summary['agents']} agents "
          f"into {args.dest}")
    print(f"  config.json {'written' if summary['config_written'] else 'kept (exists)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd tools && python -m unittest codex_install.test_installer -v`
Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add tools/codex_install/__main__.py tools/codex_install/test_installer.py
git commit -m "feat(codex): CLI entry point for the installer"
```

---

## Task 5: `codex/RUNTIME.md` — execution brain + lint test

**Files:**
- Create: `codex/RUNTIME.md`
- Create: `tools/codex_install/test_live_repo.py`

- [ ] **Step 1: Write the failing lint test**

Create `tools/codex_install/test_live_repo.py`:

```python
"""Tests against the real repo: RUNTIME.md lint + transform of live sources."""
from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


class RuntimeDocTests(unittest.TestCase):
    def test_runtime_doc_has_required_mappings(self):
        text = (REPO_ROOT / "codex" / "RUNTIME.md").read_text(encoding="utf-8")
        for anchor in (
            "spawn_agent", "wait_agent", "close_agent", "update_plan",
            "AskUserQuestion", "git-common-dir", "index.json",
            ".claude/css/", "단일 모델",
        ):
            self.assertIn(anchor, text, f"RUNTIME.md missing anchor: {anchor}")
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd tools && python -m unittest codex_install.test_live_repo -v`
Expected: FAIL — `FileNotFoundError` (no `codex/RUNTIME.md`).

- [ ] **Step 3: Create `codex/RUNTIME.md`**

Create `codex/RUNTIME.md` with this exact content:

````markdown
# CSS Codex Runtime — Execution Model & Tool Mapping

Every installed CSS prompt (`~/.codex/prompts/css-*.md`) begins with a pointer
to this file. Read it before acting. CSS command/agent bodies are copied
verbatim from Claude Code and reference Claude tool names; this file maps each
to its Codex behavior. **User instructions and the prompt body always take
precedence over the examples here.**

## Tool mapping

| The body calls | Do this on Codex |
|---|---|
| `Task(subagent_type=X, prompt=P)` | Resolve `X` via `~/.codex/css/agents/index.json` to an agent file. **If `spawn_agent` is available:** `spawn_agent` with that file's contents + `P` as the prompt. **Otherwise:** perform that file's instructions inline, in the current thread, in order. |
| Several `Task(...)` meant to run in parallel | One `spawn_agent` per task, then `wait_agent` for each, then `close_agent` to free slots. Without `spawn_agent`, run them sequentially. |
| `TodoWrite` | `update_plan` |
| `AskUserQuestion(question, options=[...])` | Print the question and the options as a numbered plain-text list, then **stop and wait** for the user's typed reply. Map the reply back to an option. |
| `Read` / `Write` / `Edit` / `Bash` | Your native file and shell tools |

## Capability detection (hybrid)

If `spawn_agent` is in your toolset, use the **parallel** path (isolated
subagents). If not, use the **sequential** path (inline, single thread). Both
produce the same artifacts in the same locations. To enable the parallel path,
add to `~/.codex/config.toml`:

```toml
[features]
multi_agent = true
```

## Agent resolution

`subagent_type` values (e.g. `css-reviewer`) map to files via
`~/.codex/css/agents/index.json` (`{ "css-reviewer": "agents/reviewer.md", ... }`).
Load the file's text and use it as the specialist's prompt/instructions. The
agent files contain no frontmatter — body only.

## Model

Codex runs a **단일 모델** (single session model). The Claude per-agent
`model:` tiering (opus/sonnet/haiku) does not exist here and is not replicated;
those frontmatter keys were stripped at install time. There is no per-task
model switching and therefore no model-based cost tiering.

## Worktree / finish environment detection

Before creating a worktree (`/css-execute`) or pushing/PR (`/css-pr`), detect
the environment with read-only git:

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
BRANCH=$(git branch --show-current)
```

- `GIT_DIR != GIT_COMMON` → already in a linked worktree → **skip** worktree creation.
- `BRANCH` empty → detached HEAD (sandbox) → cannot branch/push/PR → use handoff.

## PR / finish

If `gh` is present, authenticated, and network is available, create the PR as
the body instructs. Otherwise emit a **handoff payload** — suggested branch
name, commit message, and PR body — for the user to apply via their host UI or
local checkout.

## State

CSS session state lives at `<project>/.claude/css/` and is **shared with Claude
Code** — read and write there so a session started in either tool resumes in
the other. Do not relocate it.
````

- [ ] **Step 4: Run to verify it passes**

Run: `cd tools && python -m unittest codex_install.test_live_repo -v`
Expected: PASS (1 test).

- [ ] **Step 5: Commit**

```bash
git add codex/RUNTIME.md tools/codex_install/test_live_repo.py
git commit -m "feat(codex): RUNTIME.md execution brain + lint test"
```

---

## Task 6: Live-repo transform/install test (real 9 commands + 21 agents)

**Files:**
- Modify: `tools/codex_install/test_live_repo.py`

- [ ] **Step 1: Write the failing test**

Append to `tools/codex_install/test_live_repo.py`:

```python
import tempfile
from codex_install.installer import install


class LiveInstallTests(unittest.TestCase):
    def test_install_real_repo(self):
        with tempfile.TemporaryDirectory() as d:
            dest = Path(d)
            summary = install(REPO_ROOT, dest)
            # Counts match the live source tree.
            n_cmds = len(list((REPO_ROOT / "commands").glob("*.md")))
            n_agents = len(list((REPO_ROOT / "agents").glob("*.md")))
            self.assertEqual(summary["commands"], n_cmds)
            self.assertEqual(summary["agents"], n_agents)
            # ship prompt exists and preserves the shared state path.
            ship = (dest / "prompts" / "css-ship.md").read_text(encoding="utf-8")
            self.assertIn(".claude/css/", ship)
            self.assertIn("$ARGUMENTS", ship)
            # index.json covers exactly the agent set, and every agent body
            # has no leftover frontmatter.
            import json
            index = json.loads((dest / "css" / "agents" / "index.json").read_text(encoding="utf-8"))
            self.assertEqual(len(index), n_agents)
            for rel in index.values():
                body = (dest / "css" / rel).read_text(encoding="utf-8")
                self.assertFalse(body.lstrip().startswith("---"))
                self.assertNotIn("\nmodel:", "\n" + body[:200])

    def test_real_sources_unchanged_after_install(self):
        import hashlib
        def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
        before = {p: h(p) for p in (REPO_ROOT / "commands").glob("*.md")}
        before.update({p: h(p) for p in (REPO_ROOT / "agents").glob("*.md")})
        with tempfile.TemporaryDirectory() as d:
            install(REPO_ROOT, Path(d))
        after = {p: h(p) for p in before}
        self.assertEqual(after, before)
```

- [ ] **Step 2: Run to verify it fails (or passes if code already correct)**

Run: `cd tools && python -m unittest codex_install.test_live_repo -v`
Expected: PASS — the implementation from Tasks 1–5 already supports this; this test locks in live-repo behavior. If it FAILS, the failure message identifies which invariant broke (count, state path, frontmatter leak, or source mutation). Fix the implicated function before continuing.

- [ ] **Step 3: Commit**

```bash
git add tools/codex_install/test_live_repo.py
git commit -m "test(codex): live-repo install coverage (counts, state path, source untouched)"
```

---

## Task 7: `scripts/install-codex.sh`

**Files:**
- Create: `scripts/install-codex.sh`

- [ ] **Step 1: Create the script**

Create `scripts/install-codex.sh`:

```bash
#!/usr/bin/env bash
# install-codex.sh — install CSS into OpenAI Codex CLI (~/.codex).
# Single source = this repo's commands/ + agents/. The Claude Code install is
# untouched (use scripts/install.sh for that).
#
# Usage:
#   bash scripts/install-codex.sh                 # install
#   FORCE=1 bash scripts/install-codex.sh         # overwrite existing config.json
set -euo pipefail

SOURCE_PATH="${SOURCE_PATH:-$(cd "$(dirname "$0")/.." && pwd)}"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
FORCE="${FORCE:-0}"

section() { echo; echo "=== $1 ==="; }

section "Verifying prerequisites"
if ! command -v python3 >/dev/null 2>&1; then
  echo "  [MISSING] python3 (required to transform sources)" >&2
  exit 1
fi
echo "  [OK] python3"
command -v codex >/dev/null 2>&1 && echo "  [OK] codex CLI" || echo "  [WARN] codex CLI not found (runtime dependency)"
command -v git   >/dev/null 2>&1 && echo "  [OK] git"        || echo "  [WARN] git not found (runtime dependency)"
command -v gh    >/dev/null 2>&1 && echo "  [OK] gh"          || echo "  [WARN] gh not found (PR step falls back to handoff)"

section "Installing CSS Codex artifacts"
force_flag=""
[ "$FORCE" = "1" ] && force_flag="--force"
( cd "$SOURCE_PATH/tools" && python3 -m codex_install --source "$SOURCE_PATH" --dest "$CODEX_HOME" $force_flag )

section "Done"
echo "Optional — enable parallel specialists in $CODEX_HOME/config.toml:"
echo "  [features]"
echo "  multi_agent = true"
echo
echo "Try: /css-ship \"<small idea>\" in a Codex CLI session."
```

- [ ] **Step 2: Verify it runs end-to-end into a throwaway CODEX_HOME**

Run: `CODEX_HOME="$(mktemp -d)/codex" bash scripts/install-codex.sh`
Expected: prints `[OK] python3`, an "Installing" section, then `Installed 9 prompts, 21 agents into <tmp>/codex` and the Done banner. Exit 0.

- [ ] **Step 3: Commit**

```bash
git add scripts/install-codex.sh
git commit -m "feat(codex): install-codex.sh (Ubuntu/Git-Bash wrapper)"
```

---

## Task 8: `scripts/install-codex.ps1`

**Files:**
- Create: `scripts/install-codex.ps1`

- [ ] **Step 1: Create the script**

Create `scripts/install-codex.ps1`:

```powershell
<#
.SYNOPSIS
  Install CSS into OpenAI Codex CLI (~/.codex). The Claude Code install is
  untouched (use scripts\install.ps1 for that).
.PARAMETER SourcePath
  Path to the css-claude repo. Defaults to the repo containing this script.
.PARAMETER Force
  Overwrite an existing config.json.
.EXAMPLE
  .\scripts\install-codex.ps1
  .\scripts\install-codex.ps1 -Force
#>
[CmdletBinding()]
param([string]$SourcePath = "", [switch]$Force)

if (-not $SourcePath) {
  $scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
  $SourcePath = Join-Path $scriptDir ".."
}
$ErrorActionPreference = "Stop"
function Write-Section($m) { Write-Host ""; Write-Host "=== $m ===" -ForegroundColor Cyan }

Write-Section "Verifying prerequisites"
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $python) { Write-Host "  [MISSING] python (required to transform sources)" -ForegroundColor Red; exit 1 }
Write-Host "  [OK] $($python.Source)" -ForegroundColor Green
if (Get-Command codex -ErrorAction SilentlyContinue) { Write-Host "  [OK] codex CLI" -ForegroundColor Green } else { Write-Host "  [WARN] codex CLI not found (runtime dependency)" -ForegroundColor Yellow }

$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE ".codex" }

Write-Section "Installing CSS Codex artifacts"
$toolsDir = Join-Path $SourcePath "tools"
$argsList = @("-m", "codex_install", "--source", $SourcePath, "--dest", $codexHome)
if ($Force) { $argsList += "--force" }
Push-Location $toolsDir
try { & $python.Source @argsList } finally { Pop-Location }

Write-Section "Done"
Write-Host "Optional — enable parallel specialists in $codexHome\config.toml:"
Write-Host "  [features]"
Write-Host "  multi_agent = true"
Write-Host ""
Write-Host "Try: /css-ship `"<small idea>`" in a Codex CLI session."
```

- [ ] **Step 2: Verify it runs end-to-end into a throwaway CODEX_HOME**

Run (PowerShell): `$env:CODEX_HOME = Join-Path $env:TEMP 'codex-test'; powershell -ExecutionPolicy Bypass -File scripts\install-codex.ps1`
Expected: `[OK]` python line, "Installing" section, `Installed 9 prompts, 21 agents into <temp>\codex-test`, Done banner. Then clean up: `Remove-Item -Recurse -Force $env:CODEX_HOME`.

- [ ] **Step 3: Commit**

```bash
git add scripts/install-codex.ps1
git commit -m "feat(codex): install-codex.ps1 (Windows wrapper)"
```

---

## Task 9: Documentation

**Files:**
- Modify: `docs/installation.md`
- Modify: `docs/installation.ko.md`
- Modify: `README.md`
- Modify: `README.en.md`

- [ ] **Step 1: Add a Codex CLI section to `docs/installation.md`**

Append this section to the end of `docs/installation.md`:

```markdown
## Codex CLI (experimental)

CSS also runs on OpenAI Codex CLI. The same `commands/` and `agents/` sources
are transformed into Codex prompts + agent data files under `~/.codex`; your
Claude Code install is untouched.

```bash
bash scripts/install-codex.sh
# Windows:
powershell -ExecutionPolicy Bypass -File scripts\install-codex.ps1
```

Then invoke stages as `/css-ship`, `/css-interview`, … (Codex uses a `css-`
prefix instead of the `css:` namespace).

Optional — enable parallel specialists by adding to `~/.codex/config.toml`:

```toml
[features]
multi_agent = true
```

Without it, specialists run sequentially in one agent (no parallelism, same
result). Session state is shared with Claude Code at `<project>/.claude/css/`,
so a session started in either tool resumes in the other. Execution behavior
is governed by `~/.codex/css/RUNTIME.md`. Prerequisites: `python3` (install),
plus `codex`, `git`, and optionally `gh` at runtime.
```

- [ ] **Step 2: Add the equivalent Korean section to `docs/installation.ko.md`**

Append to the end of `docs/installation.ko.md`:

```markdown
## Codex CLI (실험적)

CSS는 OpenAI Codex CLI에서도 동작합니다. 동일한 `commands/`·`agents/` 소스를
`~/.codex` 아래 Codex 프롬프트 + 에이전트 데이터 파일로 변환하며, Claude Code
설치는 건드리지 않습니다.

```bash
bash scripts/install-codex.sh
# Windows:
powershell -ExecutionPolicy Bypass -File scripts\install-codex.ps1
```

이후 `/css-ship`, `/css-interview` … 로 호출합니다 (Codex는 `css:` 네임스페이스
대신 `css-` 프리픽스 사용).

선택 — 병렬 전문가를 켜려면 `~/.codex/config.toml`에 추가:

```toml
[features]
multi_agent = true
```

없으면 전문가가 단일 에이전트에서 순차 실행됩니다(병렬성만 포기, 결과 동일).
세션 상태는 `<project>/.claude/css/`에서 Claude Code와 공유되어 어느 도구에서
시작하든 다른 도구에서 이어집니다. 실행 동작은 `~/.codex/css/RUNTIME.md`가
규정합니다. 사전 조건: `python3`(설치 시), 런타임에 `codex`·`git`·(선택) `gh`.
```

- [ ] **Step 3: Add a pointer line to both READMEs**

In `README.md`, under the "## 설치" section, after the platform-script bullets, add:

```markdown
- Codex CLI: `bash scripts/install-codex.sh` (자세한 내용은 [`docs/installation.ko.md`](docs/installation.ko.md)의 Codex CLI 섹션)
```

In `README.en.md`, under its install section, add the analogous line:

```markdown
- Codex CLI: `bash scripts/install-codex.sh` (see the Codex CLI section in [`docs/installation.md`](docs/installation.md))
```

- [ ] **Step 4: Sanity-check the docs render and links resolve**

Run: `cd tools && python -m unittest discover -v`
Expected: all `codex_install` tests still PASS (docs changes don't affect them; this is a final guard that the package is intact).

- [ ] **Step 5: Commit**

```bash
git add docs/installation.md docs/installation.ko.md README.md README.en.md
git commit -m "docs(codex): document Codex CLI install + usage"
```

---

## Final verification

- [ ] **Run the full Codex test suite**

Run: `cd tools && python -m unittest codex_install.test_transform codex_install.test_installer codex_install.test_live_repo -v`
Expected: all PASS.

- [ ] **Confirm the Claude tooling regression guard still passes**

Run: `cd tools && python -m unittest agent_registry.test_registry -v`
Expected: all PASS (we never modified `commands/`, `agents/`, or the READMEs' specialist tables; `test_live_repo_is_consistent` still holds).
