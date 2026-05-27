# CSS Pipeline Design — Claude Super System

## Metadata

- **Created**: 2026-05-27
- **Owner**: sub1904@gmail.com
- **Status**: Design — pending implementation
- **Namespace**: `/css:*` (global Claude Code commands)
- **Target installation**: `~/.claude/commands/css/`, `~/.claude/agents/css/`
- **Future repository**: Private GitHub repo (e.g. `css-claude`)
- **Brainstorming session**: Driven by `superpowers:brainstorming`

## Overview

CSS (Claude Super System) is a personal, global software-development automation pipeline for Claude Code. It exposes eight slash commands under the `/css:` namespace that walk a feature from idea to merged PR through seven stages plus a master command that runs the full pipeline with three approval gates.

### Goals

1. **Idea-to-PR automation** with explicit human checkpoints at high-stakes decisions.
2. **Quality by construction**: TDD with ≥85% coverage enforced, structured planning before implementation, multi-pass review/verify with bounded automatic loopback.
3. **Cross-project reusability**: install once at `~/.claude/`, works in any project on the user's machine.
4. **Independence from OMC**: `/css:*` does not depend on oh-my-claudecode (OMC). It relies only on Claude Code standard plugins (specifically `superpowers`) and `gh` CLI.
5. **Domain-aware delegation**: 17 specialized sub-agents cover API, DB, UI (web + Android), infra, security, testing, debugging, refactoring, async, LLM apps, and prompt authoring.

### Non-Goals (v1)

- Multi-session concurrency in the same project (1 active session per project for v1).
- Auto-merging PRs.
- Cross-language monorepo orchestration beyond per-package detection (basic monorepo handling only).
- Distribution as a Claude Code plugin package (deferred to stage 3 deployment).

## Decisions Summary

| Topic | Decision |
|-------|----------|
| Installation location | `~/.claude/commands/css/` (global commands, `/css:command` namespace) |
| OMC dependency | None — fully independent |
| Master command (`/css:ship`) gates | 3 user approvals: after interview (interview spec accepted), before execute, before PR |
| Language detection | Automatic: JS/TS, Python, Go, Rust, Java (Maven), Java/Kotlin (Gradle, including Android) |
| Artifact storage | `<project>/.claude/css/` (gitignored only where ephemeral) |
| Loopback control | AI auto-judgment, max 2 attempts for review, max 3 for verify, then user escalation |
| Interview style | One question at a time (Socratic, ambiguity-scored) via `superpowers:brainstorming` |
| Plan style | Via `superpowers:writing-plans` |
| `css` meaning | Claude Super System / Studio — general software dev pipeline |
| Architecture | Modular: commands = thin orchestrators, agents = workers |
| Agent system prompts | English (policy precision); user-facing messages and outputs in Korean |
| Deployment scope | Stage 2: private GitHub repo with manual + scripted install (Windows PowerShell + Ubuntu 22.04 Bash) |

## Architecture

### Three-Layer Structure

```
┌─────────────────────────────────────────────────────────┐
│  Commands Layer  (~/.claude/commands/css/)              │
│  /css:interview /css:plan /css:review /css:execute      │
│  /css:verify    /css:document /css:pr /css:ship         │
│                                                          │
│  Role: thin entrypoints. Gate via AskUserQuestion,      │
│        dispatch agents, persist artifacts.              │
└──────────────────────┬──────────────────────────────────┘
                       │ Task() invocations
┌──────────────────────▼──────────────────────────────────┐
│  Agents Layer  (~/.claude/agents/css/)                  │
│  reviewer / executor / verifier / documenter /          │
│  pr-creator / api-specialist / ui-engineer /            │
│  architect / db-specialist / infra-engineer /           │
│  security-reviewer / test-engineer / debugger /         │
│  code-simplifier / async-coder /                        │
│  langgraph-engineer / prompt-engineer                   │
│                                                          │
│  Role: stage- and domain-specific workers with policy   │
│        encoded in system prompts.                       │
└──────────────────────┬──────────────────────────────────┘
                       │ read/write
┌──────────────────────▼──────────────────────────────────┐
│  State Layer  (<project>/.claude/css/)                  │
│  session.json   (current phase, locks, gates)           │
│  specs/         (interview output via brainstorming)    │
│  plans/         (writing-plans output + spec extensions)│
│  reviews/       (review verdicts + findings)            │
│  executions/    (TDD logs + worktree info)              │
│  verifies/      (test/coverage/criteria reports)        │
│  documents/     (staging before docs/<slug>/)           │
└─────────────────────────────────────────────────────────┘
```

### Core Principles

- **Independent execution**: each `/css:*` command can be invoked alone. Missing prior artifacts surface as user-friendly guidance, not crashes.
- **Single source of truth**: per-stage artifacts live under `<project>/.claude/css/`. session.json points to them.
- **Three approval gates only** in `/css:ship`: after interview, before execute, before PR.
- **English policy + Korean response**: agent system prompts use English (precision); user-visible output text is Korean.
- **Domain delegation**: API, DB, UI, infra, async, LLM-app, prompt-engineering work each dispatches to the matching specialist agent before execution.

## Directory Structure

### Global Install (`~/.claude/`)

```
~/.claude/
├── commands/
│   └── css/
│       ├── interview.md       # /css:interview
│       ├── plan.md            # /css:plan
│       ├── review.md          # /css:review
│       ├── execute.md         # /css:execute
│       ├── verify.md          # /css:verify
│       ├── document.md        # /css:document
│       ├── pr.md              # /css:pr
│       └── ship.md            # /css:ship (master)
├── agents/
│   └── css/
│       ├── reviewer.md
│       ├── executor.md
│       ├── verifier.md
│       ├── documenter.md
│       ├── pr-creator.md
│       ├── api-specialist.md
│       ├── ui-engineer.md
│       ├── architect.md
│       ├── db-specialist.md
│       ├── infra-engineer.md
│       ├── security-reviewer.md
│       ├── test-engineer.md
│       ├── debugger.md
│       ├── code-simplifier.md
│       ├── async-coder.md
│       ├── langgraph-engineer.md
│       └── prompt-engineer.md
└── css/
    └── config.json            # global defaults (optional)
```

### Per-Project Artifacts (`<project>/.claude/css/`)

```
<project>/.claude/css/
├── session.json
├── specs/
│   └── interview-{slug}-{ts}.md          # from superpowers:brainstorming
├── plans/
│   ├── plan-{slug}-{ts}.md               # from superpowers:writing-plans
│   ├── api-spec-{slug}-{ts}.md           # from css-api-specialist (if applicable)
│   ├── db-spec-{slug}-{ts}.md
│   ├── ui-spec-{slug}-{ts}.md
│   ├── infra-spec-{slug}-{ts}.md
│   ├── arch-review-{slug}-{ts}.md
│   ├── async-spec-{slug}-{ts}.md
│   ├── llm-app-spec-{slug}-{ts}.md
│   └── prompt-spec-{slug}-{ts}.md
├── reviews/
│   └── review-{slug}-{ts}.md
├── executions/
│   ├── exec-log-{slug}-{ts}.md
│   └── worktree-{slug}/                  # metadata only; the actual worktree lives at ../{repo}-css-{slug}
├── verifies/
│   └── verify-{slug}-{ts}.md
└── documents/
    └── doc-staging-{slug}.md
```

### Final Documentation (`<project>/docs/{slug}/`)

```
<project>/docs/{slug}/
├── README.md         # always
├── api.md            # if public API surface added
└── changelog.md      # if behavior change or migration
```

### Naming Rules

- `{slug}`: kebab-case identifier derived during interview (e.g. `user-auth-jwt`).
- `{ts}`: ISO-8601 timestamp with safe separator (e.g. `2026-05-27T14-30`).
- **All artifact filenames include `-{ts}`** without exception (interview spec, plan, domain specs, reviews, exec logs, verifies, document staging).
- Re-running a stage with the same slug creates a new timestamped artifact (history preserved). session.json points to the latest.
- Final user-facing documentation (`<project>/docs/{slug}/*.md`) does **not** use timestamps in filenames — those are the merged-product canonical docs.

## Command Specifications

All eight commands follow the same skeleton:

```
1. Parse arguments and flags.
2. Load session.json (or initialize).
3. Acquire phase lock.
4. Detect language profile if missing.
5. Gate (AskUserQuestion) when required.
6. Dispatch to skill or sub-agent.
7. Persist artifact path, update session.json.
8. Release lock.
9. Announce next step (and, for /css:ship, auto-advance).
```

### `/css:interview <idea>`

- **Skill**: `superpowers:brainstorming`
- **Behavior**:
  1. Initialize session.json with a generated slug (extracted from brainstorming's design filename).
  2. `Skill("superpowers:brainstorming")` runs the full Socratic flow (context discovery → clarifying questions → 2-3 approaches → section-by-section design → spec write → spec self-review → user review).
  3. **Override**: skip brainstorming's terminal `writing-plans` invocation. CSS calls `/css:plan` separately so each command remains independently runnable.
  4. Record `phases.interview.artifact` in session.json (path to brainstorming's spec file).
- **Output**: `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md` (brainstorming default location, kept as single source of truth).
- **Gate** (in master flow): the user-review step inside brainstorming serves as Gate 1.

### `/css:plan [--from <spec-path>]`

- **Skill**: `superpowers:writing-plans`
- **Behavior**:
  1. Resolve spec path (argument > session.json > prompt user).
  2. `Skill("superpowers:writing-plans")` produces a structured plan.
  3. Persist plan path in session.json.
- **Output**: writing-plans default location (e.g. `docs/superpowers/plans/...`). CSS only records the path.

### `/css:review [--plan <plan-path>]`

- **Agent**: `css-reviewer` (with sub-dispatch to domain specialists)
- **Behavior**:
  1. Reviewer loads plan + spec, performs coverage-matrix audit.
  2. Reviewer identifies domains and dispatches to specialists in parallel:
     - REST/GraphQL/gRPC/tRPC patterns → `css-api-specialist`
     - SQL schemas, migrations, Redis, ARQ → `css-db-specialist`
     - Components/Composables/Activity/Fragment → `css-ui-engineer`
     - Dockerfile/compose/K8s/CI → `css-infra-engineer`
     - Architecture-touching changes → `css-architect`
     - `async`/`await`/`asyncio` patterns → `css-async-coder`
     - LangChain/LangGraph/LangFuse → `css-langgraph-engineer`
     - LLM prompt authoring → `css-prompt-engineer`
  3. Specialist outputs become `*-spec-{slug}.md` artifacts referenced by the plan.
  4. Reviewer issues verdict: `PASS | LOOPBACK_TO_PLAN | LOOPBACK_TO_INTERVIEW`.
  5. Auto-loopback up to 2 attempts. Escalates to user beyond that.
- **Output**: `.claude/css/reviews/review-{slug}-{ts}.md` + domain spec files.

### `/css:execute [--plan <plan-path>]`

- **Agent**: `css-executor` (with on-demand calls to debugger, code-simplifier, test-engineer)
- **Behavior**:
  1. Create `git worktree add ../{repo}-css-{slug} -b css/{slug}`.
  2. Group plan tasks into batches by dependency graph.
  3. **Batch checkpoint**: before each batch, announce intent and request user confirmation. These per-batch micro-checkpoints are **separate from and additional to** the three master `/css:ship` gates (post-interview, pre-execute, pre-PR). They only appear during execute and do not block standalone `/css:execute` use beyond a single combined "start execute?" prompt.
  4. For each task, enforce TDD:
     - **RED**: write tests, run, must fail. If exit code 0 → abort task and escalate.
     - **GREEN**: implement minimum; up to 2 self-heal cycles via `css-debugger` on failure; if still failing, escalate.
     - **REFACTOR**: call `css-code-simplifier` for style improvement; tests must remain green.
  5. Per-task commit on the css branch.
  6. Per-batch coverage measurement. If <85%, call `css-test-engineer` for up to 2 additional test-author cycles.
- **Output**: `css/{slug}` branch in `../{repo}-css-{slug}` worktree + `.claude/css/executions/exec-log-{slug}-{ts}.md`.

### `/css:verify [--exec-log <log-path>]`

- **Agent**: `css-verifier` (with mandatory `css-security-reviewer`)
- **Behavior**:
  1. Run the full test suite in the worktree using the detected commands.
  2. Run coverage tool, ensure ≥85%.
  3. Map each acceptance criterion in the spec to concrete code/test evidence.
  4. Always invoke `css-security-reviewer` (OWASP, secrets scan, dependency audit).
  5. Verdict: `PASS | LOOPBACK_TO_EXECUTE | ESCALATE`.
  6. Auto-loopback up to 3 attempts. Then user escalation.
- **Output**: `.claude/css/verifies/verify-{slug}-{ts}.md`.

### `/css:document [--from-worktree]`

- **Agent**: `css-documenter`
- **Behavior**:
  1. Read spec, plan, verify report, and the actual code in the worktree.
  2. Generate `<project>/docs/{slug}/README.md` (overview, quick start, usage, architecture, testing, future work).
  3. Conditionally generate `api.md`, `changelog.md`.
  4. Extract usage examples from verified tests.
  5. Use Mermaid for diagrams when helpful.
  6. Commit `docs(css): add docs for {slug}` in the worktree.
- **Output**: `<project>/docs/{slug}/*.md`.

### `/css:pr [--draft]`

- **Agent**: `css-pr-creator`
- **Behavior**:
  1. Verify `gh` CLI is available; abort with guidance if not.
  2. Detect base branch via `git symbolic-ref refs/remotes/origin/HEAD`.
  3. Request explicit user confirmation before push (no force push allowed).
  4. `git push -u origin css/{slug}`.
  5. Assemble PR body (Summary / Spec link / Plan link / Test plan / Coverage / Checklist).
  6. `gh pr create` (with `--draft` if requested).
  7. Print PR URL.
- **Output**: GitHub PR URL.

### `/css:ship <idea>` (master)

- Orchestrates `/css:interview` → `/css:plan` → `/css:review` (auto-loopback) → **Gate 2** → `/css:execute` → `/css:verify` (auto-loopback) → `/css:document` → **Gate 3** → `/css:pr`.
- Gate 1 is implicit (the brainstorming user-review step).
- Resumable: on Ctrl+C, session.json is preserved; re-running prompts to resume or restart.

## Agent Specifications

### Stage Agents (5)

| Agent | Model | Source | Key Policy |
|-------|-------|--------|-----------|
| `css-reviewer` | opus | OMC `code-reviewer` + CSS adaptations | Coverage-matrix audit, specialist dispatch, verdict |
| `css-executor` | sonnet (opus fallback for complex tasks) | CSS-native | TDD enforcement, worktree isolation |
| `css-verifier` | sonnet (opus fallback) | CSS-native | Test/coverage/criteria mapping, loopback decision |
| `css-documenter` | sonnet | OMC `document-specialist` + CSS adaptations | docs/{slug}/ structure, example extraction |
| `css-pr-creator` | haiku | OMC `git-master` + CSS adaptations | gh CLI workflow, PR body template, no force push |

### Domain Specialists (12, copied from OMC with CSS headers)

| Agent | Model | Domain | Dispatched From |
|-------|-------|--------|-----------------|
| `css-api-specialist` | opus | REST/GraphQL/gRPC/tRPC contract design | review |
| `css-ui-engineer` | opus | Web + Android UI/UX (Material 3, Compose, web frameworks) | review |
| `css-architect` | opus (read-only) | System architecture, module boundaries | review |
| `css-db-specialist` | sonnet | PostgreSQL, Redis, ARQ, migrations | review |
| `css-infra-engineer` | sonnet | Docker, K8s, CI/CD, nginx | review |
| `css-security-reviewer` | opus (read-only) | OWASP, secrets, dependency audit | verify (always), review (on demand) |
| `css-test-engineer` | sonnet | Test design, coverage gap closure | execute (when coverage <85%) |
| `css-debugger` | sonnet | Root-cause analysis | execute (GREEN self-heal) |
| `css-code-simplifier` | opus | Refactoring for clarity | execute (REFACTOR) |
| `css-async-coder` | sonnet | Python asyncio concurrency | review |
| `css-langgraph-engineer` | sonnet | LangChain/LangGraph/LangFuse LLM apps | review |
| `css-prompt-engineer` | opus | 9-section prompt design | review |

### Common Frontmatter

```yaml
---
name: css-{role}
description: {one-line role + (CSS pipeline, model)}
model: opus | sonnet | haiku
disallowedTools: [Write, Edit]      # for read-only agents
css_stages: [review]                 # array — an agent may be called from multiple stages
                                     # e.g. security-reviewer: [verify, review]
adapted_from: oh-my-claudecode/agents/{source}.md   # for OMC-derived agents (omit for CSS-native)
---
```

### UI Engineer Platform Switching

`css-ui-engineer` auto-detects platform:

- **Web** if `package.json` has `react`, `vue`, `svelte`, `@angular/core`, etc.
- **Android** if `build.gradle(.kts)` declares `com.android.application` or `androidx.compose.*` dependencies.
- **Both** if a monorepo has both.

For Android specifically: Material 3, Jetpack Compose preferred (Kotlin), 48dp touch targets, dark theme + dynamic color, TalkBack labels, font scaling, RTL support, ConstraintLayout/XML fallback when Compose absent.

## Data Flow and State Management

### session.json Schema

```json
{
  "schema_version": "1.0.0",
  "session_id": "uuid-v4",
  "slug": "user-auth-jwt",
  "created_at": "2026-05-27T14:30:00Z",
  "updated_at": "2026-05-27T15:42:11Z",
  "current_phase": "execute",
  "master_flow": true,
  "phases": {
    "interview": { "status": "completed", "artifact": "...", "ambiguity": 0.18, "rounds": 12 },
    "plan":      { "status": "completed", "artifact": "...", "task_count": 9 },
    "review":    { "status": "completed", "artifact": "...", "verdict": "PASS", "attempts": 1 },
    "execute":   { "status": "in_progress", "artifact": "...", "worktree": "...", "branch": "css/user-auth-jwt", "current_batch": 2, "total_batches": 3 },
    "verify":    { "status": "pending" },
    "document":  { "status": "pending" },
    "pr":        { "status": "pending" }
  },
  "retry_counters": { "review": 0, "verify": 0, "execute_tdd_self_heal": { "task_3": 0 } },
  "gates": { "interview_approval": "approved", "execute_approval": "approved", "pr_approval": "pending" },
  "lock": { "phase": "execute", "pid": null, "started_at": "2026-05-27T15:20:00Z" },
  "language_profile": {
    "primary": "kotlin-android",
    "build_tool": "gradle",
    "test_command": "./gradlew testDebugUnitTest",
    "coverage_command": "./gradlew jacocoTestReport",
    "coverage_report_path": "app/build/reports/jacoco/jacocoTestReport/html/index.html",
    "platform": "android",
    "ui_framework": "compose",
    "detected_from": ["build.gradle.kts", "settings.gradle.kts"]
  },
  "last_error": null
}
```

### Resume Scenarios

| Scenario | Behavior |
|----------|----------|
| `/css:ship` interrupted | session.json preserved; re-run prompts: resume / restart |
| `/css:execute` standalone with no session | Requires `--plan <path>` |
| Same slug re-run | Backup session as `.bak.{ts}`, start fresh; artifacts accumulate |
| Worktree already exists | Prompt: reuse / recreate / cancel |

### Concurrency Lock

- `session.lock` field gates phase entry.
- If same phase + <30 min → reject.
- If different phase + <30 min → warn user.
- If stale (>30 min) → force release with warning.
- v1 limitation: 1 active session per project.

### Language Detection Logic

```
1. package.json present                 → JS/TS
   - vitest in deps                      → vitest run --coverage
   - jest in deps                        → jest --coverage
   - pnpm/yarn lockfile                  → package manager picked

2. pyproject.toml | setup.py | requirements.txt → Python
   - pytest in deps                      → pytest --cov
   - poetry.lock / uv.lock               → poetry / uv; else pip

3. go.mod                               → Go
   - test: go test -cover ./...

4. Cargo.toml                           → Rust
   - test: cargo test
   - coverage: cargo tarpaulin

5. pom.xml                              → Java + Maven
   - test: mvn test
   - coverage: mvn jacoco:report

6. build.gradle | build.gradle.kts |
   settings.gradle(.kts)                → Java/Kotlin + Gradle
   - test: ./gradlew test
   - coverage: ./gradlew jacocoTestReport (fallback koverHtmlReport)
   - If com.android.application or androidx.compose detected:
       platform=android, ui_framework=compose,
       test: ./gradlew testDebugUnitTest,
       optional: connectedAndroidTest (if emulator)

7. Multiple manifests (monorepo)        → array of language_profiles
   - Each task's Files path resolves which profile

8. None detected                        → ask user in interview, save to session
```

## Error Handling and Loopback Logic

### Loopback Decision Matrix

| Stage | Finding | Result |
|-------|---------|--------|
| review | Acceptance criterion in plan not in spec (or vice versa) | LOOPBACK_TO_INTERVIEW |
| review | Plan misses acceptance criteria | LOOPBACK_TO_PLAN |
| review | Dependency cycle / invalid file path | LOOPBACK_TO_PLAN |
| review | Incomplete code snippet (TODO/`...`) | LOOPBACK_TO_PLAN |
| review | API/UI specialist artifact missing | LOOPBACK_TO_PLAN |
| verify | Test failure | LOOPBACK_TO_EXECUTE |
| verify | Coverage <85% | LOOPBACK_TO_EXECUTE |
| verify | Acceptance criterion not mapped | LOOPBACK_TO_EXECUTE |
| verify | Interface drift from api-spec | LOOPBACK_TO_EXECUTE |
| verify | UI accessibility violation (Android <48dp, etc.) | LOOPBACK_TO_EXECUTE |

### Counters

- review attempts ≤ 2
- verify attempts ≤ 3
- TDD self-heal per task ≤ 2

When exceeded → user escalation via `AskUserQuestion` with options: retry once / accept current state / abort and preserve.

### TDD Self-Heal (executor internal)

```
RED:
  write tests → run
  if exit 0: abort task ("RED failed: tests did not fail")
  else: continue

GREEN:
  for attempt in 0..2:
    write/patch implementation → run tests
    if exit 0: break
    diagnose with css-debugger → patch hint
  else: abort task, escalate

REFACTOR:
  invoke css-code-simplifier → patch → run tests
  if regression: revert refactor, log warning, proceed
```

### Error Classes

| Class | Example | Handling |
|-------|---------|----------|
| Validation | corrupt session.json | abort pre-check + recovery guidance |
| Tool | gh missing, worktree create fails | report + suggest alternatives |
| Agent | sub-agent Task failure | mark phase failed, preserve session |
| Policy violation | RED did not fail, write outside worktree | immediate abort, never silent |
| Loopback (normal) | review/verify within counters | automatic retry |

**Principle**: no silent failure. Every abnormal end records `last_error` in session.json and surfaces to user.

## Master Flow (`/css:ship`)

```
USER: /css:ship "<idea>"

[ship.md]
1. Check session.json.
   Existing? → AskUserQuestion: resume / new session / cancel.
   New?      → generate slug, init session.json, acquire lock.

2. /css:interview <idea>
   → superpowers:brainstorming runs
   → spec written
   → brainstorming's "user reviews spec" step IS Gate 1

3. /css:plan
   → superpowers:writing-plans runs
   → plan written

4. /css:review (auto-loop)
   loop:
     css-reviewer runs (dispatches domain specialists in parallel)
     verdict == PASS → break
     verdict == LOOPBACK_TO_PLAN → /css:plan (attempts++)
     verdict == LOOPBACK_TO_INTERVIEW → user confirm → /css:interview
     attempts >= 2 → escalate

5. [Gate 2] AskUserQuestion:
   "Plan validated. Worktree '../{repo}-css-{slug}', N batches, M tasks. Start execute?"

6. /css:execute
   → worktree create
   → batch-by-batch TDD with checkpoints
   → all tasks complete

7. /css:verify (auto-loop)
   loop:
     css-verifier + css-security-reviewer run
     verdict == PASS → break
     verdict == LOOPBACK_TO_EXECUTE → /css:execute --resume (failed tasks only)
     attempts >= 3 → escalate

8. /css:document
   → css-documenter runs
   → docs/{slug}/ written + committed in worktree

9. [Gate 3] AskUserQuestion:
   "Implementation + docs complete. Push 'css/{slug}' and create PR? (draft / normal / cancel)"

10. /css:pr
    → push → gh pr create → print URL

11. Finalize: mark all phases completed, release lock.
```

### Standalone Command Behavior

When a single `/css:*` is invoked outside of `/css:ship`:

- No gate prompts are added — the user is presumed to know what they want.
- Missing prior artifacts surface as friendly guidance ("Run `/css:plan` first or pass `--plan <path>`").
- session.json still tracks progress so that switching to `/css:ship` later can resume.

## Skill Dependencies

### Hard Dependencies

- `superpowers:brainstorming` — `/css:interview`
- `superpowers:writing-plans` — `/css:plan`

CSS commands check `~/.claude/settings.json`'s `enabledPlugins["superpowers@claude-plugins-official"]` at entry. If disabled, abort with clear instructions to enable.

### Soft Dependencies

| CSS stage | Skill | Behavior |
|-----------|-------|----------|
| execute - worktree | `superpowers:using-git-worktrees` | Use if available; fallback to direct `git worktree` |
| execute - TDD | `superpowers:test-driven-development` | Use if available for RED-GREEN-REFACTOR enforcement |
| execute - debug | `superpowers:systematic-debugging` | Use during self-heal |
| verify | `superpowers:verification-before-completion` | Use as guardrail |

### External Tools

- `gh` CLI — required for `/css:pr`.
- `git` ≥ 2.5 — required for worktree.
- Language-specific test/coverage tools — auto-detected; missing tools prompt user (in interview phase).

## Testing Strategy

### 1. Agent Unit (manual + golden file)

```
tests/css/agents/
├── reviewer/
│   ├── input-plan-missing-criteria.md
│   └── expected-verdict.txt
├── api-specialist/
│   ├── input-rest-spec.md
│   └── golden-output-shape.md
└── ...
```

Validate: output structure, verdict format, policy compliance (e.g. reviewer never asks two questions at once).

### 2. Command Integration (toy projects)

```
tests/css/fixtures/
├── toy-typescript/
├── toy-python/
├── toy-android/
└── toy-go/
```

Scenarios per fixture: A (interview happy path), B (plan from spec), C (execute 1 task with TDD log), D (verify catches injected failure).

### 3. End-to-End (`/css:ship` weekly)

Smallest real feature, watch all gates and loopbacks. Confirm PR is created.

### 4. Self-Check Block in Commands

Each command `.md` ends with:

```markdown
<self_check>
- [ ] Artifact written to correct path
- [ ] session.json phase status updated
- [ ] Last line contains VERDICT=... or NEXT=...
- [ ] No policy violations
</self_check>
```

### 5. Regression Tracking

- Artifacts in `.claude/css/` are git-tracked → diff between runs surfaces drift.
- Re-run same scenario twice; large divergence in artifacts signals an unstable system prompt.

### 6. Metrics (collected over time, no gating threshold v1)

| Metric | Target |
|--------|--------|
| interview avg rounds | 8–15 |
| review loopback rate | <30% |
| verify loopback rate | <40% |
| TDD self-heal success | >60% |
| /css:ship end-to-end time | recorded only |

## Security Guardrails

### Worktree Isolation

- All code changes happen in `../{repo}-css-{slug}`.
- css-executor verifies `cwd` at entry; aborts if in main working tree.
- Forbidden inside worktree:
  - Direct `.git/` modification
  - Access to main working tree path
  - `..` traversal above worktree root

### Secrets

- All agent prompts include rule: never write API keys / passwords / tokens / `.env` values directly. Reference env vars or secret managers.
- Detected secrets in existing code → mask in artifacts (`***REDACTED***`) and report to user.
- Recommended `.gitignore` additions: `.claude/css/state/` (lock, ephemeral), `.claude/css/archive/`.

### Agent Tool Allowlist

- Read-only agents: `disallowedTools: [Write, Edit]` (architect, security-reviewer, reviewer, verifier baseline).
- Write-capable agents: explicit allow (executor, documenter, pr-creator).
- `Bash` blocked patterns (require user confirmation): `rm -rf`, `git push --force`, `git reset --hard origin/*`, `chmod 777`.

### Command Entry Guards

- Lock check (concurrency).
- cwd must be inside a git repo (or its worktree).
- Required tool presence (`gh` only at `/css:pr`).
- Clear, recoverable errors on failure.

### Explicit User Approvals

- worktree creation
- branch push
- PR creation (draft or normal)
- force release of non-stale lock
- overwrite of existing session

## Installation and Deployment

### Stage 1 — Personal (current target)

- Files copied to `~/.claude/commands/css/` and `~/.claude/agents/css/`.
- Cross-machine sync via dotfiles or the install script.

### Stage 2 — Private GitHub Repository (current target)

Repository layout:

```
css-claude/                       # private GitHub repo (e.g. github.com/songsub-cha/css-claude)
├── README.md
├── LICENSE                       # personal use license
├── commands/                     # source of truth for ~/.claude/commands/css/
│   └── *.md
├── agents/                       # source of truth for ~/.claude/agents/css/
│   └── *.md
├── config/
│   └── default-config.json       # global defaults
├── scripts/
│   ├── install.ps1               # Windows PowerShell installer
│   ├── install.sh                # Ubuntu 22.04 Bash installer
│   ├── uninstall.ps1
│   └── uninstall.sh
├── docs/
│   ├── specs/                    # design docs (this file)
│   ├── usage.md
│   ├── architecture.md
│   ├── installation.md
│   └── troubleshooting.md
└── tests/
    ├── agents/                   # golden files
    └── fixtures/                 # toy projects
```

#### Deployment Sequence (after implementation completes)

1. Pipeline implementation lands locally and passes integration tests.
2. Create private GitHub repo (manual: `gh repo create <user>/css-claude --private`).
3. Initial commit with all sources, scripts, and docs.
4. Tag `v0.1.0`.
5. README documents prerequisites + install steps.

#### Prerequisites (documented in README)

- Claude Code installed.
- `superpowers` plugin enabled in `~/.claude/settings.json`.
- `gh` CLI installed and authenticated.
- `git` ≥ 2.5.
- Optional but recommended language-specific test/coverage tools.

### Stage 3 — Plugin Packaging (deferred)

After v0.1.0 stabilizes, consider repackaging as a Claude Code plugin so `/plugin install css` is available. Not v1 scope.

## Installation Scripts

### Windows PowerShell (`scripts/install.ps1`)

Design (final code in implementation phase):

```powershell
# install.ps1 — Windows installer for CSS
# Usage: irm https://raw.githubusercontent.com/songsub-cha/css-claude/main/scripts/install.ps1 | iex
#    or: .\scripts\install.ps1 -SourcePath .

param(
  [string]$SourcePath = $PSScriptRoot + "\..",
  [switch]$Force
)

# 1. Verify prerequisites
#    - Claude Code config dir: $env:USERPROFILE\.claude
#    - gh.exe in PATH
#    - git in PATH (version ≥ 2.5)
#    - superpowers enabled in ~/.claude/settings.json

# 2. Create directories
#    - ~/.claude/commands/css
#    - ~/.claude/agents/css
#    - ~/.claude/css

# 3. Copy files
#    - commands/*.md → ~/.claude/commands/css/
#    - agents/*.md   → ~/.claude/agents/css/
#    - config/default-config.json → ~/.claude/css/config.json (only if absent or -Force)

# 4. Verify superpowers in settings.json; warn if disabled.

# 5. Print summary: file counts, prerequisite status, next steps.
```

### Ubuntu 22.04 Bash (`scripts/install.sh`)

Design (final code in implementation phase):

```bash
#!/usr/bin/env bash
# install.sh — Ubuntu 22.04 installer for CSS
# Usage: curl -fsSL https://raw.githubusercontent.com/songsub-cha/css-claude/main/scripts/install.sh | bash
#    or: bash scripts/install.sh

set -euo pipefail

SOURCE_PATH="${SOURCE_PATH:-$(dirname "$0")/..}"
CLAUDE_HOME="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
FORCE="${FORCE:-0}"

# 1. Verify prerequisites
#    - $CLAUDE_HOME exists
#    - command -v gh
#    - command -v git; git version ≥ 2.5
#    - jq for settings.json parsing
#    - superpowers enabled in $CLAUDE_HOME/settings.json

# 2. mkdir -p $CLAUDE_HOME/{commands/css,agents/css,css}

# 3. cp -r commands/*.md $CLAUDE_HOME/commands/css/
#    cp -r agents/*.md   $CLAUDE_HOME/agents/css/
#    Only copy default-config.json if absent or FORCE=1.

# 4. Warn if superpowers disabled.

# 5. Summary printout.
```

### Uninstaller Behavior (both platforms)

- Remove `~/.claude/commands/css/` and `~/.claude/agents/css/`.
- Keep `~/.claude/css/config.json` and per-project `.claude/css/` artifacts (user must remove explicitly).
- Print restoration command for accidental removal.

### Per-Machine Setup Flow

1. Clone repo locally (or download release archive).
2. Run platform-appropriate installer.
3. (Optional) Edit `~/.claude/css/config.json` for personal defaults.
4. Run `/css:ship "<small idea>"` in a sample project to verify.

## Migration and Removal

### Updates

- Pull from private repo or re-run install script.
- In-flight sessions are not affected; artifacts are file-based.
- Schema-version mismatch in session.json triggers migration guidance.

### Removal

- Delete `~/.claude/commands/css/` and `~/.claude/agents/css/`.
- Project `.claude/css/` artifacts are preserved (user manages).
- Worktrees and branches are user-managed (no auto-delete to avoid losing work).

### Temporary Disable

- Rename `~/.claude/commands/css/` (e.g. to `_css.bak`).

## Open Questions / Future Work

- **Multi-session per project**: array-of-sessions support in session.json; deferred.
- **Stage 3 plugin packaging**: bundle commands + agents into a single installable Claude Code plugin.
- **Telemetry**: opt-in metrics export to evaluate prompt drift over time.
- **Ralph-style persistence loop**: integration with `/css:ship` for ambient self-correction (deferred).
- **Cross-language monorepo orchestration** beyond per-package detection.
- **Cloud sync of session.json**: optional GitHub-based sync to resume sessions across machines.

## Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| Long prompts overflow context | Per-stage artifacts are file-based; agents read only what they need. brainstorming/writing-plans already manage context. |
| Brittle TDD enforcement (false RED pass) | Executor explicitly checks exit code. If RED unexpectedly passes, aborts and escalates rather than continuing. |
| Loopback infinite loops | Hard counters (review=2, verify=3, self-heal=2). |
| OMC drift breaks adapted agents | Adapted-from frontmatter cites OMC path. Periodic manual diff. CSS-specific overrides documented inside each agent. |
| Coverage tool detection fails | Fallback: ask user in interview, save to language_profile. |
| User accidentally commits secrets | Agent prompts forbid; secret-pattern grep at verify; .gitignore additions suggested. |
| Worktree pollution if `/css:ship` is cancelled mid-execute | Worktree preserved deliberately; cleanup is a separate explicit command. |

## Glossary

- **CSS**: Claude Super System (this pipeline). Not to be confused with web CSS.
- **Slug**: kebab-case identifier for a feature, generated during interview.
- **Worktree**: a `git worktree`-isolated checkout used during `/css:execute`.
- **Gate**: a user approval point in `/css:ship`. Three exist: post-interview (implicit), pre-execute, pre-PR.
- **Loopback**: automatic re-entry into an earlier stage based on a verdict from review or verify.
- **Specialist**: domain-specific sub-agent (api/db/ui/etc.) called by `css-reviewer` during the review stage.
- **Master command**: `/css:ship`, which runs the full pipeline.
