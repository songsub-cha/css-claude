# css-claude

**CSS — Claude Super System**: a personal, global software-development automation pipeline for [Claude Code](https://claude.com/claude-code).

Status: **v0.1.0**. Personal-use pipeline. See [`docs/installation.md`](docs/installation.md) for setup.

## What it is

Eight slash commands under the `/css:` namespace that walk a feature from idea to merged PR through seven stages, plus a master command that runs the full pipeline with three approval gates.

```
/css:interview  →  /css:plan  →  /css:review  →  /css:execute  →  /css:verify  →  /css:document  →  /css:pr
                                                                                                        ↑
                                                /css:ship  ──── runs everything with 3 gates ──────────┘
```

## Quick start

After installation:

```
/css:ship "<your idea>"
```

See [`docs/usage.md`](docs/usage.md) for full command reference.

## Highlights

- **Idea-to-PR automation** with explicit human checkpoints at high-stakes decisions
- **TDD enforced** with ≥85% coverage in the execute stage
- **18 specialized sub-agents** for plan review, code-quality review, API, DB, UI (web + Android), infra, security, testing, debugging, refactoring, async, LLM apps, and prompt engineering
- **Auto language detection**: JS/TS, Python, Go, Rust, Java (Maven), Java/Kotlin (Gradle, including Android Jetpack Compose)
- **Stateful & resumable** via `<project>/.claude/css/sessions/{slug}.json`
- **Multi-session concurrency**: run `/css:ship` for feature A in one terminal and feature B in another against the same project — sessions are isolated by slug
- **Bounded automatic loopback** between stages, with user escalation when limits are hit
- **OMC-independent** — depends only on Claude Code's `superpowers` plugin and `gh` CLI

## Design

See [`docs/specs/2026-05-27-css-pipeline-design.md`](docs/specs/2026-05-27-css-pipeline-design.md) for the full design.

## Prerequisites (planned)

- Claude Code
- `superpowers` plugin enabled
- `gh` CLI authenticated
- `git` ≥ 2.5

## Installation (planned)

Manual or via platform scripts:

- Windows: `scripts/install.ps1`
- Ubuntu 22.04: `scripts/install.sh`

Details: see design doc § Installation Scripts.

## Layout (planned)

```
css-claude/
├── README.md
├── commands/      # → ~/.claude/commands/css/
├── agents/        # → ~/.claude/agents/css/
├── config/        # default config
├── scripts/       # install / uninstall scripts (Windows + Ubuntu)
├── docs/          # design, usage, troubleshooting
└── tests/         # agent goldens + toy fixtures
```

## License

Personal use. Not for redistribution at this stage.
