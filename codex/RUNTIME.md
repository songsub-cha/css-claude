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
