> **English** · 한국어 reference copy may be added at the document stage.

# CSS Plugin Packaging — Design

**Status:** Draft (brainstorming output, awaiting review)
**Date:** 2026-06-25
**Topic:** Distribute the CSS pipeline as an official Claude Code plugin via a self-hosted marketplace.

---

## 1. Context & Problem

`css-claude` is the source of the CSS (Claude Super System) pipeline: 9 slash commands (`commands/*.md`), 21 subagents (`agents/*.md`), a GitHub-sync helper (`lib/gh_sync.sh`), default config (`config/default-config.json`), Python tooling with pytest (`tools/`), and a Codex runtime path (`codex/`, `tools/codex_install/`).

Today it is **not** a Claude Code plugin. It is distributed by **copy-on-install scripts** (`scripts/install.sh`, `scripts/install.ps1`) that place files under `~/.claude/commands/css/`, `~/.claude/agents/css/`, `~/.claude/css/lib/`, and `~/.claude/css/config.json`. Commands hardcode the install path via `${CSS_LIB:-$HOME/.claude/css/lib}` and `${CSS_CONFIG:-$HOME/.claude/css/config.json}`.

We want it installable the standard way: `/plugin marketplace add` → `/plugin install`.

## 2. Goals

- Make the repo installable as a Claude Code plugin through a **self-hosted marketplace** living in the same repo.
- Keep the existing **`/css:*` command namespace** and **`css-*` agent dispatch** unchanged.
- **Coexist** with the current script installers and the Codex install path — nothing deprecated.

## 3. Non-Goals (explicitly out of scope)

- **License change.** The repo stays "personal use; redistribution not permitted at this stage." No public-release posture.
- **External-user docs overhaul.** Only an additive "install as a plugin" section.
- **Codex restructuring.** Codex cannot consume Claude Code plugins; `install-codex.*` and `codex/RUNTIME.md` are untouched.
- **A separate marketplace repo.** The marketplace is in-repo.

## 4. Confirmed Decisions

| # | Decision | Choice |
|---|----------|--------|
| D1 | Distribution level | Marketplace distribution (plugin.json + marketplace.json in same repo) |
| D2 | Legacy installers | Full parallel — scripts kept and equally recommended, nothing deprecated |
| D3 | `.ko.md` auto-discovery conflict | **Move** `commands/*.ko.md` and `agents/*.ko.md` into an `i18n/` tree |

## 5. Verified Platform Facts (de-risking)

From the current Claude Code docs (`code.claude.com/docs/en/plugins-reference`, `…/plugin-marketplaces`, `…/sub-agents`):

1. **Plugin name namespaces commands.** Plugin `css` + `commands/ship.md` → `/css:ship`. So the plugin **must be named `css`** to preserve the existing namespace.
2. **Agents dispatch by bare frontmatter name.** "For a plugin-provided subagent, you can pass just the agent name and Claude Code will find it"; the `plugin:name` form is only for disambiguation on collisions. → `Task(subagent_type="css-executor")` keeps working in plugin mode. **No agent renames, no dispatch edits.**
3. **`${CLAUDE_PLUGIN_ROOT}` is substituted inline in command/agent content** (and exported to subprocess env for hooks/MCP/LSP). This enables a dual-mode path resolver.
4. **`commands`/`agents` manifest fields replace the default scan**, while omitting them keeps auto-discovery of `commands/` and `agents/`. Because we move `.ko.md` out (D3), we **omit** those fields and rely on clean auto-discovery.
5. **Marketplace `source: "./"`** points at the repo root as the plugin; `plugin.json` and `marketplace.json` can both live in `.claude-plugin/`. Marketplace name `css-claude` is not reserved.
6. **Version pinning.** If `version` is set in `plugin.json`, users only update when it is bumped; if omitted, the git commit SHA is the version (per-commit updates).

## 6. Architecture — Single Source, Dual Loading

The same file tree must work under two loaders:

| | Plugin install | Script install |
|---|----------------|----------------|
| Commands | auto-discovered as `/css:*` from `commands/` | copied to `~/.claude/commands/css/` |
| Agents | auto-discovered, dispatched by bare `css-*` name | copied to `~/.claude/agents/css/` |
| `lib/`, `config/` | read from `${CLAUDE_PLUGIN_ROOT}` | read from `~/.claude/css/` |
| Root anchor | `${CLAUDE_PLUGIN_ROOT}` (substituted) | `$HOME/.claude/css` (fallback) |

A one-line resolver bridges the anchor difference. Everything else is identical.

## 7. Detailed Design

### 7.1 `.claude-plugin/plugin.json`

```jsonc
{
  "$schema": "https://json.schemastore.org/claude-code-plugin-manifest.json",
  "name": "css",
  "displayName": "CSS — Claude Super System",
  "version": "0.1.0",
  "description": "Idea → spec → plan → review → TDD → verify → docs → PR pipeline with domain-specialist agents and human approval gates.",
  "author": { "name": "songsub-cha", "email": "sub1904@gmail.com" },
  "homepage": "https://github.com/songsub-cha/css-claude",
  "repository": "https://github.com/songsub-cha/css-claude",
  "license": "SEE LICENSE IN LICENSE",
  "keywords": ["pipeline", "tdd", "automation", "agents", "workflow", "code-review"]
}
```

- **No `commands`/`agents` fields** — auto-discovery handles `commands/*.md` and `agents/*.md` once `.ko.md` is moved out (D3).
- `version: "0.1.0"` is explicit; release discipline (§7.7) requires bumping it on each release. (Alternative: omit for commit-SHA versioning during rapid iteration — open for review.)

### 7.2 `.claude-plugin/marketplace.json`

```jsonc
{
  // $schema omitted — no documented marketplace schema URL; verify before adding.
  "name": "css-claude",
  "owner": { "name": "songsub-cha", "email": "sub1904@gmail.com" },
  "plugins": [
    {
      "name": "css",
      "source": "./",
      "description": "Idea → PR software-development pipeline for Claude Code."
    }
  ]
}
```

User flow: `/plugin marketplace add songsub-cha/css-claude` → `/plugin install css@css-claude`.

### 7.3 `.ko.md` → `i18n/` (D3)

- `git mv commands/*.ko.md i18n/commands/` (9 files)
- `git mv agents/*.ko.md i18n/agents/` (21 files)
- `docs/*.ko.md` stay put — they are cross-linked from English docs and are not scanned by the plugin loader.
- After the move, `commands/` and `agents/` contain only English `.md`, so plugin auto-discovery registers exactly the 9 commands and 21 agents with no `.ko` duplicates.

### 7.4 Dual-mode path resolver

Only `commands/ship.md` references the lib path among commands (other stages are orchestrated by `ship.md`). Replace the `GHS` helper definition:

```bash
# Resolve CSS root for both plugin and script installs.
CSS_ROOT="${CLAUDE_PLUGIN_ROOT}"          # substituted to an abs path in plugin mode
CSS_ROOT="${CSS_ROOT:-$HOME/.claude/css}" # empty in script mode → home fallback
GHS() { bash "$CSS_ROOT/lib/gh_sync.sh" "$@"; }
```

- Plugin mode: content substitution yields `CSS_ROOT=/abs/plugin/path` → `…/lib/gh_sync.sh` (the plugin ships `lib/` at its root).
- Script mode: `${CLAUDE_PLUGIN_ROOT}` is unset, bash expands it to empty, `:-` falls back to `$HOME/.claude/css/lib/gh_sync.sh`.
- The legacy `${CSS_LIB:-…}` override remains honored for anyone setting it explicitly.

### 7.5 `lib/gh_sync.sh` config fallback

`gh_sync.sh` runs as a subprocess and may not receive `${CLAUDE_PLUGIN_ROOT}`. Make `config_path()` resolve in order:

1. `$CSS_CONFIG` if set (explicit override — unchanged).
2. `$HOME/.claude/css/config.json` if it exists (user config / script install).
3. The script's bundled default, located relative to itself: `"$(dirname "$0")/../config/default-config.json"` (plugin-only users who never ran a script installer).
4. Fall back to `$HOME/.claude/css/config.json` (preserves current error path when nothing exists).

This needs **no install-time hook** to seed config (YAGNI). User overrides still live at `~/.claude/css/config.json` in both modes.

### 7.6 Installer & codex-installer touch-ups

- `scripts/install.sh` / `install.ps1`: the `*.ko.md` skip becomes dead code after D3. Simplify to a plain `commands/*.md` / `agents/*.md` copy. Functionally identical.
- `tools/codex_install/installer.py`: `_source_md()` filters stems containing `.` — **location-independent**, so no functional change is required after the move. Re-run `tools/codex_install/test_*.py`; update any fixture/assertion that referenced real `commands/*.ko.md` paths.

### 7.7 Docs

- `README.md` / `README.en.md`: add an **"Install as a plugin"** option alongside (not replacing) the script instructions; add `.claude-plugin/` and `i18n/` to the directory-structure block.
- `docs/installation.md` / `installation.ko.md`: add a plugin-install section.
- Note the version-bump release discipline where the plugin install is documented.

### 7.8 Tests (added under `tools/`, pytest)

1. **Manifest validity** — assert `plugin.json` and `marketplace.json` are valid JSON with required fields (`name`; marketplace `name`/`owner`/`plugins[].{name,source}`). If `claude` CLI is available in CI, also run `claude plugin validate --strict`.
2. **Discovery integrity** — assert `commands/` and `agents/` contain only `*.md` with no `.` in the stem (no stray `.ko.md`), and that `i18n/commands` + `i18n/agents` hold the moved translations (counts match the originals: 9 + 21).
3. **Path resolver** — a bash-level test of the dual-mode `CSS_ROOT` snippet: with `CLAUDE_PLUGIN_ROOT` set → resolves under it; unset → resolves under `$HOME/.claude/css`.
4. **gh_sync config fallback** — extend `tools/gh_sync_bridge` coverage: user config present → used; absent → bundled `config/default-config.json` is read.

## 8. Component Boundaries

| Unit | Responsibility | Depends on |
|------|----------------|-----------|
| `plugin.json` | Declare the plugin; name → namespace | none |
| `marketplace.json` | Catalog the plugin at `./` | `plugin.json` |
| `i18n/` move | Keep auto-discovery clean | — |
| `ship.md` resolver | Locate `lib/` in both modes | `CLAUDE_PLUGIN_ROOT` |
| `gh_sync.sh` config fallback | Locate config in both modes | bundled `config/` |
| Installer touch-ups | Keep script path correct post-move | `i18n/` move |
| Docs | Document the new install option | manifests |
| Tests | Lock in all of the above | all |

Each unit is independently testable and reviewable.

## 9. Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Plugin agent dispatch needs `css:`-prefix | Verified bare-name dispatch works (§5.2); guard via a smoke note in docs |
| `${CLAUDE_PLUGIN_ROOT}` not substituted as expected | Dual-mode `:-` fallback is safe whether substituted or bash-expanded-to-empty; covered by resolver test (§7.8.3) |
| codex installer tests reference real `.ko.md` paths | Re-run codex tests; update fixtures (§7.6) |
| `version` pinning forgotten on release | Document the bump discipline; CHANGELOG entry per release (§7.7) |
| Plugin-cache read-only vs config writes | Config/state writes target `~/.claude/css/` and `<project>/.claude/css/`, never the plugin cache (§7.5) |

## 10. Verification / Done Criteria

- `claude plugin validate --strict` passes (or JSON-schema test passes where CLI is absent).
- Fresh plugin install exposes `/css:ship` and dispatches `css-executor` et al. by bare name.
- Existing `scripts/install.sh` still installs and runs unchanged.
- `tools/` pytest suite (including new tests) is green.
- README documents both install paths.

## 11. Out-of-Scope Confirmations

License unchanged; Codex path unchanged; no separate marketplace repo; no external-user doc rewrite.
