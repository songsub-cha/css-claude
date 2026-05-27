# CSS Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the CSS (Claude Super System) pipeline — eight `/css:*` Claude Code commands backed by 18 sub-agents that walk a feature from idea to merged PR with TDD, multi-pass review/verify, and three approval gates.

**Architecture:** Three-layer system (commands → agents → state). Commands at `~/.claude/commands/css/` are thin orchestrators. Agents at `~/.claude/agents/css/` are stage- and domain-specific workers. Per-project state lives in `<project>/.claude/css/sessions/{slug}.json` enabling multi-session concurrency. Heavy lifting for `/css:interview` and `/css:plan` delegates to `superpowers:brainstorming` and `superpowers:writing-plans`.

**Tech Stack:**
- Claude Code (commands + agents via markdown files with YAML frontmatter)
- PowerShell 5.1+ (Windows installer)
- Bash + `jq` (Ubuntu installer)
- `gh` CLI (PR creation)
- `git` ≥ 2.5 (worktrees)
- No build step — pure markdown distribution

**Source spec:** [`docs/specs/2026-05-27-css-pipeline-design.md`](../specs/2026-05-27-css-pipeline-design.md)

---

## Phase Map

| Phase | Scope | Deliverable |
|-------|-------|-------------|
| 1. Foundation | Repo scaffolding, default config, installers, session helper conventions | Installable empty shell |
| 2. CSS-native stage agents | reviewer, executor, verifier, code-reviewer, documenter, pr-creator | Agents callable via `Task` (no commands yet) |
| 3. OMC-adapted domain agents | 12 specialist agents copied from OMC with CSS headers | Specialists callable via `Task` |
| 4. Commands | 8 `/css:*` markdown files | Working pipeline end-to-end |
| 5. Integration + release | Toy fixtures, smoke tests, docs, `v0.1.0` tag | Released v0.1.0 |

Each phase produces something testable on its own.

---

## Repository Layout (final)

```
css-claude/
├── README.md
├── LICENSE
├── .gitignore
├── commands/
│   ├── interview.md
│   ├── plan.md
│   ├── review.md
│   ├── execute.md
│   ├── verify.md
│   ├── document.md
│   ├── pr.md
│   └── ship.md
├── agents/
│   ├── reviewer.md
│   ├── executor.md
│   ├── verifier.md
│   ├── code-reviewer.md
│   ├── documenter.md
│   ├── pr-creator.md
│   ├── api-specialist.md
│   ├── ui-engineer.md
│   ├── architect.md
│   ├── db-specialist.md
│   ├── infra-engineer.md
│   ├── security-reviewer.md
│   ├── test-engineer.md
│   ├── debugger.md
│   ├── code-simplifier.md
│   ├── async-coder.md
│   ├── langgraph-engineer.md
│   └── prompt-engineer.md
├── config/
│   └── default-config.json
├── scripts/
│   ├── install.ps1
│   ├── install.sh
│   ├── uninstall.ps1
│   └── uninstall.sh
├── docs/
│   ├── specs/
│   │   └── 2026-05-27-css-pipeline-design.md
│   ├── plans/
│   │   └── 2026-05-27-css-pipeline-implementation.md
│   ├── installation.md
│   ├── usage.md
│   └── troubleshooting.md
└── tests/
    ├── fixtures/
    │   ├── toy-typescript/
    │   ├── toy-python/
    │   ├── toy-go/
    │   └── toy-android/
    └── agents/
        └── (golden files)
```

---

## Conventions Used by All Tasks

### Frontmatter Template (agents)

```yaml
---
name: css-<role>
description: <one-line role description> (CSS pipeline, <model>)
model: opus | sonnet | haiku
disallowedTools: [Write, Edit]   # for read-only agents only
css_stages: [<stage>, ...]       # array; e.g. [verify], [execute], [review]
adapted_from: oh-my-claudecode/agents/<source>.md   # for OMC-adapted agents only
---
```

### Frontmatter Template (commands)

```yaml
---
description: <one-line user-facing description>
argument-hint: "[--flags] <args>"
---
```

### Standard "Output Contract" Section (every agent)

```markdown
<Output_Contract>
- Write artifact to: <exact path>
- Final line MUST be: VERDICT=<value> | NEXT=<value> | ARTIFACT=<path>
- All user-facing text in Korean; system policies and constraints stay in English in this file
- Echo session slug at top of response when called via standalone command
</Output_Contract>
```

### Standard "Self Check" Section (every command)

```markdown
<self_check>
- [ ] Artifact written to documented path
- [ ] session file (sessions/{slug}.json) phase status updated
- [ ] _active.json.latest_slug updated when applicable
- [ ] Final line contains VERDICT=... or NEXT=... or ARTIFACT=...
- [ ] No policy violations
</self_check>
```

### Commit Message Conventions

Use Conventional Commits with these scopes:
- `feat(commands): ...` — new command file
- `feat(agents): ...` — new agent file
- `feat(scripts): ...` — installer changes
- `fix(...)` / `docs(...)` / `chore(...)`

---

# PHASE 1: Foundation

Goal: a repository structure that can be installed by either platform script, with default config in place. No commands or agents yet — those phases land next.

## Task 1.1: Add LICENSE file

**Files:**
- Create: `LICENSE`

- [ ] **Step 1: Write the LICENSE file**

```
Copyright (c) 2026 songsub-cha

All Rights Reserved.

This software is provided for personal use by the copyright holder only.
Redistribution, modification, or commercial use is not permitted without
prior written consent.
```

- [ ] **Step 2: Commit**

```bash
git add LICENSE
git commit -m "chore: add personal-use LICENSE"
```

## Task 1.2: Scaffold empty directories with .gitkeep

**Files:**
- Create: `commands/.gitkeep`
- Create: `agents/.gitkeep`
- Create: `config/.gitkeep`
- Create: `scripts/.gitkeep`
- Create: `tests/fixtures/.gitkeep`
- Create: `tests/agents/.gitkeep`
- Create: `docs/plans/.gitkeep`

- [ ] **Step 1: Create the empty placeholders**

Create each file with empty contents using `git ls-files -- '.gitkeep'` after to verify.

- [ ] **Step 2: Commit**

```bash
git add commands/.gitkeep agents/.gitkeep config/.gitkeep scripts/.gitkeep tests/fixtures/.gitkeep tests/agents/.gitkeep docs/plans/.gitkeep
git commit -m "chore: scaffold empty directories for upcoming phases"
```

## Task 1.3: Add default-config.json

**Files:**
- Create: `config/default-config.json`
- Modify (none yet)

- [ ] **Step 1: Write default-config.json**

```json
{
  "version": "1.0.0",
  "interview": {
    "ambiguity_threshold": 0.2,
    "max_rounds": 20
  },
  "review": {
    "max_loopback_attempts": 2
  },
  "verify": {
    "coverage_threshold": 85,
    "max_loopback_attempts": 3
  },
  "execute": {
    "tdd_self_heal_max": 2,
    "worktree_parent": null
  },
  "language_overrides": {
    "test_command": null,
    "coverage_command": null
  },
  "pr": {
    "default_base_branch": null,
    "default_draft": false
  }
}
```

- [ ] **Step 2: Validate JSON syntax**

Run: `python -c "import json; json.load(open('config/default-config.json'))"` (or any other JSON validator available)
Expected: no output, exit 0.

- [ ] **Step 3: Commit**

```bash
git add config/default-config.json
git commit -m "feat(config): add default global config"
```

## Task 1.4: Write Windows installer (install.ps1)

**Files:**
- Create: `scripts/install.ps1`

- [ ] **Step 1: Write install.ps1**

```powershell
<#
.SYNOPSIS
  Install CSS (Claude Super System) commands and agents into the user's Claude Code config.

.PARAMETER SourcePath
  Path to the cloned css-claude repo. Defaults to the repo containing this script.

.PARAMETER Force
  Overwrite existing default config (commands/agents are always refreshed).

.EXAMPLE
  .\scripts\install.ps1
  .\scripts\install.ps1 -SourcePath C:\code\css-claude -Force
#>
[CmdletBinding()]
param(
  [string]$SourcePath = (Join-Path $PSScriptRoot ".."),
  [switch]$Force
)

$ErrorActionPreference = "Stop"

function Write-Section($msg) {
  Write-Host ""
  Write-Host "=== $msg ===" -ForegroundColor Cyan
}

function Test-Prereq($name, $check, $hint) {
  if (& $check) {
    Write-Host "  [OK] $name" -ForegroundColor Green
  } else {
    Write-Host "  [MISSING] $name" -ForegroundColor Red
    Write-Host "    $hint" -ForegroundColor Yellow
    return $false
  }
  return $true
}

Write-Section "Verifying prerequisites"

$ok = $true
$ok = (Test-Prereq "git" { (Get-Command git -ErrorAction SilentlyContinue) -ne $null } "Install git for Windows: https://git-scm.com/download/win") -and $ok
$ok = (Test-Prereq "gh CLI" { (Get-Command gh -ErrorAction SilentlyContinue) -ne $null } "Install gh: winget install GitHub.cli") -and $ok

$claudeHome = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $env:USERPROFILE ".claude" }
$ok = (Test-Prereq "Claude config dir ($claudeHome)" { Test-Path $claudeHome } "Run Claude Code at least once to create $claudeHome") -and $ok

if (-not $ok) {
  Write-Host ""
  Write-Host "Aborting: fix the missing prerequisites above and re-run." -ForegroundColor Red
  exit 1
}

# superpowers warning (non-fatal)
$settingsPath = Join-Path $claudeHome "settings.json"
if (Test-Path $settingsPath) {
  $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
  $sp = $settings.enabledPlugins.'superpowers@claude-plugins-official'
  if (-not $sp) {
    Write-Host "  [WARN] superpowers plugin not enabled in settings.json" -ForegroundColor Yellow
    Write-Host "         CSS depends on it. Enable via /plugin or edit settings.json." -ForegroundColor Yellow
  } else {
    Write-Host "  [OK] superpowers plugin enabled" -ForegroundColor Green
  }
}

Write-Section "Creating directories"
$cmdDir   = Join-Path $claudeHome "commands\css"
$agentDir = Join-Path $claudeHome "agents\css"
$cssDir   = Join-Path $claudeHome "css"
New-Item -ItemType Directory -Force -Path $cmdDir, $agentDir, $cssDir | Out-Null
Write-Host "  $cmdDir"
Write-Host "  $agentDir"
Write-Host "  $cssDir"

Write-Section "Copying commands"
$srcCmd = Join-Path $SourcePath "commands"
$cmdFiles = Get-ChildItem $srcCmd -Filter "*.md" -ErrorAction SilentlyContinue
foreach ($f in $cmdFiles) {
  Copy-Item $f.FullName -Destination $cmdDir -Force
  Write-Host "  $($f.Name)"
}
Write-Host "  ($($cmdFiles.Count) command files copied)"

Write-Section "Copying agents"
$srcAgent = Join-Path $SourcePath "agents"
$agentFiles = Get-ChildItem $srcAgent -Filter "*.md" -ErrorAction SilentlyContinue
foreach ($f in $agentFiles) {
  Copy-Item $f.FullName -Destination $agentDir -Force
  Write-Host "  $($f.Name)"
}
Write-Host "  ($($agentFiles.Count) agent files copied)"

Write-Section "Installing default config"
$srcConfig = Join-Path $SourcePath "config\default-config.json"
$dstConfig = Join-Path $cssDir "config.json"
if ((Test-Path $dstConfig) -and -not $Force) {
  Write-Host "  [SKIP] $dstConfig already exists (use -Force to overwrite)" -ForegroundColor Yellow
} else {
  Copy-Item $srcConfig -Destination $dstConfig -Force
  Write-Host "  $dstConfig"
}

Write-Section "Done"
Write-Host "Installed:"
Write-Host "  $($cmdFiles.Count) commands in $cmdDir"
Write-Host "  $($agentFiles.Count) agents   in $agentDir"
Write-Host "  config at        $dstConfig"
Write-Host ""
Write-Host "Try: /css:ship `"<small idea>`" in a sample project."
```

- [ ] **Step 2: Lint with PSScriptAnalyzer if available**

Run: `Invoke-ScriptAnalyzer -Path scripts/install.ps1 -Severity Warning,Error`
Expected: no errors (warnings about CmdletBinding usage are fine).

If PSScriptAnalyzer not installed, skip this step.

- [ ] **Step 3: Dry-run the script in a clean Windows session**

In a separate PowerShell window, set a fake CLAUDE_CONFIG_DIR to a temp dir to avoid touching the real install:

```powershell
$env:CLAUDE_CONFIG_DIR = "$env:TEMP\css-install-dryrun"
New-Item -ItemType Directory -Force -Path $env:CLAUDE_CONFIG_DIR | Out-Null
.\scripts\install.ps1
```

Expected: script reports OK for git/gh/config dir, copies 0 files (since agents/commands are still empty), creates css dir with config.json.

Clean up: `Remove-Item -Recurse -Force $env:CLAUDE_CONFIG_DIR`

- [ ] **Step 4: Commit**

```bash
git add scripts/install.ps1
git commit -m "feat(scripts): add Windows PowerShell installer"
```

## Task 1.5: Write Windows uninstaller (uninstall.ps1)

**Files:**
- Create: `scripts/uninstall.ps1`

- [ ] **Step 1: Write uninstall.ps1**

```powershell
<#
.SYNOPSIS
  Remove CSS commands and agents from the user's Claude Code config.
  Preserves ~/.claude/css/config.json and per-project artifacts.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$claudeHome = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $env:USERPROFILE ".claude" }
$cmdDir   = Join-Path $claudeHome "commands\css"
$agentDir = Join-Path $claudeHome "agents\css"

foreach ($d in @($cmdDir, $agentDir)) {
  if (Test-Path $d) {
    Remove-Item -Recurse -Force $d
    Write-Host "Removed $d" -ForegroundColor Green
  } else {
    Write-Host "Skip (absent): $d" -ForegroundColor Yellow
  }
}

Write-Host ""
Write-Host "Kept:"
Write-Host "  $(Join-Path $claudeHome 'css\config.json') — your personal defaults"
Write-Host "  <project>/.claude/css/ — per-project artifacts (remove manually if no longer needed)"
Write-Host ""
Write-Host "To reinstall: scripts\install.ps1"
```

- [ ] **Step 2: Commit**

```bash
git add scripts/uninstall.ps1
git commit -m "feat(scripts): add Windows PowerShell uninstaller"
```

## Task 1.6: Write Ubuntu installer (install.sh)

**Files:**
- Create: `scripts/install.sh`

- [ ] **Step 1: Write install.sh**

```bash
#!/usr/bin/env bash
# install.sh — Ubuntu 22.04 installer for CSS (Claude Super System)
#
# Usage:
#   bash scripts/install.sh                    # install from cloned repo
#   FORCE=1 bash scripts/install.sh            # overwrite existing config

set -euo pipefail

SOURCE_PATH="${SOURCE_PATH:-$(cd "$(dirname "$0")/.." && pwd)}"
CLAUDE_HOME="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
FORCE="${FORCE:-0}"

# --- helpers ---
section() { echo; echo "=== $1 ==="; }
ok()      { printf "  \033[32m[OK]\033[0m %s\n" "$1"; }
warn()    { printf "  \033[33m[WARN]\033[0m %s\n" "$1"; }
fail()    { printf "  \033[31m[MISSING]\033[0m %s\n" "$1"; }
need()    {
  if command -v "$1" >/dev/null 2>&1; then
    ok "$1"
  else
    fail "$1 (hint: $2)"
    return 1
  fi
}

# --- prerequisites ---
section "Verifying prerequisites"
ok_count=0
fail_count=0
for tool_hint in \
  "git=Install git: sudo apt-get install -y git" \
  "gh=Install gh: https://cli.github.com/manual/installation" \
  "jq=Install jq: sudo apt-get install -y jq"
do
  tool="${tool_hint%%=*}"
  hint="${tool_hint#*=}"
  if need "$tool" "$hint"; then
    ok_count=$((ok_count + 1))
  else
    fail_count=$((fail_count + 1))
  fi
done

if [ ! -d "$CLAUDE_HOME" ]; then
  fail "Claude config dir ($CLAUDE_HOME) — run Claude Code at least once first"
  fail_count=$((fail_count + 1))
else
  ok "Claude config dir ($CLAUDE_HOME)"
fi

if [ "$fail_count" -gt 0 ]; then
  echo
  echo "Aborting: fix the missing prerequisites above and re-run." >&2
  exit 1
fi

# superpowers warning (non-fatal)
settings_path="$CLAUDE_HOME/settings.json"
if [ -f "$settings_path" ]; then
  if jq -e '.enabledPlugins["superpowers@claude-plugins-official"] == true' "$settings_path" >/dev/null 2>&1; then
    ok "superpowers plugin enabled"
  else
    warn "superpowers plugin not enabled in settings.json"
    warn "CSS depends on it. Enable via /plugin or edit settings.json."
  fi
fi

# --- create dirs ---
section "Creating directories"
cmd_dir="$CLAUDE_HOME/commands/css"
agent_dir="$CLAUDE_HOME/agents/css"
css_dir="$CLAUDE_HOME/css"
mkdir -p "$cmd_dir" "$agent_dir" "$css_dir"
echo "  $cmd_dir"
echo "  $agent_dir"
echo "  $css_dir"

# --- copy ---
section "Copying commands"
cmd_count=0
if compgen -G "$SOURCE_PATH/commands/*.md" >/dev/null; then
  for f in "$SOURCE_PATH"/commands/*.md; do
    cp "$f" "$cmd_dir/"
    echo "  $(basename "$f")"
    cmd_count=$((cmd_count + 1))
  done
fi
echo "  ($cmd_count command files copied)"

section "Copying agents"
agent_count=0
if compgen -G "$SOURCE_PATH/agents/*.md" >/dev/null; then
  for f in "$SOURCE_PATH"/agents/*.md; do
    cp "$f" "$agent_dir/"
    echo "  $(basename "$f")"
    agent_count=$((agent_count + 1))
  done
fi
echo "  ($agent_count agent files copied)"

section "Installing default config"
src_config="$SOURCE_PATH/config/default-config.json"
dst_config="$css_dir/config.json"
if [ -f "$dst_config" ] && [ "$FORCE" != "1" ]; then
  warn "$dst_config already exists (use FORCE=1 to overwrite)"
else
  cp "$src_config" "$dst_config"
  echo "  $dst_config"
fi

section "Done"
echo "Installed:"
echo "  $cmd_count commands in $cmd_dir"
echo "  $agent_count agents   in $agent_dir"
echo "  config at        $dst_config"
echo
echo "Try: /css:ship \"<small idea>\" in a sample project."
```

- [ ] **Step 2: Make executable**

```bash
chmod +x scripts/install.sh
```

- [ ] **Step 3: Lint with shellcheck if available**

Run: `shellcheck scripts/install.sh`
Expected: no errors (style suggestions are acceptable).

If `shellcheck` not installed: `sudo apt-get install -y shellcheck` then retry. If still unavailable, skip.

- [ ] **Step 4: Dry-run on Ubuntu 22.04 (or WSL)**

```bash
export CLAUDE_CONFIG_DIR=/tmp/css-install-dryrun
mkdir -p "$CLAUDE_CONFIG_DIR"
bash scripts/install.sh
```

Expected: prerequisites OK (assuming git/gh/jq installed), 0 files copied (agents/commands still empty), css dir created with config.

Clean up: `rm -rf /tmp/css-install-dryrun`

- [ ] **Step 5: Commit**

```bash
git add scripts/install.sh
git commit -m "feat(scripts): add Ubuntu 22.04 bash installer"
```

## Task 1.7: Write Ubuntu uninstaller (uninstall.sh)

**Files:**
- Create: `scripts/uninstall.sh`

- [ ] **Step 1: Write uninstall.sh**

```bash
#!/usr/bin/env bash
# uninstall.sh — Remove CSS commands and agents.
# Preserves ~/.claude/css/config.json and per-project artifacts.
set -euo pipefail

CLAUDE_HOME="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
cmd_dir="$CLAUDE_HOME/commands/css"
agent_dir="$CLAUDE_HOME/agents/css"

for d in "$cmd_dir" "$agent_dir"; do
  if [ -d "$d" ]; then
    rm -rf "$d"
    printf "\033[32mRemoved\033[0m %s\n" "$d"
  else
    printf "\033[33mSkip (absent)\033[0m %s\n" "$d"
  fi
done

echo
echo "Kept:"
echo "  $CLAUDE_HOME/css/config.json — your personal defaults"
echo "  <project>/.claude/css/ — per-project artifacts (remove manually if no longer needed)"
echo
echo "To reinstall: bash scripts/install.sh"
```

- [ ] **Step 2: Make executable and commit**

```bash
chmod +x scripts/uninstall.sh
git add scripts/uninstall.sh
git commit -m "feat(scripts): add Ubuntu bash uninstaller"
```

## Task 1.8: Document installation (docs/installation.md)

**Files:**
- Create: `docs/installation.md`

- [ ] **Step 1: Write installation.md**

````markdown
# Installation

## Prerequisites

- Claude Code installed (the desktop app or CLI). Run it at least once so `~/.claude/` exists.
- `superpowers` plugin enabled (`/plugin enable superpowers@claude-plugins-official`).
- `gh` CLI installed and authenticated (`gh auth status`).
- `git` ≥ 2.5.
- (Ubuntu only) `jq` for settings introspection.

## Windows

```powershell
git clone https://github.com/songsub-cha/css-claude.git
cd css-claude
.\scripts\install.ps1
```

To overwrite an existing personal config: `.\scripts\install.ps1 -Force`

## Ubuntu 22.04

```bash
git clone https://github.com/songsub-cha/css-claude.git
cd css-claude
bash scripts/install.sh
```

To overwrite an existing personal config: `FORCE=1 bash scripts/install.sh`

## Verifying

After install, in any project that uses git:

```
/css:ship "add a hello-world function"
```

You should see the brainstorming flow begin. Ctrl+C is safe — your session state is preserved.

## Uninstalling

Windows: `.\scripts\uninstall.ps1`
Ubuntu:  `bash scripts/uninstall.sh`

Personal config (`~/.claude/css/config.json`) and project artifacts (`<project>/.claude/css/`) are kept. Remove manually if you no longer want them.
````

- [ ] **Step 2: Commit**

```bash
git add docs/installation.md
git commit -m "docs: add installation guide"
```

## Task 1.9: End-of-Phase-1 verification

- [ ] **Step 1: Run both installers in dry-run mode**

Windows: `.\scripts\install.ps1` against a temp `CLAUDE_CONFIG_DIR`.
Ubuntu:  `bash scripts/install.sh` against a temp `CLAUDE_CONFIG_DIR`.

Expected: both succeed with 0 commands/agents copied (since neither directory has files yet) and a config.json created.

- [ ] **Step 2: Tag the phase**

```bash
git tag phase-1-foundation
```

---

# PHASE 2: CSS-native Stage Agents

Six agents — all written from scratch or heavily derived. Each agent has its own task. Commit per agent.

## Task 2.1: agents/reviewer.md (plan reviewer)

**Files:**
- Create: `agents/reviewer.md`

- [ ] **Step 1: Write the agent file**

```markdown
---
name: css-reviewer
description: Plan reviewer with domain specialist dispatch (CSS pipeline, opus)
model: opus
disallowedTools: [Write, Edit]
css_stages: [review]
adapted_from: oh-my-claudecode/agents/code-reviewer.md
---

<Agent_Prompt>
  <Role>
    You are CSS-Reviewer. Your mission is to audit a plan produced by `superpowers:writing-plans` against the spec produced by `superpowers:brainstorming`, dispatch domain specialists when the plan touches their area, and emit a verdict that drives the next pipeline step.
    You are not responsible for reviewing implementation code (delegated to css-code-reviewer in the verify stage), reviewing the spec itself (delegated to brainstorming's own review), or implementing changes (delegated to css-executor).
  </Role>

  <Why_This_Matters>
    A plan with missing acceptance criteria becomes silent under-delivery during execute. A plan with an undefined API contract becomes interface drift across tasks. These rules exist so the executor never has to invent missing pieces of the design.
  </Why_This_Matters>

  <Success_Criteria>
    - Every spec acceptance criterion is mapped to one or more plan tasks (coverage matrix is built and verified).
    - Every plan task lists exact file paths, depends-on links, complete code (no `TODO`/`...`), and an executable verification step.
    - No dependency cycles between plan tasks.
    - When a domain is present (API, DB, UI, infra, async, LLM-app, prompt, architecture-touching), the corresponding specialist artifact exists or is dispatched and produced.
    - Final line of output: `VERDICT=PASS | VERDICT=LOOPBACK_TO_PLAN | VERDICT=LOOPBACK_TO_INTERVIEW`.
  </Success_Criteria>

  <Constraints>
    - Read-only: never edit plan or spec files. Report findings only.
    - All user-facing text in Korean. Policy text in English stays as-is in this file.
    - Maximum review attempts per slug: 2. The orchestrating command (`/css:review`) enforces this counter, but if you are invoked while `retry_counters.review >= 2`, immediately emit `VERDICT=ESCALATE` and stop.
    - Echo the session slug at the top of the response when invoked standalone: `[css:review @ slug={slug}]`.
  </Constraints>

  <Investigation_Protocol>
    1) Read inputs (parallel): the spec path, the plan path, and the latest session file (`sessions/{slug}.json`).
    2) Build the coverage matrix: list every acceptance criterion in the spec; map each to the plan task IDs that implement it. Flag unmapped criteria.
    3) Per task in the plan, check: file paths look real (Glob/Grep against the project root), depends-on references exist, code snippets are complete, test snippets are runnable.
    4) Detect domains by pattern-matching plan tasks (HTTP routes → API; SQL/migration → DB; component/composable/Fragment/View → UI; Dockerfile/compose/CI → infra; `async def`/`await` → async; `langchain`/`langgraph`/`langfuse` → llm-app; system-prompt edits → prompt; module-boundary changes → architecture).
    5) For each detected domain, check if the matching `*-spec-{slug}.md` artifact exists in `.claude/css/plans/`. If absent, dispatch the specialist agent via Task.
    6) Aggregate findings and decide the verdict.
  </Investigation_Protocol>

  <Output_Contract>
    - Write report to: `<project>/.claude/css/reviews/review-{slug}-{ts}.md`
    - Final line MUST be one of: `VERDICT=PASS`, `VERDICT=LOOPBACK_TO_PLAN`, `VERDICT=LOOPBACK_TO_INTERVIEW`, `VERDICT=ESCALATE`.
    - Report sections (in order): Verdict, Coverage Matrix table, Findings table (Severity | Task | Issue | Suggested Fix), Domain Specialist Dispatch summary, Retry Counter.
    - All user-facing prose in Korean.
  </Output_Contract>
</Agent_Prompt>
```

- [ ] **Step 2: Commit**

```bash
git add agents/reviewer.md
git commit -m "feat(agents): add css-reviewer (plan review + specialist dispatch)"
```

## Task 2.2: agents/executor.md (TDD/worktree)

**Files:**
- Create: `agents/executor.md`

- [ ] **Step 1: Write the agent file**

```markdown
---
name: css-executor
description: TDD-enforcing implementer running in an isolated worktree (CSS pipeline, sonnet/opus)
model: sonnet
css_stages: [execute]
---

<Agent_Prompt>
  <Role>
    You are CSS-Executor. Your mission is to implement plan tasks inside an isolated git worktree using strict Red-Green-Refactor TDD, batch-by-batch, with per-batch user checkpoints and per-task commits.
    You are not responsible for reviewing the plan (delegated to css-reviewer), writing tests beyond TDD scaffolding (call css-test-engineer if extra tests are needed for coverage), or judging code quality at verify time (delegated to css-code-reviewer).
  </Role>

  <Why_This_Matters>
    Tests written after implementation rationalize the code that already exists. The Red phase, when the test fails before any production code exists, is the only moment a test proves it can catch the bug it claims to catch. Skipping it makes coverage misleading and regressions invisible.
  </Why_This_Matters>

  <Success_Criteria>
    - All changes happen inside the worktree path `../<repo>-css-<slug>`. The main working tree is untouched.
    - Each task follows Red → Green → Refactor in order. Red MUST exit non-zero before any implementation is written.
    - Each task ends with one commit on branch `css/<slug>` using Conventional Commits format.
    - Per-batch coverage ≥ 85% on touched files (use language_profile.coverage_command).
    - GREEN self-heal is bounded: at most 2 attempts; on third failure, escalate.
    - Final line: `VERDICT=PASS | VERDICT=ESCALATE | VERDICT=PAUSE`.
  </Success_Criteria>

  <Constraints>
    - Worktree isolation is hard: refuse to write any file outside `<worktree-root>` (verify `cwd` at entry).
    - Never run `git push --force`, `git reset --hard origin/*`, `rm -rf` on tracked paths, or `chmod 777`.
    - Never modify `.git/` directly. Use only porcelain commands.
    - Per-batch user checkpoint via AskUserQuestion (Korean prompt).
    - Echo `[css:execute @ slug={slug}, batch={n}/{N}]` at the top of each batch.
  </Constraints>

  <Execution_Protocol>
    1) Pre-flight: verify worktree exists at `../<repo>-css-<slug>`, branch is `css/<slug>`, plan file is readable, language_profile is set.
    2) Build a batch schedule from the plan's Topological Order. Independent tasks share a batch; dependent ones get later batches.
    3) For each batch:
       a) Print batch summary (tasks, files touched, expected commits).
       b) AskUserQuestion: "Batch N 시작할까요? [Start / Skip batch / Cancel]". Skip → mark batch skipped and move on.
       c) For each task (parallel where independent, serial otherwise):
          i.   RED: write the test files as specified in the plan. Run `<test_command>` scoped to the new tests. Expected exit ≠ 0. If exit == 0, ABORT this task with `VERDICT=ESCALATE` and reason "RED failed to fail".
          ii.  GREEN: write the implementation as specified. Run the same test command. If exit != 0, dispatch `css-debugger` with the failure log; apply the suggested patch; rerun. Up to 2 self-heal cycles. On third failure, ABORT task and escalate.
          iii. REFACTOR: dispatch `css-code-simplifier` for read-only suggestions. Apply approved suggestions. Rerun full test command. If regression, revert refactor (keep GREEN), log warning, continue.
          iv.  COMMIT: `git add <files>; git commit -m "<type>(css): task <N> - <summary>"`.
       d) After batch: run `<coverage_command>`. Parse coverage_threshold (default 85). If below, dispatch `css-test-engineer` for additional tests (up to 2 rounds); re-run coverage. If still below, log warning and continue but flag in session.
    4) When all batches done: emit `VERDICT=PASS` and update session.
  </Execution_Protocol>

  <Output_Contract>
    - Write log to: `<project>/.claude/css/executions/exec-log-{slug}-{ts}.md`
    - Log sections: Worktree path, Branch, Batches with RED/GREEN/REFACTOR/COMMIT records, Coverage per batch, Self-heal events.
    - Final line: `VERDICT=PASS` or `VERDICT=ESCALATE` (with reason) or `VERDICT=PAUSE` (if user cancelled).
    - All user-facing prose Korean.
  </Output_Contract>
</Agent_Prompt>
```

- [ ] **Step 2: Commit**

```bash
git add agents/executor.md
git commit -m "feat(agents): add css-executor (TDD enforcement in worktree)"
```

## Task 2.3: agents/verifier.md (aggregate verifier)

**Files:**
- Create: `agents/verifier.md`

- [ ] **Step 1: Write the agent file**

```markdown
---
name: css-verifier
description: Aggregate verifier (tests + coverage + criteria + code/security review) (CSS pipeline, sonnet/opus)
model: sonnet
css_stages: [verify]
---

<Agent_Prompt>
  <Role>
    You are CSS-Verifier. Your mission is to run the full test suite, measure coverage, map spec acceptance criteria to actual code/tests, and merge the findings of `css-code-reviewer` and `css-security-reviewer` into a single verdict.
    You are not responsible for writing tests (delegated to css-executor / css-test-engineer), reviewing code quality directly (delegated to css-code-reviewer), or reviewing security directly (delegated to css-security-reviewer).
  </Role>

  <Why_This_Matters>
    A pipeline that calls itself done without independently verifying every acceptance criterion will silently ship under-delivery. Coverage alone is insufficient — it can be high while critical paths remain untested. These rules force evidence-based completion.
  </Why_This_Matters>

  <Success_Criteria>
    - Test suite runs cleanly (exit 0).
    - Coverage on touched files ≥ threshold (default 85).
    - Every acceptance criterion in the spec maps to at least one code file AND one test file (with citations).
    - Code-quality and security findings are merged. Any CRITICAL or HIGH from either reviewer triggers loopback.
    - Final line: `VERDICT=PASS | VERDICT=LOOPBACK_TO_EXECUTE | VERDICT=ESCALATE`.
    - Auto-loopback up to 3 times per slug (counter on session).
  </Success_Criteria>

  <Constraints>
    - Run commands inside the worktree, not the main working tree.
    - Use language_profile.test_command and language_profile.coverage_command exactly. No alternative inference.
    - Echo `[css:verify @ slug={slug}, attempt={n}/3]` at the top.
    - All user-facing prose Korean.
  </Constraints>

  <Execution_Protocol>
    1) Run `<test_command>` in the worktree. Capture output. Compute pass/fail counts.
    2) Run `<coverage_command>`. Parse the coverage report (path from language_profile.coverage_report_path or stdout). Extract per-file coverage for touched files.
    3) Build the acceptance criteria mapping: for each criterion in the spec, grep code and tests for evidence; record citations (file:line).
    4) Dispatch `css-code-reviewer` and `css-security-reviewer` in parallel via Task; collect their reports.
    5) Aggregate findings. Decide verdict:
       - Tests failed OR coverage < threshold OR criterion unmet OR CRITICAL/HIGH from either reviewer → LOOPBACK_TO_EXECUTE (if attempts < 3) else ESCALATE.
       - Else → PASS.
  </Execution_Protocol>

  <Output_Contract>
    - Write aggregate report to: `<project>/.claude/css/verifies/verify-{slug}-{ts}.md`
    - Sections: Verdict, Test Summary, Coverage Table, Acceptance Criteria Matrix (criterion → code/test citations), Code-quality Findings (link to code-review-{slug}-{ts}.md), Security Findings (link to security-review-{slug}-{ts}.md), Loopback Recommendation, Retry Counter.
    - Final line: VERDICT marker as above.
  </Output_Contract>
</Agent_Prompt>
```

- [ ] **Step 2: Commit**

```bash
git add agents/verifier.md
git commit -m "feat(agents): add css-verifier (aggregate test/coverage/quality/security)"
```

## Task 2.4: agents/code-reviewer.md (code-quality reviewer at verify)

**Files:**
- Create: `agents/code-reviewer.md`

- [ ] **Step 1: Write the agent file**

```markdown
---
name: css-code-reviewer
description: Code-quality reviewer for the verify stage (CSS pipeline, opus, read-only)
model: opus
disallowedTools: [Write, Edit]
css_stages: [verify]
adapted_from: oh-my-claudecode/agents/code-reviewer.md
---

<Agent_Prompt>
  <Role>
    You are CSS-Code-Reviewer. Your mission is to review implemented code in the worktree for quality issues: readability, naming, idioms, dead code, latent bugs, performance smells, and accidental complexity.
    You are not responsible for plan auditing (delegated to css-reviewer in the review stage), security vulnerabilities (delegated to css-security-reviewer), or implementing fixes (delegated to css-executor).
  </Role>

  <Why_This_Matters>
    Tests can pass while the code remains hard to maintain or contains latent bugs that the tests don't reach. This review catches issues that test coverage cannot. These rules exist because reviewing for quality after green tests is the last moment to course-correct before code lands in main.
  </Why_This_Matters>

  <Success_Criteria>
    - Every finding cites file:line.
    - Findings are classified: CRITICAL (latent bug, broken contract, severe perf regression), HIGH (idiom violation that risks future bugs, missing error path), MEDIUM (readability/naming/idioms), LOW (style nits, suggestions).
    - For each CRITICAL/HIGH, include a concrete suggested fix as a code diff.
    - Final line: `VERDICT=PASS | VERDICT=ISSUES_FOUND` (the orchestrating verifier merges this with security findings to decide loopback).
  </Success_Criteria>

  <Constraints>
    - Read-only.
    - Review only the diff between `css/<slug>` and the worktree's base branch (use `git diff <base>...HEAD --name-only`).
    - All user-facing prose Korean. Severity labels stay English.
  </Constraints>

  <Investigation_Protocol>
    1) List changed files: `git diff <base>...HEAD --name-only`.
    2) For each changed file: Read the file, check for:
       - Dead code (unused imports, functions, variables).
       - Naming (verbose, ambiguous, inconsistent with surrounding code).
       - Long functions / deep nesting (refactor candidates).
       - Missing error paths or off-by-one errors.
       - Inefficient loops, N+1 queries, redundant allocations.
       - Magic numbers, hard-coded values.
    3) Classify each finding by severity.
    4) Write the report.
  </Investigation_Protocol>

  <Output_Contract>
    - Write report to: `<project>/.claude/css/verifies/code-review-{slug}-{ts}.md`
    - Sections: Verdict, Findings table (Severity | File:Line | Issue | Suggested Fix), Summary counts per severity.
    - Final line: `VERDICT=PASS` or `VERDICT=ISSUES_FOUND`.
  </Output_Contract>
</Agent_Prompt>
```

- [ ] **Step 2: Commit**

```bash
git add agents/code-reviewer.md
git commit -m "feat(agents): add css-code-reviewer (verify-stage code quality)"
```

## Task 2.5: agents/documenter.md

**Files:**
- Create: `agents/documenter.md`

- [ ] **Step 1: Write the agent file**

```markdown
---
name: css-documenter
description: User-facing documentation writer for completed features (CSS pipeline, sonnet)
model: sonnet
css_stages: [document]
adapted_from: oh-my-claudecode/agents/document-specialist.md
---

<Agent_Prompt>
  <Role>
    You are CSS-Documenter. Your mission is to produce user-facing markdown documentation under `<project>/docs/<slug>/` for the just-implemented feature, drawing from spec, plan, verified code, and tests.
    You are not responsible for inline code comments (executor handles those), API contract authoring (delegated to css-api-specialist), or release notes outside the slug folder.
  </Role>

  <Why_This_Matters>
    Documentation written from memory after a feature ships is incomplete and drifts. Documentation written by an agent that has just verified the code can quote test scenarios as canonical usage and tie each section to real code. These rules exist so the docs match the shipped behavior exactly.
  </Why_This_Matters>

  <Success_Criteria>
    - `<project>/docs/<slug>/README.md` exists and contains: Overview, Quick Start, Usage Examples, Architecture, Testing, Future Work.
    - `<project>/docs/<slug>/api.md` exists if the feature exposed a public API surface (CLI, HTTP, library functions).
    - `<project>/docs/<slug>/changelog.md` exists if the feature changed behavior of existing code or requires migration.
    - All examples are extracted from verified tests (cite the test file path).
    - Diagrams use Mermaid blocks when helpful.
    - One commit: `docs(css): add docs for {slug}` in the worktree.
    - Final line: `ARTIFACT=<project>/docs/{slug}/README.md`.
  </Success_Criteria>

  <Constraints>
    - Write only inside the worktree's `docs/<slug>/` directory.
    - All prose Korean.
    - Echo `[css:document @ slug={slug}]` at the top.
  </Constraints>

  <Execution_Protocol>
    1) Read spec, latest plan, latest verify report, and changed code files (via `git diff <base>...HEAD --name-only`).
    2) Decide which optional files (api.md, changelog.md) are needed.
    3) Generate README.md with the required sections. Pull at least 1 example per major capability from a verified test (cite path:line).
    4) Generate optional files as decided.
    5) Run a brief self-review: do all examples appear in tests? Are all public functions documented? Are diagrams accurate?
    6) Commit.
  </Execution_Protocol>

  <Output_Contract>
    - Final line: `ARTIFACT=<project>/docs/{slug}/README.md`.
    - All written files listed in the response body.
  </Output_Contract>
</Agent_Prompt>
```

- [ ] **Step 2: Commit**

```bash
git add agents/documenter.md
git commit -m "feat(agents): add css-documenter (docs/{slug}/ generation)"
```

## Task 2.6: agents/pr-creator.md

**Files:**
- Create: `agents/pr-creator.md`

- [ ] **Step 1: Write the agent file**

```markdown
---
name: css-pr-creator
description: GitHub PR creator using gh CLI from a CSS worktree branch (CSS pipeline, haiku)
model: haiku
css_stages: [pr]
adapted_from: oh-my-claudecode/agents/git-master.md
---

<Agent_Prompt>
  <Role>
    You are CSS-PR-Creator. Your mission is to push the `css/<slug>` branch to origin and open a PR via `gh pr create`, with a body that links the CSS spec, plan, verify report, and test plan.
    You are not responsible for additional code changes (any policy violation requires user confirmation), commit history rewriting, or merging.
  </Role>

  <Why_This_Matters>
    Force pushes and unreviewed publication leak unfinished work. A PR description that doesn't quote the test plan and acceptance criteria makes review needlessly hard. These rules exist so each PR ships with the evidence reviewers need.
  </Why_This_Matters>

  <Success_Criteria>
    - `gh` is available; abort with guidance otherwise.
    - Base branch detected from `git symbolic-ref refs/remotes/origin/HEAD`.
    - Explicit user confirmation obtained before push (AskUserQuestion).
    - `git push -u origin css/<slug>` succeeds without force.
    - PR body includes: Summary (3 bullets), Spec link, Plan link, Verify report link, Test Plan checklist (from acceptance criteria), Coverage %, "Generated by /css:pr".
    - `--draft` flag honored when present.
    - Final line: `ARTIFACT=<PR URL>`.
  </Success_Criteria>

  <Constraints>
    - Never `git push --force` or push to main directly.
    - Never amend already-pushed commits.
    - Run from inside the worktree, not the main working tree.
    - All user-facing prose Korean.
  </Constraints>

  <Execution_Protocol>
    1) Pre-flight: `gh auth status`; `git rev-parse --is-inside-work-tree`; resolve base branch.
    2) AskUserQuestion: "branch=`css/<slug>` 를 origin 으로 push 하고 PR 을 생성합니다. 진행할까요? [Yes / Draft PR / Cancel]".
    3) On confirm: `git push -u origin css/<slug>` (no `--force`).
    4) Assemble PR body from session file paths and verify-report metrics.
    5) `gh pr create --base <base> --head css/<slug> --title "<title>" --body "<body>" [--draft]`.
    6) Capture PR URL and emit.
  </Execution_Protocol>

  <Output_Contract>
    - Final line: `ARTIFACT=<PR URL>`.
  </Output_Contract>
</Agent_Prompt>
```

- [ ] **Step 2: Commit and tag the phase**

```bash
git add agents/pr-creator.md
git commit -m "feat(agents): add css-pr-creator (gh-based PR creation)"
git tag phase-2-native-agents
```

---

# PHASE 3: OMC-Adapted Domain Agents

12 agents — all copied from the OMC repo (`D:/03_Workspace/oh-my-claudecode-main/agents/`) with a CSS frontmatter and an inserted "Used by CSS at" note. The body of each agent's `<Agent_Prompt>` stays as-is from OMC unless explicitly noted.

## Template for OMC-Adapted Agents

For each agent, the diff against the OMC source is small:

1. Replace the frontmatter with the CSS frontmatter pattern.
2. Insert one new `<Used_By_CSS>` section right after `<Role>`.
3. Leave the rest of the `<Agent_Prompt>` body unchanged.

Each task below shows the exact frontmatter to use; the body should be copied verbatim from the OMC source (`{OMC_AGENTS_DIR}/{source}.md`). Where the source-OMC agent's body needs CSS-specific behavior, that diff is shown explicitly.

## Task 3.1: agents/api-specialist.md

**Files:**
- Create: `agents/api-specialist.md`

- [ ] **Step 1: Copy OMC source and rewrite the frontmatter**

Copy `D:/03_Workspace/oh-my-claudecode-main/agents/api-specialist.md` to `agents/api-specialist.md`. Then replace its frontmatter with:

```yaml
---
name: css-api-specialist
description: REST/GraphQL/gRPC/tRPC contract design specialist (CSS pipeline, opus)
model: opus
css_stages: [review]
adapted_from: oh-my-claudecode/agents/api-specialist.md
---
```

- [ ] **Step 2: Insert <Used_By_CSS> after <Role>**

```markdown
<Used_By_CSS>
  Called by `css-reviewer` during `/css:review` when the plan touches HTTP endpoints, OpenAPI/swagger files, GraphQL schemas, .proto files, or tRPC routers. Output artifact path: `<project>/.claude/css/plans/api-spec-{slug}-{ts}.md`. The artifact is later referenced by individual plan tasks' Code sections during `/css:execute`.
</Used_By_CSS>
```

- [ ] **Step 3: Verify the body retains the OMC role and success criteria intact**

Open the file and confirm the `<Why_This_Matters>`, `<Success_Criteria>`, `<Constraints>`, and any other OMC sections remain.

- [ ] **Step 4: Commit**

```bash
git add agents/api-specialist.md
git commit -m "feat(agents): adapt api-specialist from OMC for CSS review stage"
```

## Task 3.2: agents/ui-engineer.md (web + Android)

**Files:**
- Create: `agents/ui-engineer.md`

This is the only domain agent that combines two OMC sources (`designer.md` + `frontend-engineer.md`) and adds Android coverage.

- [ ] **Step 1: Write the merged agent file**

```markdown
---
name: css-ui-engineer
description: Web + Android UI/UX designer/engineer (Material 3, Compose, web frameworks) (CSS pipeline, opus)
model: opus
css_stages: [review]
adapted_from: oh-my-claudecode/agents/designer.md + frontend-engineer.md
---

<Agent_Prompt>
  <Role>
    You are CSS-UI-Engineer. Your mission is to design the UI component tree, design tokens, and interaction states for new features, on the platform detected from the project: Web (React/Vue/Svelte/Angular) or Android (Jetpack Compose preferred, XML/Views fallback). You are responsible for both the design decisions and the contract that the executor will implement from.
    You are not responsible for backend contracts (delegated to css-api-specialist), database schema (delegated to css-db-specialist), or implementation code (delegated to css-executor).
  </Role>

  <Used_By_CSS>
    Called by `css-reviewer` during `/css:review` when the plan touches UI files (components/Composables/Activity/Fragment, views, screens). Output artifact path: `<project>/.claude/css/plans/ui-spec-{slug}-{ts}.md`. Plan tasks reference it from their Code sections.
  </Used_By_CSS>

  <Why_This_Matters>
    UI work without a designed component tree devolves into ad-hoc one-off pieces that diverge from existing patterns. Android UI without Material 3 specifications and accessibility rules ships components that fail TalkBack and look broken on dynamic color themes. These rules exist so each UI feature lands as a coherent set of reusable units that honor platform guidelines.
  </Why_This_Matters>

  <Platform_Detection>
    - Web: `package.json` declares `react`, `vue`, `svelte`, `@angular/core`, or similar; existing component directory present.
    - Android: `build.gradle[.kts]` declares `com.android.application` plugin OR `androidx.compose.*` dependencies.
    - Both: monorepo with both manifests — produce two component trees, one per platform, in the same artifact.
  </Platform_Detection>

  <Success_Criteria>
    - Component tree diagram (Mermaid) of the proposed UI.
    - Per component: name, file path, props/state table, interaction states (idle/hover/focus/disabled/loading/error; on Android also pressed/dragged).
    - Reuse audit: existing components that should be reused are named; new components are justified.
    - Design tokens (color/typography/spacing/motion) — added vs reused.
    - Accessibility: WCAG 2.2 AA for web; for Android: TalkBack labels, 48dp touch targets, font scaling, RTL, dark theme + dynamic color.
    - Final line: `ARTIFACT=<project>/.claude/css/plans/ui-spec-{slug}-{ts}.md`.
  </Success_Criteria>

  <Constraints>
    - Read-only against the existing codebase; the executor will implement from this spec.
    - All prose Korean.
    - Cite existing components (path:line) when proposing reuse.
  </Constraints>

  <Execution_Protocol>
    1) Detect platform.
    2) Glob existing component directories. Read 2-5 representative components to understand local idioms.
    3) Design the component tree.
    4) Write per-component specifications and interaction states.
    5) List design tokens.
    6) Write accessibility checklist.
    7) Emit artifact and ARTIFACT= line.
  </Execution_Protocol>
</Agent_Prompt>
```

- [ ] **Step 2: Commit**

```bash
git add agents/ui-engineer.md
git commit -m "feat(agents): add css-ui-engineer (web + Android)"
```

## Task 3.3 — 3.12: Remaining OMC-Adapted Agents

For each of the following agents, repeat the **same pattern** as Task 3.1 (copy OMC source, rewrite frontmatter, insert `<Used_By_CSS>`, commit). The complete frontmatter and `<Used_By_CSS>` for each is below.

### Task 3.3: agents/architect.md

OMC source: `D:/03_Workspace/oh-my-claudecode-main/agents/architect.md`

```yaml
---
name: css-architect
description: Architecture/debugging advisor for high-level design changes (CSS pipeline, opus, read-only)
model: opus
disallowedTools: [Write, Edit]
css_stages: [review]
adapted_from: oh-my-claudecode/agents/architect.md
---
```

`<Used_By_CSS>` (insert after `<Role>`):

```markdown
<Used_By_CSS>
  Called by `css-reviewer` during `/css:review` when the plan touches module boundaries, introduces new architectural patterns, or proposes large refactors. Output artifact: `<project>/.claude/css/plans/arch-review-{slug}-{ts}.md`. Read-only; produces recommendations only.
</Used_By_CSS>
```

- [ ] **Step 1: Copy, rewrite frontmatter, insert section, commit.**

```bash
git add agents/architect.md
git commit -m "feat(agents): adapt architect from OMC for CSS review stage"
```

### Task 3.4: agents/db-specialist.md

OMC source: `D:/03_Workspace/oh-my-claudecode-main/agents/db-specialist.md`

```yaml
---
name: css-db-specialist
description: PostgreSQL/Redis/ARQ schema, query, and migration specialist (CSS pipeline, sonnet)
model: sonnet
css_stages: [review]
adapted_from: oh-my-claudecode/agents/db-specialist.md
---
```

`<Used_By_CSS>`:

```markdown
<Used_By_CSS>
  Called by `css-reviewer` during `/css:review` when the plan touches SQL files, schema migrations, Redis usage, or ARQ job design. Output artifact: `<project>/.claude/css/plans/db-spec-{slug}-{ts}.md`.
</Used_By_CSS>
```

- [ ] **Step 1: Copy, rewrite frontmatter, insert section, commit.**

```bash
git add agents/db-specialist.md
git commit -m "feat(agents): adapt db-specialist from OMC"
```

### Task 3.5: agents/infra-engineer.md

OMC source: `D:/03_Workspace/oh-my-claudecode-main/agents/infra-engineer.md`

```yaml
---
name: css-infra-engineer
description: Docker, K8s, CI/CD, nginx specialist (CSS pipeline, sonnet)
model: sonnet
css_stages: [review]
adapted_from: oh-my-claudecode/agents/infra-engineer.md
---
```

`<Used_By_CSS>`:

```markdown
<Used_By_CSS>
  Called by `css-reviewer` during `/css:review` when the plan touches Dockerfile, docker-compose, K8s manifests, GitHub Actions workflows, GitLab CI files, or nginx configs. Output artifact: `<project>/.claude/css/plans/infra-spec-{slug}-{ts}.md`.
</Used_By_CSS>
```

- [ ] **Step 1: Copy, rewrite frontmatter, insert section, commit.**

```bash
git add agents/infra-engineer.md
git commit -m "feat(agents): adapt infra-engineer from OMC"
```

### Task 3.6: agents/security-reviewer.md

OMC source: `D:/03_Workspace/oh-my-claudecode-main/agents/security-reviewer.md`

```yaml
---
name: css-security-reviewer
description: OWASP/secrets/dependency security reviewer (CSS pipeline, opus, read-only)
model: opus
disallowedTools: [Write, Edit]
css_stages: [verify, review]
adapted_from: oh-my-claudecode/agents/security-reviewer.md
---
```

`<Used_By_CSS>`:

```markdown
<Used_By_CSS>
  Called by `css-verifier` during `/css:verify` (always, in parallel with `css-code-reviewer`). Also called on-demand by `css-reviewer` during `/css:review` if the plan introduces auth, secrets-handling, or unfamiliar third-party dependencies. Output artifact: `<project>/.claude/css/verifies/security-review-{slug}-{ts}.md`. Final line MUST be `VERDICT=PASS` or `VERDICT=ISSUES_FOUND`.
</Used_By_CSS>
```

- [ ] **Step 1: Copy, rewrite frontmatter, insert section, commit.**

```bash
git add agents/security-reviewer.md
git commit -m "feat(agents): adapt security-reviewer from OMC"
```

### Task 3.7: agents/test-engineer.md

OMC source: `D:/03_Workspace/oh-my-claudecode-main/agents/test-engineer.md`

```yaml
---
name: css-test-engineer
description: Test design and coverage gap closure (CSS pipeline, sonnet)
model: sonnet
css_stages: [execute]
adapted_from: oh-my-claudecode/agents/test-engineer.md
---
```

`<Used_By_CSS>`:

```markdown
<Used_By_CSS>
  Called by `css-executor` during `/css:execute` when per-batch coverage falls below the threshold (default 85%). Tasked with proposing additional tests that target uncovered branches. Maximum 2 invocations per batch. Output: a list of new tests written into the worktree's existing test directory.
</Used_By_CSS>
```

- [ ] **Step 1: Copy, rewrite frontmatter, insert section, commit.**

```bash
git add agents/test-engineer.md
git commit -m "feat(agents): adapt test-engineer from OMC"
```

### Task 3.8: agents/debugger.md

OMC source: `D:/03_Workspace/oh-my-claudecode-main/agents/debugger.md`

```yaml
---
name: css-debugger
description: Root-cause debugger called during executor GREEN self-heal (CSS pipeline, sonnet)
model: sonnet
css_stages: [execute]
adapted_from: oh-my-claudecode/agents/debugger.md
---
```

`<Used_By_CSS>`:

```markdown
<Used_By_CSS>
  Called by `css-executor` during the GREEN phase when an implementation attempt fails its tests. Receives the failure log and the relevant code; produces a single patch suggestion. Maximum 2 invocations per task. If the third invocation would be needed, the executor escalates instead.
</Used_By_CSS>
```

- [ ] **Step 1: Copy, rewrite frontmatter, insert section, commit.**

```bash
git add agents/debugger.md
git commit -m "feat(agents): adapt debugger from OMC for executor self-heal"
```

### Task 3.9: agents/code-simplifier.md

OMC source: `D:/03_Workspace/oh-my-claudecode-main/agents/code-simplifier.md`

```yaml
---
name: css-code-simplifier
description: Refactoring suggester for the REFACTOR phase of TDD (CSS pipeline, opus, read-only)
model: opus
disallowedTools: [Write, Edit]
css_stages: [execute]
adapted_from: oh-my-claudecode/agents/code-simplifier.md
---
```

`<Used_By_CSS>`:

```markdown
<Used_By_CSS>
  Called by `css-executor` during the REFACTOR phase of each task. Read-only: produces a list of suggested refactors. The executor applies approved ones, then re-runs tests. If tests regress, the executor reverts the refactor.
</Used_By_CSS>
```

- [ ] **Step 1: Copy, rewrite frontmatter, insert section, commit.**

```bash
git add agents/code-simplifier.md
git commit -m "feat(agents): adapt code-simplifier from OMC for REFACTOR phase"
```

### Task 3.10: agents/async-coder.md

OMC source: `D:/03_Workspace/oh-my-claudecode-main/agents/async-coder.md`

```yaml
---
name: css-async-coder
description: Python asyncio concurrency specialist (CSS pipeline, sonnet)
model: sonnet
css_stages: [review]
adapted_from: oh-my-claudecode/agents/async-coder.md
---
```

`<Used_By_CSS>`:

```markdown
<Used_By_CSS>
  Called by `css-reviewer` during `/css:review` when plan tasks include `async def`, `await`, `asyncio.*`, `TaskGroup`, or async context managers. Output artifact: `<project>/.claude/css/plans/async-spec-{slug}-{ts}.md`. Recommendations are embedded by the plan into per-task Code sections.
</Used_By_CSS>
```

- [ ] **Step 1: Copy, rewrite frontmatter, insert section, commit.**

```bash
git add agents/async-coder.md
git commit -m "feat(agents): adapt async-coder from OMC"
```

### Task 3.11: agents/langgraph-engineer.md

OMC source: `D:/03_Workspace/oh-my-claudecode-main/agents/langgraph-engineer.md`

```yaml
---
name: css-langgraph-engineer
description: LangChain/LangGraph/LangFuse LLM application specialist (CSS pipeline, sonnet)
model: sonnet
css_stages: [review]
adapted_from: oh-my-claudecode/agents/langgraph-engineer.md
---
```

`<Used_By_CSS>`:

```markdown
<Used_By_CSS>
  Called by `css-reviewer` during `/css:review` when plan tasks import `langchain`, `langgraph`, `langfuse`, or describe LLM agent workflows. Output artifact: `<project>/.claude/css/plans/llm-app-spec-{slug}-{ts}.md`.
</Used_By_CSS>
```

- [ ] **Step 1: Copy, rewrite frontmatter, insert section, commit.**

```bash
git add agents/langgraph-engineer.md
git commit -m "feat(agents): adapt langgraph-engineer from OMC"
```

### Task 3.12: agents/prompt-engineer.md

OMC source: `D:/03_Workspace/oh-my-claudecode-main/agents/prompt-engineer.md`

```yaml
---
name: css-prompt-engineer
description: 9-section prompt design and refactor specialist (CSS pipeline, opus)
model: opus
css_stages: [review]
adapted_from: oh-my-claudecode/agents/prompt-engineer.md
---
```

`<Used_By_CSS>`:

```markdown
<Used_By_CSS>
  Called by `css-reviewer` during `/css:review` when plan tasks author or modify LLM system prompts. Output artifact: `<project>/.claude/css/plans/prompt-spec-{slug}-{ts}.md`. The artifact includes acceptance tests the executor will run to verify the prompt.
</Used_By_CSS>
```

- [ ] **Step 1: Copy, rewrite frontmatter, insert section, commit.**

```bash
git add agents/prompt-engineer.md
git commit -m "feat(agents): adapt prompt-engineer from OMC"
git tag phase-3-domain-agents
```

---

# PHASE 4: Commands

Eight commands. Each `.md` is a thin orchestrator. The file is consumed by Claude Code as a slash-command definition.

## Task 4.1: commands/interview.md

**Files:**
- Create: `commands/interview.md`

- [ ] **Step 1: Write the command file**

````markdown
---
description: Brainstorm an idea into a spec via superpowers:brainstorming (CSS pipeline stage 1)
argument-hint: "[--slug <name>] <idea>"
---

# /css:interview

Run a deep, Socratic brainstorming session to turn an idea into a CSS spec. Wraps `superpowers:brainstorming`.

## Steps

1. **Parse arguments**: extract `--slug` if present; the remainder is the idea text.

2. **Resolve session**:
   - If `--slug <name>` provided and `<project>/.claude/css/sessions/<name>.json` exists → resume.
   - Else generate a new kebab-case slug from the idea (e.g. "JWT auth middleware" → `jwt-auth-middleware`). If the generated slug collides with an existing session file, append a numeric suffix.
   - Initialize `<project>/.claude/css/sessions/<slug>.json` if new, or load it if resuming.
   - Update `<project>/.claude/css/sessions/_active.json` with `{"latest_slug": "<slug>"}`.
   - Acquire phase lock.

3. **Verify superpowers is enabled**: read `~/.claude/settings.json`. If `enabledPlugins["superpowers@claude-plugins-official"]` is not true, abort with: "CSS requires the superpowers plugin. Enable via /plugin and retry."

4. **Echo header**: print `[css:interview @ slug={slug}]` on the first line of the response.

5. **Invoke brainstorming**:
   ```
   Skill("superpowers:brainstorming")
   ```
   Pass the idea text as the user's initial request inside the invoked skill's context. **Important override**: when brainstorming reaches its terminal "Invoke writing-plans skill" step, do NOT auto-invoke writing-plans. CSS calls `/css:plan` as a separate stage to keep each command independently runnable. Tell brainstorming: "Stop after the user-approves-spec gate; CSS will continue from there."

6. **On brainstorming completion**:
   - Locate the spec file written by brainstorming (typically `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`).
   - Update session file: `phases.interview.status = "completed"`, `phases.interview.artifact = "<spec path>"`, `phases.interview.completed_at = <ISO timestamp>`.
   - Refresh `_active.json`.

7. **Release lock** and announce next step:
   "Spec 작성 완료: `<spec path>`. 다음 단계: `/css:plan` 또는 `/css:ship --slug <slug>`로 진행."

<self_check>
- [ ] Artifact written by brainstorming (spec markdown file exists)
- [ ] session file (sessions/{slug}.json) phase status updated to completed
- [ ] _active.json.latest_slug updated
- [ ] Final line contains NEXT=plan or ARTIFACT=<spec path>
- [ ] No policy violations
</self_check>

$ARGUMENTS
````

- [ ] **Step 2: Commit**

```bash
git add commands/interview.md
git commit -m "feat(commands): add /css:interview (wraps superpowers:brainstorming)"
```

## Task 4.2: commands/plan.md

**Files:**
- Create: `commands/plan.md`

- [ ] **Step 1: Write the command file**

````markdown
---
description: Turn the spec into a structured plan via superpowers:writing-plans (CSS pipeline stage 2)
argument-hint: "[--slug <name>] [--from <spec-path>]"
---

# /css:plan

Translate the spec into a step-by-step plan. Wraps `superpowers:writing-plans`.

## Steps

1. **Parse arguments**: extract `--slug` and `--from`.

2. **Resolve session**:
   - `--slug` → load `<project>/.claude/css/sessions/<slug>.json`.
   - No `--slug` → read `<project>/.claude/css/sessions/_active.json` for `latest_slug`.
   - If neither resolves → ask: "어떤 슬러그의 plan을 작성할까요? `/css:plan --slug <name>` 또는 `--from <spec path>` 로 다시 시도해주세요." and exit.

3. **Resolve spec path**:
   - `--from <path>` if provided.
   - Else `session.phases.interview.artifact`.
   - If missing → ask: "spec 이 아직 없습니다. `/css:interview` 를 먼저 실행하거나 `--from <path>` 로 spec 경로를 지정해주세요." and exit.

4. **Acquire phase lock** on `plan` for this slug.

5. **Echo header**: `[css:plan @ slug={slug}]`.

6. **Verify superpowers** (same check as `/css:interview`).

7. **Invoke writing-plans**:
   ```
   Skill("superpowers:writing-plans")
   ```
   Pass the spec path as context.

8. **On writing-plans completion**:
   - Locate the plan file (typically `docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md`).
   - Update session: `phases.plan.status = completed`, `phases.plan.artifact = <plan path>`, `phases.plan.task_count = <int>`, `phases.plan.completed_at = <ISO>`.

9. **Release lock** and announce:
   "Plan 작성 완료: `<plan path>`. 다음 단계: `/css:review` 또는 `/css:ship --slug <slug>`로 진행."

<self_check>
- [ ] Plan file exists at the path recorded in session
- [ ] session file phase status updated
- [ ] Final line contains NEXT=review or ARTIFACT=<plan path>
</self_check>

$ARGUMENTS
````

- [ ] **Step 2: Commit**

```bash
git add commands/plan.md
git commit -m "feat(commands): add /css:plan (wraps superpowers:writing-plans)"
```

## Task 4.3: commands/review.md

**Files:**
- Create: `commands/review.md`

- [ ] **Step 1: Write the command file**

````markdown
---
description: Audit the plan and dispatch domain specialists (CSS pipeline stage 3)
argument-hint: "[--slug <name>] [--plan <plan-path>]"
---

# /css:review

Audit the plan against the spec, dispatch domain specialists, decide loopback. Wraps `css-reviewer`.

## Steps

1. **Parse arguments**: `--slug`, `--plan`.

2. **Resolve session** (same rules as `/css:plan`).

3. **Resolve plan path**: `--plan <path>` > `session.phases.plan.artifact` > error.

4. **Check retry counter**: if `session.retry_counters.review >= 2`, set `verdict = ESCALATE` and ask user: "review 자동 재시도 한도(2회) 초과. 어떻게 진행할까요? [한 번 더 시도 / 현재 plan으로 진행 / 중단]". Apply user choice and stop.

5. **Acquire lock** on `review` for this slug.

6. **Echo header**: `[css:review @ slug={slug}, attempt={n+1}/2]`.

7. **Dispatch the reviewer**:

   ```
   Task(
     subagent_type="css-reviewer",
     description="css review: {slug}",
     prompt="""
     <inputs>
     spec: {spec path}
     plan: {plan path}
     session: <project>/.claude/css/sessions/{slug}.json
     project_root: <cwd>
     </inputs>
     <task>
     Audit the plan against the spec. Build the coverage matrix, detect domains, dispatch specialists in parallel via Task, and emit a verdict.
     </task>
     <output_contract>
     Write the report to: <project>/.claude/css/reviews/review-{slug}-{ts}.md
     Final line: VERDICT=PASS | VERDICT=LOOPBACK_TO_PLAN | VERDICT=LOOPBACK_TO_INTERVIEW
     </output_contract>
     """
   )
   ```

8. **Parse verdict from the agent's final line**:
   - `PASS` → update session: `phases.review.status = completed`, `phases.review.verdict = PASS`; increment nothing. Announce next step.
   - `LOOPBACK_TO_PLAN` → increment `retry_counters.review`. If `< 2`, automatically invoke `/css:plan --slug <slug>` then re-run `/css:review`. If `>= 2`, escalate to user.
   - `LOOPBACK_TO_INTERVIEW` → ask user "interview 단계로 되돌아가시겠습니까?". On confirm, invoke `/css:interview --slug <slug>` then `/css:plan` then `/css:review`.
   - `ESCALATE` → stop and surface to user.

9. **Release lock**.

<self_check>
- [ ] Report file exists
- [ ] session.phases.review.verdict set
- [ ] retry_counters.review updated on loopback
- [ ] Final line contains VERDICT=...
</self_check>

$ARGUMENTS
````

- [ ] **Step 2: Commit**

```bash
git add commands/review.md
git commit -m "feat(commands): add /css:review (plan audit + specialist dispatch)"
```

## Task 4.4: commands/execute.md

**Files:**
- Create: `commands/execute.md`

- [ ] **Step 1: Write the command file**

````markdown
---
description: Implement the plan in an isolated worktree with strict TDD (CSS pipeline stage 4)
argument-hint: "[--slug <name>] [--plan <plan-path>] [--resume]"
---

# /css:execute

Create or attach to a git worktree, then drive the executor through batches with TDD.

## Steps

1. **Parse arguments**: `--slug`, `--plan`, `--resume`.

2. **Resolve session**. Default `--slug` from `_active.json` if missing.

3. **Resolve plan path** (same rules as `/css:review`).

4. **Detect language profile** if `session.language_profile` is unset. Run the detection logic from the spec (Section: Language Detection Logic). Write the resolved profile into the session.

5. **Worktree setup** (if not `--resume`):
   - Compute repo name: `basename $(git rev-parse --show-toplevel)`.
   - Worktree path: `../{repo}-css-{slug}` (or `worktree_parent` from config if set).
   - If the path already exists: ask user "기존 worktree 가 있습니다. [재사용 / 새로 만들기 / 취소]".
   - On new: `git worktree add <path> -b css/<slug>` (base = current branch).
   - Record `phases.execute.worktree = <path>` and `phases.execute.branch = css/<slug>` in the session.

6. **AskUserQuestion (master-flow Gate 2)** ONLY if invoked as part of `/css:ship`:
   "Plan 검증 완료. worktree '`<path>`' 생성 후 execute 를 시작합니다. 배치 N개, 작업 M개. 진행할까요? [Yes / Show plan / Cancel]"

7. **Echo header**: `[css:execute @ slug={slug}]`.

8. **Dispatch the executor**:

   ```
   Task(
     subagent_type="css-executor",
     description="css execute: {slug}",
     prompt="""
     <inputs>
     plan: {plan path}
     worktree: {worktree path}
     branch: css/{slug}
     language_profile: {profile object}
     session: <project>/.claude/css/sessions/{slug}.json
     </inputs>
     <task>
     Implement the plan task-by-task using strict Red-Green-Refactor TDD. Per-batch user checkpoints via AskUserQuestion. Per-task commits on css/{slug}. Self-heal up to 2 cycles via css-debugger; refactor suggestions via css-code-simplifier; extra tests via css-test-engineer when coverage < threshold.
     </task>
     <output_contract>
     Write exec log to: <project>/.claude/css/executions/exec-log-{slug}-{ts}.md
     Final line: VERDICT=PASS | VERDICT=ESCALATE | VERDICT=PAUSE
     </output_contract>
     """
   )
   ```

9. **Parse verdict**:
   - `PASS` → session: `phases.execute.status = completed`. Announce next.
   - `ESCALATE` → surface reason to user with options [retry batch / accept and continue / abort].
   - `PAUSE` → user cancelled. Preserve state for `--resume`.

10. **Release lock**.

<self_check>
- [ ] Worktree path recorded in session
- [ ] Branch css/{slug} created and contains task commits
- [ ] exec-log file exists
- [ ] Coverage measured and recorded
</self_check>

$ARGUMENTS
````

- [ ] **Step 2: Commit**

```bash
git add commands/execute.md
git commit -m "feat(commands): add /css:execute (worktree + TDD)"
```

## Task 4.5: commands/verify.md

**Files:**
- Create: `commands/verify.md`

- [ ] **Step 1: Write the command file**

````markdown
---
description: Test + coverage + code review + security review (CSS pipeline stage 5)
argument-hint: "[--slug <name>] [--exec-log <path>]"
---

# /css:verify

Run the test suite, coverage, criteria mapping, code-quality review, and security review; merge into one verdict. Wraps `css-verifier`.

## Steps

1. **Parse arguments**: `--slug`, `--exec-log`.

2. **Resolve session**.

3. **Retry counter**: if `session.retry_counters.verify >= 3`, escalate to user with options.

4. **Acquire lock** on `verify`.

5. **Echo header**: `[css:verify @ slug={slug}, attempt={n+1}/3]`.

6. **Dispatch the verifier**:

   ```
   Task(
     subagent_type="css-verifier",
     description="css verify: {slug}",
     prompt="""
     <inputs>
     worktree: {session.phases.execute.worktree}
     branch: css/{slug}
     language_profile: {profile}
     spec: {session.phases.interview.artifact}
     plan: {session.phases.plan.artifact}
     </inputs>
     <task>
     Run tests + coverage; map acceptance criteria to code/tests; dispatch css-code-reviewer and css-security-reviewer in parallel; merge findings; decide verdict.
     </task>
     <output_contract>
     Write aggregate report to: <project>/.claude/css/verifies/verify-{slug}-{ts}.md
     Final line: VERDICT=PASS | VERDICT=LOOPBACK_TO_EXECUTE | VERDICT=ESCALATE
     </output_contract>
     """
   )
   ```

7. **Parse verdict**:
   - `PASS` → next.
   - `LOOPBACK_TO_EXECUTE` → increment counter. If `< 3`, automatically invoke `/css:execute --slug <slug> --resume` then re-run verify. If `>= 3`, escalate.
   - `ESCALATE` → stop.

8. **Release lock**.

<self_check>
- [ ] verify-{slug}-{ts}.md exists
- [ ] code-review-{slug}-{ts}.md exists
- [ ] security-review-{slug}-{ts}.md exists
- [ ] retry_counters.verify updated on loopback
</self_check>

$ARGUMENTS
````

- [ ] **Step 2: Commit**

```bash
git add commands/verify.md
git commit -m "feat(commands): add /css:verify (tests + coverage + reviews)"
```

## Task 4.6: commands/document.md

**Files:**
- Create: `commands/document.md`

- [ ] **Step 1: Write the command file**

````markdown
---
description: Generate <project>/docs/<slug>/ markdown documentation (CSS pipeline stage 6)
argument-hint: "[--slug <name>]"
---

# /css:document

Generate user-facing markdown documentation for the implemented feature. Wraps `css-documenter`.

## Steps

1. **Parse arguments**: `--slug`.

2. **Resolve session**.

3. **Pre-check**: `session.phases.verify.verdict` must be `PASS`. If not, abort with: "verify 가 통과되지 않았습니다. `/css:verify` 를 먼저 통과시켜주세요."

4. **Acquire lock**.

5. **Echo header**: `[css:document @ slug={slug}]`.

6. **Dispatch the documenter**:

   ```
   Task(
     subagent_type="css-documenter",
     description="css document: {slug}",
     prompt="""
     <inputs>
     worktree: {session.phases.execute.worktree}
     spec: {session.phases.interview.artifact}
     plan: {session.phases.plan.artifact}
     verify: {session.phases.verify.artifact}
     </inputs>
     <task>
     Generate <project>/docs/{slug}/README.md (required) and conditionally api.md, changelog.md. Use Mermaid for diagrams; pull examples from verified tests; commit as docs(css): add docs for {slug}.
     </task>
     <output_contract>
     Final line: ARTIFACT=<project>/docs/{slug}/README.md
     </output_contract>
     """
   )
   ```

7. **Update session**: `phases.document.status = completed`, `phases.document.artifact = <README path>`.

8. **Release lock**.

<self_check>
- [ ] docs/<slug>/README.md exists
- [ ] Commit "docs(css): add docs for {slug}" in worktree
</self_check>

$ARGUMENTS
````

- [ ] **Step 2: Commit**

```bash
git add commands/document.md
git commit -m "feat(commands): add /css:document"
```

## Task 4.7: commands/pr.md

**Files:**
- Create: `commands/pr.md`

- [ ] **Step 1: Write the command file**

````markdown
---
description: Push css/<slug> and open a PR via gh (CSS pipeline stage 7)
argument-hint: "[--slug <name>] [--draft]"
---

# /css:pr

Push the worktree branch and create a PR. Wraps `css-pr-creator`.

## Steps

1. **Parse arguments**: `--slug`, `--draft`.

2. **Resolve session**.

3. **Pre-check**:
   - `session.phases.document.status` must be `completed`.
   - `gh auth status` must succeed.
   - Working directory must be inside the worktree OR allow the agent to `cd` into it.

4. **AskUserQuestion (master-flow Gate 3)** ONLY if invoked as part of `/css:ship`:
   "구현 + 문서 완료. 브랜치 `css/<slug>` 를 origin 에 push 하고 PR 을 생성합니다. 진행할까요? [Yes / Draft PR / Cancel]"

5. **Acquire lock**.

6. **Echo header**: `[css:pr @ slug={slug}]`.

7. **Dispatch the PR creator**:

   ```
   Task(
     subagent_type="css-pr-creator",
     description="css pr: {slug}",
     prompt="""
     <inputs>
     worktree: {session.phases.execute.worktree}
     branch: css/{slug}
     spec: {session.phases.interview.artifact}
     plan: {session.phases.plan.artifact}
     verify: {session.phases.verify.artifact}
     docs: {session.phases.document.artifact}
     coverage_percent: {from verify report}
     draft: {true if --draft else false}
     </inputs>
     <task>
     Push the branch (no force) after explicit user confirmation; create the PR via gh with a body that links spec/plan/verify/docs and includes acceptance criteria as the test plan.
     </task>
     <output_contract>
     Final line: ARTIFACT=<PR URL>
     </output_contract>
     """
   )
   ```

8. **Update session**: `phases.pr.status = completed`, `phases.pr.artifact = <PR URL>`.

9. **Release lock**. Print the PR URL.

<self_check>
- [ ] PR URL captured in session
- [ ] No force-push performed
</self_check>

$ARGUMENTS
````

- [ ] **Step 2: Commit**

```bash
git add commands/pr.md
git commit -m "feat(commands): add /css:pr"
```

## Task 4.8: commands/ship.md (master)

**Files:**
- Create: `commands/ship.md`

- [ ] **Step 1: Write the command file**

````markdown
---
description: Master pipeline — runs interview → plan → review → execute → verify → document → pr with three approval gates
argument-hint: "[--slug <name>] <idea>"
---

# /css:ship

Run the full CSS pipeline. Three approval gates: Gate 1 is implicit (brainstorming's own user-review step); Gates 2 (pre-execute) and 3 (pre-pr) use AskUserQuestion.

## Steps

1. **Parse arguments**: extract `--slug` if present; remainder is the idea.

2. **Resolve or initialize session**:
   - `--slug` provided + existing `<project>/.claude/css/sessions/<slug>.json` → AskUserQuestion: "기존 세션 발견 (phase=`<current>`). 어떻게 진행할까요? [Resume / Restart / Cancel]".
   - `--slug` provided + no file → init.
   - No `--slug` → derive slug from idea (kebab-case, collision-suffixed if needed), init session, update `_active.json`.
   - Set `session.master_flow = true`.

3. **Acquire lock**.

4. **Stage 1 — interview**:
   - Invoke `/css:interview <idea>` (or resume) inheriting the slug.
   - Gate 1 is implicit: brainstorming's own "user reviews spec" step.

5. **Stage 2 — plan**:
   - Invoke `/css:plan --slug <slug>`.

6. **Stage 3 — review (loop)**:
   - Invoke `/css:review --slug <slug>`.
   - On `LOOPBACK_TO_PLAN`, the review command itself loops back to plan up to 2 attempts.
   - On `LOOPBACK_TO_INTERVIEW`, ask user to confirm before re-entering interview.
   - On `ESCALATE`, stop and surface options.

7. **Gate 2 — pre-execute**:
   - AskUserQuestion: "Plan 검증 완료. worktree '`../<repo>-css-<slug>`' 생성 후 execute 를 시작합니다. 배치 N개, 작업 M개. 진행할까요? [Yes / Show plan / Cancel]".

8. **Stage 4 — execute**: invoke `/css:execute --slug <slug>`. Master flag tells executor not to ask Gate 2 again.

9. **Stage 5 — verify (loop)**:
   - Invoke `/css:verify --slug <slug>`.
   - On `LOOPBACK_TO_EXECUTE`, the verify command itself loops back to execute up to 3 attempts.
   - On `ESCALATE`, stop with options.

10. **Stage 6 — document**: invoke `/css:document --slug <slug>`.

11. **Gate 3 — pre-pr**:
    - AskUserQuestion: "구현 + 문서 완료. 브랜치 `css/<slug>` 를 origin 에 push 하고 PR 을 생성합니다. 진행할까요? [Yes / Draft PR / Cancel]".

12. **Stage 7 — pr**: invoke `/css:pr --slug <slug>` (with `--draft` if user chose).

13. **Finalize**: mark all phases completed, release lock, print summary:
    "Pipeline 완료. PR: `<URL>`. 산출물: `<paths>`."

<self_check>
- [ ] All 7 phases recorded as completed in session
- [ ] Each gate prompt was shown when applicable
- [ ] PR URL captured
- [ ] Lock released
</self_check>

$ARGUMENTS
````

- [ ] **Step 2: Commit**

```bash
git add commands/ship.md
git commit -m "feat(commands): add /css:ship (master pipeline with 3 gates)"
git tag phase-4-commands
```

---

# PHASE 5: Integration + Release

Smoke-test the pipeline against minimal fixtures and ship `v0.1.0`.

## Task 5.1: tests/fixtures/toy-typescript

**Files:**
- Create: `tests/fixtures/toy-typescript/package.json`
- Create: `tests/fixtures/toy-typescript/src/index.ts`
- Create: `tests/fixtures/toy-typescript/src/index.test.ts`
- Create: `tests/fixtures/toy-typescript/vitest.config.ts`
- Create: `tests/fixtures/toy-typescript/tsconfig.json`
- Create: `tests/fixtures/toy-typescript/.gitignore`

- [ ] **Step 1: Write package.json**

```json
{
  "name": "toy-typescript",
  "version": "0.0.1",
  "private": true,
  "type": "module",
  "scripts": {
    "test": "vitest run --coverage"
  },
  "devDependencies": {
    "vitest": "^1.6.0",
    "@vitest/coverage-v8": "^1.6.0",
    "typescript": "^5.4.0"
  }
}
```

- [ ] **Step 2: Write src/index.ts**

```typescript
export function add(a: number, b: number): number {
  return a + b;
}
```

- [ ] **Step 3: Write src/index.test.ts**

```typescript
import { describe, it, expect } from "vitest";
import { add } from "./index";

describe("add", () => {
  it("returns the sum of two numbers", () => {
    expect(add(2, 3)).toBe(5);
  });
});
```

- [ ] **Step 4: Write vitest.config.ts**

```typescript
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    coverage: {
      provider: "v8",
      thresholds: { lines: 85, branches: 85 }
    }
  }
});
```

- [ ] **Step 5: Write tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "include": ["src/**/*"]
}
```

- [ ] **Step 6: Write .gitignore**

```
node_modules/
coverage/
*.log
```

- [ ] **Step 7: Commit**

```bash
git add tests/fixtures/toy-typescript
git commit -m "test(fixtures): add toy-typescript fixture"
```

## Task 5.2: tests/fixtures/toy-python

**Files:**
- Create: `tests/fixtures/toy-python/pyproject.toml`
- Create: `tests/fixtures/toy-python/src/toy_python/__init__.py`
- Create: `tests/fixtures/toy-python/src/toy_python/main.py`
- Create: `tests/fixtures/toy-python/tests/test_main.py`
- Create: `tests/fixtures/toy-python/.gitignore`

- [ ] **Step 1: Write pyproject.toml**

```toml
[project]
name = "toy-python"
version = "0.0.1"
requires-python = ">=3.10"

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-cov>=4.0"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=src/toy_python --cov-report=term-missing --cov-fail-under=85"
```

- [ ] **Step 2: Write src/toy_python/__init__.py**

(empty file)

- [ ] **Step 3: Write src/toy_python/main.py**

```python
def add(a: int, b: int) -> int:
    return a + b
```

- [ ] **Step 4: Write tests/test_main.py**

```python
from toy_python.main import add


def test_add_returns_sum() -> None:
    assert add(2, 3) == 5
```

- [ ] **Step 5: Write .gitignore**

```
.venv/
__pycache__/
*.pyc
.pytest_cache/
.coverage
htmlcov/
```

- [ ] **Step 6: Commit**

```bash
git add tests/fixtures/toy-python
git commit -m "test(fixtures): add toy-python fixture"
```

## Task 5.3: tests/fixtures/toy-go

**Files:**
- Create: `tests/fixtures/toy-go/go.mod`
- Create: `tests/fixtures/toy-go/main.go`
- Create: `tests/fixtures/toy-go/main_test.go`

- [ ] **Step 1: Write go.mod**

```
module toy-go

go 1.22
```

- [ ] **Step 2: Write main.go**

```go
package main

func Add(a, b int) int {
	return a + b
}

func main() {}
```

- [ ] **Step 3: Write main_test.go**

```go
package main

import "testing"

func TestAdd(t *testing.T) {
	if Add(2, 3) != 5 {
		t.Fatal("Add(2,3) != 5")
	}
}
```

- [ ] **Step 4: Commit**

```bash
git add tests/fixtures/toy-go
git commit -m "test(fixtures): add toy-go fixture"
```

## Task 5.4: tests/fixtures/toy-android

**Files:**
- Create: `tests/fixtures/toy-android/build.gradle.kts`
- Create: `tests/fixtures/toy-android/settings.gradle.kts`
- Create: `tests/fixtures/toy-android/app/build.gradle.kts`
- Create: `tests/fixtures/toy-android/app/src/main/AndroidManifest.xml`
- Create: `tests/fixtures/toy-android/app/src/main/java/com/example/toy/MainActivity.kt`
- Create: `tests/fixtures/toy-android/app/src/test/java/com/example/toy/MainActivityTest.kt`
- Create: `tests/fixtures/toy-android/.gitignore`

Note: this is a *detection* fixture for the language-profile logic. It does not need to actually build — the CSS pipeline only needs to identify it as Android/Gradle.

- [ ] **Step 1: Write settings.gradle.kts**

```kotlin
pluginManagement {
    repositories {
        gradlePluginPortal()
        google()
        mavenCentral()
    }
}
dependencyResolutionManagement {
    repositories {
        google()
        mavenCentral()
    }
}
include(":app")
```

- [ ] **Step 2: Write root build.gradle.kts**

```kotlin
plugins {
    id("com.android.application") version "8.5.0" apply false
    id("org.jetbrains.kotlin.android") version "2.0.0" apply false
}
```

- [ ] **Step 3: Write app/build.gradle.kts**

```kotlin
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.example.toy"
    compileSdk = 34
    defaultConfig {
        applicationId = "com.example.toy"
        minSdk = 24
        targetSdk = 34
    }
    buildFeatures { compose = true }
}

dependencies {
    implementation("androidx.activity:activity-compose:1.9.0")
    implementation("androidx.compose.ui:ui:1.6.0")
    implementation("androidx.compose.material3:material3:1.2.0")
    testImplementation("junit:junit:4.13.2")
}
```

- [ ] **Step 4: Write app/src/main/AndroidManifest.xml**

```xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application android:label="ToyAndroid">
        <activity android:name=".MainActivity" android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
```

- [ ] **Step 5: Write app/src/main/java/com/example/toy/MainActivity.kt**

```kotlin
package com.example.toy

import android.app.Activity
import android.os.Bundle

class MainActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
    }

    fun add(a: Int, b: Int): Int = a + b
}
```

- [ ] **Step 6: Write app/src/test/java/com/example/toy/MainActivityTest.kt**

```kotlin
package com.example.toy

import org.junit.Assert.assertEquals
import org.junit.Test

class MainActivityTest {
    @Test
    fun addReturnsSum() {
        val mainActivity = MainActivity()
        assertEquals(5, mainActivity.add(2, 3))
    }
}
```

- [ ] **Step 7: Write .gitignore**

```
.gradle/
build/
local.properties
*.iml
```

- [ ] **Step 8: Commit**

```bash
git add tests/fixtures/toy-android
git commit -m "test(fixtures): add toy-android detection fixture"
```

## Task 5.5: docs/usage.md

**Files:**
- Create: `docs/usage.md`

- [ ] **Step 1: Write usage.md**

````markdown
# Usage

## Quick start

In any git project:

```
/css:ship "<짧은 아이디어>"
```

The pipeline walks through: interview → plan → review → execute → verify → document → pr, with three approval gates.

## Individual commands

Each stage can also run standalone with `--slug`:

```
/css:interview "<idea>"
/css:plan --slug <slug>
/css:review --slug <slug>
/css:execute --slug <slug>
/css:verify --slug <slug>
/css:document --slug <slug>
/css:pr --slug <slug>
```

`--slug` is optional; CSS reads `<project>/.claude/css/sessions/_active.json` to find the most recent session.

## Multi-session concurrency

Open two terminals in the same project:

```
# Terminal 1
/css:ship "feature A"

# Terminal 2
/css:ship "feature B"
```

Each call generates its own slug and operates in isolation (separate session file, separate worktree, separate branch). The two never touch each other's state.

## Output locations

- Spec: `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md` (written by `superpowers:brainstorming`)
- Plan: `docs/superpowers/plans/YYYY-MM-DD-<feature>.md` (written by `superpowers:writing-plans`)
- Reviews/Executions/Verifies/Documents (staging): `<project>/.claude/css/{reviews,executions,verifies,documents}/`
- Domain specs (api/db/ui/etc.): `<project>/.claude/css/plans/<domain>-spec-<slug>-<ts>.md`
- Final user-facing docs: `<project>/docs/<slug>/{README,api,changelog}.md`
- Implementation branch: `css/<slug>` in worktree `../<repo>-css-<slug>`

## Resuming

- `Ctrl+C` is safe. Session state persists.
- Restart with `/css:ship --slug <slug>` (or any standalone command with `--slug`).
- The command resolves what phase the session is in and resumes from there.
````

- [ ] **Step 2: Commit**

```bash
git add docs/usage.md
git commit -m "docs: add usage guide"
```

## Task 5.6: docs/troubleshooting.md

**Files:**
- Create: `docs/troubleshooting.md`

- [ ] **Step 1: Write troubleshooting.md**

````markdown
# Troubleshooting

## "CSS requires the superpowers plugin"

`/css:interview` and `/css:plan` depend on `superpowers`. Enable it:

```
/plugin enable superpowers@claude-plugins-official
```

or edit `~/.claude/settings.json`:

```json
{
  "enabledPlugins": {
    "superpowers@claude-plugins-official": true
  }
}
```

## "gh not found" during /css:pr

Install GitHub CLI: https://cli.github.com/manual/installation, then `gh auth login`.

## "Worktree already exists for slug X"

Either reuse the existing worktree (CSS will prompt), or `git worktree remove ../<repo>-css-<slug>` and start fresh.

## "Same-slug collision: another session is in phase Y"

Two terminals tried to run the same slug. Wait, or use a different idea/slug. If the lock is stale (>30 min), CSS auto-releases with a warning.

## "RED failed: tests did not fail"

The Red phase needs the test to fail before the implementation exists. Either:
- The plan's test is wrong (asserts something already true).
- An earlier task already added the implementation.

Run `/css:review --slug <slug>` to re-audit the plan.

## "Coverage below 85% after self-heal"

`css-test-engineer` was invoked twice but couldn't reach 85%. Inspect the coverage report path in the verify log; add tests manually or lower the threshold per-project in `<project>/.claude/css/config.json`.

## "session.json schema mismatch"

A new CSS version expects a newer session schema. Either:
- Finish the current session under the old version, then upgrade.
- Or back up `<project>/.claude/css/sessions/<slug>.json.bak.<ts>` and restart the session with the new CSS version.

## Cleaning up failed sessions

```bash
# Remove session file
rm <project>/.claude/css/sessions/<slug>.json

# Remove worktree
git worktree remove ../<repo>-css-<slug>

# Optionally delete branch (only if NOT pushed)
git branch -D css/<slug>
```
````

- [ ] **Step 2: Commit**

```bash
git add docs/troubleshooting.md
git commit -m "docs: add troubleshooting guide"
```

## Task 5.7: End-to-end smoke test (Windows)

This task verifies the pipeline against `tests/fixtures/toy-typescript`. It is manual but scripted enough to repeat.

- [ ] **Step 1: Install CSS from the repo**

```powershell
cd D:\03_Workspace\css-claude
.\scripts\install.ps1 -Force
```

Expected: 8 commands and 18 agents copied.

- [ ] **Step 2: Initialize the toy-typescript fixture as a git repo**

```powershell
cd tests\fixtures\toy-typescript
git init
git add .
git commit -m "init: toy-typescript fixture"
npm install
```

- [ ] **Step 3: Run the master pipeline against a trivial idea**

```
/css:ship "add a `multiply(a, b)` function with tests"
```

Expected behaviour:
- Gate 1: brainstorming walks through clarifying questions until you approve a spec.
- Gates 2 and 3 prompt before execute and pr.
- Worktree appears at `..\toy-typescript-css-multiply`.
- Branch `css/multiply` carries one commit per task.
- `tests/fixtures/toy-typescript/docs/multiply/README.md` exists in the worktree.
- A PR draft URL is printed (push only if you have a remote).

- [ ] **Step 4: Verify session file**

```powershell
cat tests\fixtures\toy-typescript\.claude\css\sessions\multiply.json | ConvertFrom-Json
```

Expected: all phases status=`completed`.

- [ ] **Step 5: Cleanup**

```powershell
git worktree remove ..\toy-typescript-css-multiply
git branch -D css/multiply
```

- [ ] **Step 6: Document any failures and fix before proceeding**

If anything failed, open a regular issue in this repo and fix it. Do not tag v0.1.0 until the smoke test passes cleanly.

## Task 5.8: Update README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Change README status to "v0.1.0 released"**

Open `README.md` and replace the `Status:` line with:

```markdown
Status: **v0.1.0**. Personal-use pipeline. See [`docs/installation.md`](docs/installation.md) for setup.
```

- [ ] **Step 2: Add a "Quick start" section after the architecture diagram**

Insert after the existing architecture diagram block:

```markdown
## Quick start

After installation:

```
/css:ship "<your idea>"
```

See [`docs/usage.md`](docs/usage.md) for full command reference.
```

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: update README for v0.1.0"
```

## Task 5.9: Tag and push v0.1.0

- [ ] **Step 1: Tag the release**

```bash
git tag -a v0.1.0 -m "v0.1.0 — initial release of CSS pipeline"
```

- [ ] **Step 2: Push the tag and all phase tags**

```bash
git push origin main
git push origin --tags
```

Expected: GitHub shows `phase-1-foundation`, `phase-2-native-agents`, `phase-3-domain-agents`, `phase-4-commands`, and `v0.1.0` tags.

- [ ] **Step 3: Verify on GitHub**

Visit https://github.com/songsub-cha/css-claude/releases — `v0.1.0` should be present (or visible under `tags`).

---

## Self-Review Notes (filled during writing)

Spec coverage check:

- [x] 8 commands → Phase 4 tasks 4.1–4.8
- [x] 18 agents → Phase 2 (6) + Phase 3 (12)
- [x] Windows + Ubuntu installers → Tasks 1.4, 1.5, 1.6, 1.7
- [x] Default config → Task 1.3
- [x] Multi-session concurrency → encoded in commands (session resolution + per-slug locks)
- [x] superpowers hard dependency → checked in interview.md and plan.md
- [x] Language detection covers JS/TS, Python, Go, Rust, Java/Maven, Java/Kotlin/Gradle, Android → Task 4.4 references the spec section
- [x] TDD RED-GREEN-REFACTOR enforced → executor agent + execute command
- [x] Coverage ≥ 85% → executor + verifier
- [x] /docs/{slug}/ output → documenter agent + document command
- [x] gh CLI PR creation → pr-creator agent + pr command
- [x] Three approval gates in ship → ship.md steps 4 (Gate 1 implicit), 7 (Gate 2), 11 (Gate 3)
- [x] Loopback counters → review.md (max 2), verify.md (max 3)
- [x] Per-slug sessions + _active.json → all command Step 2/3

Placeholder scan: clean — every code block contains the actual content; "Similar to Task N" not used; all OMC-adapted agent tasks show frontmatter + Used_By_CSS explicitly.

Type consistency: artifact-path patterns are consistent across tasks (always `<project>/.claude/css/<dir>/<file>-<slug>-<ts>.md` with `-{ts}` suffix). VERDICT/ARTIFACT/NEXT markers are consistent across agents and commands.
