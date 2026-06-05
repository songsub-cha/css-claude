# CSS Codex Runtime - Execution Model & Tool Mapping

Every installed CSS skill (`~/.agents/skills/css-*/SKILL.md`) begins with a
pointer to this file. Read it before acting. CSS command and agent bodies are
copied verbatim from Claude Code and reference Claude tool names; this file
maps each to its Codex behavior. User instructions and the skill body always
take precedence over the examples here.

## Skill Invocation Arguments

The copied Claude command bodies may reference `$ARGUMENTS`. On Codex, interpret
`$ARGUMENTS` as the text supplied with the skill invocation:

- `$css-ship "small idea"` means `$ARGUMENTS` is `"small idea"`.
- Selecting `css-ship` from an App or CLI skill menu and typing follow-up text
  uses that follow-up text as `$ARGUMENTS`.
- If the skill was triggered implicitly by a user request, use the user's
  request text as `$ARGUMENTS`.
- If no text was supplied, treat `$ARGUMENTS` as empty and continue only if the
  command body supports that flow.

Codex surfaces can differ. Prefer explicit skill invocation through `$css-*` or
the App/CLI skill menu. If a surface does not expose a menu, the user can still
type the skill mention directly. Do not use or depend on legacy command
artifacts.

## Tool Mapping

| The body calls | Do this on Codex |
|---|---|
| `Task(subagent_type=X, prompt=P)` | Resolve `X` via `~/.codex/css/agents/index.json` to an agent file. If `spawn_agent` is available, call `spawn_agent` with that file's contents plus `P` as the prompt. Otherwise, perform that file's instructions inline in the current thread, in order. |
| Several `Task(...)` calls meant to run in parallel | One `spawn_agent` per task, then `wait_agent` for each, then `close_agent` to free slots. Without `spawn_agent`, run them sequentially. |
| `TodoWrite` | `update_plan` |
| `AskUserQuestion(question, options=[...])` | Print the question and the options as a numbered plain-text list, then stop and wait for the user's typed reply. Map the reply back to an option. |
| `Read` / `Write` / `Edit` / `Bash` | Your native file and shell tools |

## Capability Detection

If `spawn_agent` is in your toolset, use the parallel path with isolated
subagents. If not, use the sequential path inline in the current thread. Both
paths produce the same artifacts in the same locations. To enable the parallel
path, add this to `~/.codex/config.toml`:

```toml
[features]
multi_agent = true
```

## Agent Resolution

`subagent_type` values such as `css-reviewer` map to files via
`~/.codex/css/agents/index.json` (`{ "css-reviewer": "agents/reviewer.md", ... }`).
Load the file's text and use it as the specialist's prompt or instructions. The
agent files contain no frontmatter, only body text.

## Model

Codex runs a single session model. The Claude per-agent `model:` tiering
(opus/sonnet/haiku) does not exist here and is not replicated; those frontmatter
keys were stripped at install time. There is no per-task model switching and
therefore no model-based cost tiering.

## Worktree / Finish Environment Detection

Before creating a worktree (`/css-execute`) or pushing/PR (`/css-pr`), detect
the environment with read-only git:

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
BRANCH=$(git branch --show-current)
```

- `GIT_DIR != GIT_COMMON`: already in a linked worktree; skip worktree creation.
- `BRANCH` empty: detached HEAD or sandbox; cannot branch, push, or create a PR;
  use handoff.

## PR / Finish

If `gh` is present, authenticated, and network is available, create the PR as
the body instructs. Otherwise emit a handoff payload with the suggested branch
name, commit message, and PR body for the user to apply via their host UI or
local checkout.

## State

CSS session state lives at `<project>/.claude/css/` and is shared with Claude
Code. Read and write there so a session started in either tool resumes in the
other. Do not relocate it.
