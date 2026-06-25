# CSS Plugin Packaging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `css-claude` installable as a Claude Code plugin via a self-hosted in-repo marketplace, coexisting with the existing install scripts.

**Architecture:** Add two manifests (`.claude-plugin/plugin.json` + `marketplace.json`) and rely on plugin auto-discovery of `commands/` and `agents/`. The same file tree works under both loaders: a dual-mode path resolver (`${CLAUDE_PLUGIN_ROOT}` → fallback `$HOME/.claude/css`) bridges plugin vs script installs. `.ko.md` reference translations move to `i18n/` so auto-discovery sees only canonical English files.

**Tech Stack:** Claude Code plugin manifests (JSON), bash (`lib/gh_sync.sh`, `commands/ship.md`), Python 3.11 `unittest` tests under `tools/`.

## Global Constraints

- Plugin name MUST be exactly `css` — preserves the `/css:*` command namespace and bare `css-*` agent dispatch (verified: plugin agents resolve by bare frontmatter name).
- Coexist with `scripts/install.sh|ps1` and the Codex path; **nothing deprecated**.
- License unchanged: `plugin.json` license = `"SEE LICENSE IN LICENSE"`. Codex files untouched.
- `plugin.json` MUST NOT set `commands`/`agents` fields — rely on auto-discovery of `commands/*.md` and `agents/*.md`.
- All plugin manifest paths are relative and start with `./`.
- Tests use the stdlib `unittest` runner (**pytest is not installed**). Full suite: `cd tools && python -m unittest discover -v` (currently 84 tests, green).
- Do NOT remove these anchors from `commands/ship.md`: the substrings `/css:phase --session` and `.claude/css/` (the `agent_registry` semantic guard asserts them).
- `.ko.md` reference copies live under `i18n/`, never under `commands/`/`agents/`.

---

### Task 1: Plugin manifest (`.claude-plugin/plugin.json`)

**Files:**
- Create: `tools/plugin_packaging/__init__.py`
- Create: `tools/plugin_packaging/test_manifests.py`
- Create: `.claude-plugin/plugin.json`

**Interfaces:**
- Produces: a valid plugin manifest at `.claude-plugin/plugin.json` with `name == "css"`, `version == "0.1.0"`, no `commands`/`agents` keys.

- [ ] **Step 1: Create the test package init**

Create `tools/plugin_packaging/__init__.py` (empty file):

```python
```

- [ ] **Step 2: Write the failing test**

Create `tools/plugin_packaging/test_manifests.py`:

```python
import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


class PluginManifestTests(unittest.TestCase):
    def _load(self):
        p = REPO / ".claude-plugin" / "plugin.json"
        self.assertTrue(p.exists(), "plugin.json missing")
        return json.loads(p.read_text(encoding="utf-8"))

    def test_name_is_css(self):
        self.assertEqual(self._load()["name"], "css")

    def test_has_version_and_description(self):
        m = self._load()
        self.assertEqual(m["version"], "0.1.0")
        self.assertTrue(m.get("description"))

    def test_omits_component_fields(self):
        # Auto-discovery must own commands/ and agents/.
        m = self._load()
        self.assertNotIn("commands", m)
        self.assertNotIn("agents", m)
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `cd tools && python -m unittest plugin_packaging.test_manifests -v`
Expected: FAIL — `AssertionError: plugin.json missing`.

- [ ] **Step 4: Create the manifest**

Create `.claude-plugin/plugin.json`:

```json
{
  "$schema": "https://json.schemastore.org/claude-code-plugin-manifest.json",
  "name": "css",
  "displayName": "CSS — Claude Super System",
  "version": "0.1.0",
  "description": "Idea to PR pipeline: spec, plan, review, TDD execute, verify, docs, PR — with domain-specialist agents and human approval gates.",
  "author": { "name": "songsub-cha", "email": "sub1904@gmail.com" },
  "homepage": "https://github.com/songsub-cha/css-claude",
  "repository": "https://github.com/songsub-cha/css-claude",
  "license": "SEE LICENSE IN LICENSE",
  "keywords": ["pipeline", "tdd", "automation", "agents", "workflow", "code-review"]
}
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `cd tools && python -m unittest plugin_packaging.test_manifests -v`
Expected: PASS (3 tests).

- [ ] **Step 6: Commit**

```bash
git add tools/plugin_packaging/__init__.py tools/plugin_packaging/test_manifests.py .claude-plugin/plugin.json
git commit -m "feat(plugin): add plugin.json manifest (name=css)"
```

---

### Task 2: Marketplace manifest (`.claude-plugin/marketplace.json`)

**Files:**
- Modify: `tools/plugin_packaging/test_manifests.py` (add a class)
- Create: `.claude-plugin/marketplace.json`

**Interfaces:**
- Consumes: `.claude-plugin/plugin.json` (Task 1).
- Produces: a marketplace catalog listing plugin `css` at `source: "./"`.

- [ ] **Step 1: Write the failing test**

Append to `tools/plugin_packaging/test_manifests.py`:

```python
class MarketplaceManifestTests(unittest.TestCase):
    def _load(self):
        p = REPO / ".claude-plugin" / "marketplace.json"
        self.assertTrue(p.exists(), "marketplace.json missing")
        return json.loads(p.read_text(encoding="utf-8"))

    def test_name_and_owner(self):
        m = self._load()
        self.assertEqual(m["name"], "css-claude")
        self.assertTrue(m["owner"]["name"])

    def test_lists_css_plugin_at_repo_root(self):
        plugins = self._load()["plugins"]
        entry = next(p for p in plugins if p["name"] == "css")
        self.assertEqual(entry["source"], "./")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd tools && python -m unittest plugin_packaging.test_manifests.MarketplaceManifestTests -v`
Expected: FAIL — `AssertionError: marketplace.json missing`.

- [ ] **Step 3: Create the marketplace catalog**

Create `.claude-plugin/marketplace.json`:

```json
{
  "name": "css-claude",
  "owner": { "name": "songsub-cha", "email": "sub1904@gmail.com" },
  "plugins": [
    {
      "name": "css",
      "source": "./",
      "description": "Idea to PR software-development pipeline for Claude Code."
    }
  ]
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd tools && python -m unittest plugin_packaging.test_manifests.MarketplaceManifestTests -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add tools/plugin_packaging/test_manifests.py .claude-plugin/marketplace.json
git commit -m "feat(plugin): add in-repo marketplace.json (source=./)"
```

---

### Task 3: Relocate `.ko.md` to `i18n/` and simplify installers

**Files:**
- Create: `tools/plugin_packaging/test_structure.py`
- Move: `commands/*.ko.md` → `i18n/commands/` (9 files)
- Move: `agents/*.ko.md` → `i18n/agents/` (21 files)
- Modify: `scripts/install.sh` (lines 83-90, 95-102 — drop dead `.ko.md` skip)
- Modify: `scripts/install.ps1` (lines 84, 93 — drop dead `.ko.md` filter)

**Interfaces:**
- Produces: `commands/` and `agents/` contain only canonical `*.md` (plain stems); translations live under `i18n/`.

- [ ] **Step 1: Write the failing test**

Create `tools/plugin_packaging/test_structure.py`:

```python
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd tools && python -m unittest plugin_packaging.test_structure -v`
Expected: FAIL — `commands/ still has locale files: [...]`.

- [ ] **Step 3: Move the translation files with git**

Run from the repo root:

```bash
mkdir -p i18n/commands i18n/agents
git mv commands/*.ko.md i18n/commands/
git mv agents/*.ko.md i18n/agents/
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd tools && python -m unittest plugin_packaging.test_structure -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Simplify the bash installer**

In `scripts/install.sh`, the commands loop (lines ~83-90) currently is:

```bash
if compgen -G "$SOURCE_PATH/commands/*.md" >/dev/null; then
  for f in "$SOURCE_PATH"/commands/*.md; do
    case "$f" in *.ko.md) continue ;; esac
    cp "$f" "$cmd_dir/"
    echo "  $(basename "$f")"
    cmd_count=$((cmd_count + 1))
  done
fi
```

Remove the now-dead skip line so it reads:

```bash
if compgen -G "$SOURCE_PATH/commands/*.md" >/dev/null; then
  for f in "$SOURCE_PATH"/commands/*.md; do
    cp "$f" "$cmd_dir/"
    echo "  $(basename "$f")"
    cmd_count=$((cmd_count + 1))
  done
fi
```

Apply the identical change to the agents loop (lines ~95-102): delete its `case "$f" in *.ko.md) continue ;;` line.

- [ ] **Step 6: Simplify the PowerShell installer**

In `scripts/install.ps1`, change line 84 from:

```powershell
$cmdFiles = Get-ChildItem $srcCmd -Filter "*.md" -ErrorAction SilentlyContinue | Where-Object { $_.Name -notlike "*.ko.md" }
```

to:

```powershell
$cmdFiles = Get-ChildItem $srcCmd -Filter "*.md" -ErrorAction SilentlyContinue
```

Apply the identical change to line 93 (the `$agentFiles` line): drop the `| Where-Object { $_.Name -notlike "*.ko.md" }`.

- [ ] **Step 7: Confirm the full Python suite still passes**

The `codex_install` and `agent_registry` tests read the live `commands/`/`agents/`; verify the move did not disturb them.

Run: `cd tools && python -m unittest discover -v`
Expected: PASS — `OK`, count is the previous 84 plus the new structure/manifest tests. In particular `codex_install.test_live_repo` still reports `n_cmds == 9` and the `agent_registry` consistency guard stays green (it merges duplicate agent names, so dropping `.ko.md` only removes redundant entries).

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "refactor(i18n): move command/agent .ko.md reference copies to i18n/ for clean plugin auto-discovery; simplify installers"
```

---

### Task 4: Dual-mode path resolver in `commands/ship.md`

**Files:**
- Create: `tools/plugin_packaging/test_resolver.py`
- Modify: `commands/ship.md` (the GitHub-tracking-init `GHS()` definition, step 2)

**Interfaces:**
- Produces: `ship.md` resolves `lib/gh_sync.sh` under `${CLAUDE_PLUGIN_ROOT}` in plugin mode and `$HOME/.claude/css` in script mode, honoring an explicit `$CSS_LIB`.

- [ ] **Step 1: Write the failing test**

Create `tools/plugin_packaging/test_resolver.py`:

```python
import os
import shutil
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SHIP = REPO / "commands" / "ship.md"

RESOLVER = (
    'CSS_ROOT="${CLAUDE_PLUGIN_ROOT}"; '
    'CSS_ROOT="${CSS_ROOT:-$HOME/.claude/css}"; '
    'printf "%s" "${CSS_LIB:-$CSS_ROOT/lib}"'
)


class ShipResolverTests(unittest.TestCase):
    def test_ship_embeds_dual_mode_resolver(self):
        text = SHIP.read_text(encoding="utf-8")
        self.assertIn('CSS_ROOT="${CLAUDE_PLUGIN_ROOT}"', text)
        self.assertIn('CSS_ROOT="${CSS_ROOT:-$HOME/.claude/css}"', text)
        self.assertIn('"${CSS_LIB:-$CSS_ROOT/lib}/gh_sync.sh"', text)

    def _resolve(self, **overrides):
        bash = shutil.which("bash")
        if bash is None:
            self.skipTest("bash not available")
        env = dict(os.environ)
        env.pop("CSS_LIB", None)
        env.pop("CLAUDE_PLUGIN_ROOT", None)
        env.update(overrides)
        return subprocess.run(
            [bash, "-c", RESOLVER], capture_output=True, text=True, env=env
        ).stdout

    def test_plugin_mode(self):
        self.assertEqual(
            self._resolve(CLAUDE_PLUGIN_ROOT="/x/plug", HOME="/home/u"), "/x/plug/lib"
        )

    def test_script_mode(self):
        self.assertEqual(self._resolve(HOME="/home/u"), "/home/u/.claude/css/lib")

    def test_explicit_css_lib_wins(self):
        self.assertEqual(
            self._resolve(CSS_LIB="/custom/lib", CLAUDE_PLUGIN_ROOT="/x/plug"),
            "/custom/lib",
        )
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd tools && python -m unittest plugin_packaging.test_resolver -v`
Expected: FAIL on `test_ship_embeds_dual_mode_resolver` (the snippet is not in `ship.md` yet). The three `_resolve` behavior tests PASS already (they validate the canonical snippet).

- [ ] **Step 3: Edit `ship.md`**

In `commands/ship.md`, find the GitHub-tracking-init line in step 2:

```
   - **GitHub tracking init**: define `GHS() { bash "${CSS_LIB:-$HOME/.claude/css/lib}/gh_sync.sh" "$@"; }`. Set `gh_on = ...
```

Replace the `define ...` clause with the dual-mode resolver:

```
   - **GitHub tracking init**: resolve the CSS root for both install modes, then define the helper — `CSS_ROOT="${CLAUDE_PLUGIN_ROOT}"; CSS_ROOT="${CSS_ROOT:-$HOME/.claude/css}"; GHS() { bash "${CSS_LIB:-$CSS_ROOT/lib}/gh_sync.sh" "$@"; }` (in plugin mode `${CLAUDE_PLUGIN_ROOT}` is substituted inline; in script mode it is empty and falls back to `$HOME/.claude/css`). Set `gh_on = ...
```

Keep the rest of the sentence (`Set gh_on = ...`, `init-issue`) unchanged. Do not touch any line containing `/css:phase --session` or `.claude/css/`.

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd tools && python -m unittest plugin_packaging.test_resolver -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Confirm the semantic guard still passes**

Run: `cd tools && python -m unittest agent_registry.test_pipeline_contracts agent_registry.test_registry -v`
Expected: PASS (ship.md still contains `/css:phase --session` and `.claude/css/`).

- [ ] **Step 6: Commit**

```bash
git add tools/plugin_packaging/test_resolver.py commands/ship.md
git commit -m "feat(plugin): dual-mode lib path resolver in ship.md (plugin + script installs)"
```

---

### Task 5: `lib/gh_sync.sh` config fallback to the bundled default

**Files:**
- Modify: `lib/gh_sync.sh` (`config_path()` at line 29; add `__test_config_path` hook near line 90 and a dispatch case near line 310)
- Modify: `tests/gh_sync/test_gh_sync.sh` (add a test function)

**Interfaces:**
- Produces: `config_path` resolves to `$CSS_CONFIG`, else the user config, else the bundled `../config/default-config.json` shipped beside the script.

- [ ] **Step 1: Add the test-only hook and dispatch case**

In `lib/gh_sync.sh`, after the existing hook at line 90:

```bash
__test_status() { set_board_status "$1" "$2"; }   # test-only hook
```

add:

```bash
__test_config_path() { config_path; }             # test-only hook
```

Then in `main()`, after the dispatch case at line 310:

```bash
    __test_status) __test_status "$@" ;;
```

add:

```bash
    __test_config_path) __test_config_path "$@" ;;
```

- [ ] **Step 2: Add the failing bash test**

In `tests/gh_sync/test_gh_sync.sh`, add this function (place it alongside the other `test_*` functions, above the runner block at the end of the file):

```bash
test_config_path_resolution() {
  local sb; sb="$(mktemp -d)"
  # explicit override wins
  assert_eq "explicit CSS_CONFIG" \
    "$(CSS_CONFIG="$sb/x.json" bash "$SCRIPT" __test_config_path)" "$sb/x.json"
  # no override, no user config -> bundled default beside the script
  assert_contains "bundled default" \
    "$(CSS_CONFIG= HOME="$sb/home" bash "$SCRIPT" __test_config_path)" \
    "config/default-config.json"
  # user config present -> used
  mkdir -p "$sb/home/.claude/css"; printf '{}' > "$sb/home/.claude/css/config.json"
  assert_eq "user config" \
    "$(CSS_CONFIG= HOME="$sb/home" bash "$SCRIPT" __test_config_path)" \
    "$sb/home/.claude/css/config.json"
  rm -rf "$sb"
}
```

- [ ] **Step 3: Run the bash suite to verify it fails**

Run: `cd tools && python -m unittest gh_sync_bridge.test_gh_sync_bridge -v`
Expected: FAIL — the `bundled default` and `user config` assertions fail because `config_path` still returns `$HOME/.claude/css/config.json` unconditionally.

- [ ] **Step 4: Update `config_path()`**

In `lib/gh_sync.sh`, replace line 29:

```bash
config_path() { printf '%s' "${CSS_CONFIG:-$HOME/.claude/css/config.json}"; }
```

with:

```bash
config_path() {
  if [[ -n "${CSS_CONFIG:-}" ]]; then printf '%s' "$CSS_CONFIG"; return; fi
  local user="$HOME/.claude/css/config.json"
  if [[ -f "$user" ]]; then printf '%s' "$user"; return; fi
  local here; here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  local bundled="$here/../config/default-config.json"
  if [[ -f "$bundled" ]]; then printf '%s' "$bundled"; return; fi
  printf '%s' "$user"
}
```

- [ ] **Step 5: Run the bash suite to verify it passes**

Run: `cd tools && python -m unittest gh_sync_bridge.test_gh_sync_bridge -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add lib/gh_sync.sh tests/gh_sync/test_gh_sync.sh
git commit -m "feat(plugin): gh_sync config_path falls back to bundled default (plugin install)"
```

---

### Task 6: Documentation — add the plugin install option

**Files:**
- Modify: `README.md` (install section ~lines 208-230; directory-structure block)
- Modify: `README.en.md` (matching English sections)
- Modify: `docs/installation.md` and `docs/installation.ko.md` (add a plugin section)
- Modify: `tools/plugin_packaging/test_structure.py` (add a docs assertion)

**Interfaces:**
- Consumes: marketplace name `css-claude`, plugin name `css` (Tasks 1-2).

- [ ] **Step 1: Write the failing test**

Append to `tools/plugin_packaging/test_structure.py`:

```python
class DocsTests(unittest.TestCase):
    def test_readmes_document_plugin_install(self):
        for name in ("README.md", "README.en.md"):
            text = (REPO / name).read_text(encoding="utf-8")
            self.assertIn("/plugin marketplace add", text, f"{name} missing plugin install")
            self.assertIn("css@css-claude", text, f"{name} missing install target")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd tools && python -m unittest plugin_packaging.test_structure.DocsTests -v`
Expected: FAIL — `README.md missing plugin install`.

- [ ] **Step 3: Add the plugin install option to `README.md`**

In `README.md`, under `## 설치` (the install section), add a plugin option **above** the existing platform-script bullets (keep the scripts):

```markdown
플러그인으로 설치 (Claude Code):

```
/plugin marketplace add songsub-cha/css-claude
/plugin install css@css-claude
```

또는 플랫폼 스크립트로 설치 (기존 방식, 계속 지원):
```

Then update the directory-structure block to add the two new entries:

```
├── .claude-plugin/  # plugin.json + marketplace.json (플러그인 배포)
├── i18n/            # commands/agents 한국어 참조 번역(.ko.md)
```

- [ ] **Step 4: Add the matching English section to `README.en.md`**

In `README.en.md`, under its install heading, add above the script bullets:

```markdown
Install as a plugin (Claude Code):

```
/plugin marketplace add songsub-cha/css-claude
/plugin install css@css-claude
```

Or install with the platform scripts (still supported):
```

Add the same two directory-structure rows (`.claude-plugin/`, `i18n/`).

- [ ] **Step 5: Add a plugin section to the installation docs**

Append a short "Install as a plugin" section to both `docs/installation.md` and `docs/installation.ko.md`, each containing the two `/plugin …` commands from Step 3 and a note that `version` in `plugin.json` must be bumped per release for users to receive updates.

- [ ] **Step 6: Run the test to verify it passes**

Run: `cd tools && python -m unittest plugin_packaging.test_structure.DocsTests -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add README.md README.en.md docs/installation.md docs/installation.ko.md tools/plugin_packaging/test_structure.py
git commit -m "docs(plugin): document marketplace install alongside the scripts"
```

---

### Task 7: Final validation

**Files:** none (verification only)

- [ ] **Step 1: Run the entire Python suite**

Run: `cd tools && python -m unittest discover -v`
Expected: `OK`. All prior 84 tests plus the new manifest/structure/resolver tests pass.

- [ ] **Step 2: Validate the plugin manifest with the CLI (if available)**

Run: `claude plugin validate . --strict`
Expected: passes with no errors. If the `claude` CLI is unavailable in this environment, skip and rely on Step 1's manifest tests.

- [ ] **Step 3: Manual smoke checklist (record results in the PR description)**

- `/plugin marketplace add ./` (or `songsub-cha/css-claude`) lists the `css` plugin.
- After install, `/css:ship` is available and `Task(subagent_type="css-pr-creator")` resolves by bare name.
- `bash scripts/install.sh` (or `install.ps1`) still copies 9 commands + 21 agents and runs unchanged.

- [ ] **Step 4: Final commit (only if Step 3 required doc tweaks)**

```bash
git add -A
git commit -m "chore(plugin): finalize plugin packaging validation"
```

---

## Self-Review

**Spec coverage** (against `docs/superpowers/specs/2026-06-25-css-plugin-packaging-design.md`):

- §7.1 plugin.json → Task 1 ✓
- §7.2 marketplace.json → Task 2 ✓
- §7.3 `.ko.md` → `i18n/` → Task 3 ✓
- §7.4 dual-mode resolver → Task 4 ✓
- §7.5 gh_sync config fallback → Task 5 ✓
- §7.6 installer touch-ups → Task 3 (Steps 5-6) ✓; codex installer needs no change (Task 3 Step 7 confirms) ✓
- §7.7 docs → Task 6 ✓
- §7.8 tests (manifest validity, discovery integrity, resolver, gh_sync fallback) → Tasks 1,2,3,4,5 ✓
- §10 verification → Task 7 ✓

**Placeholder scan:** No TBD/TODO; every code step shows full content; commands have expected output.

**Type/name consistency:** `CSS_ROOT`, `CSS_LIB`, `config_path`, `__test_config_path`, marketplace name `css-claude`, plugin name `css`, install target `css@css-claude` are used identically across tasks and tests.

**Non-goals honored:** license string points to the existing LICENSE file (no change); no Codex files modified; marketplace is in-repo; docs are additive.
