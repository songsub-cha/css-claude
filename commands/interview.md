---
description: Brainstorm an idea into a spec via superpowers:brainstorming (CSS pipeline stage 1)
argument-hint: "[--session <name>] <idea>"
---

# /css:interview

Run a deep, Socratic brainstorming session to turn an idea into a CSS spec. Wraps `superpowers:brainstorming`.

## Steps

1. **Parse arguments**: extract `--session` if present; the remainder is the idea text.

2. **Resolve session**:
   - If `--session <name>` provided and `<project>/.claude/css/sessions/<name>.json` exists → resume.
   - Else generate a new kebab-case slug from the idea (e.g. "JWT auth middleware" → `jwt-auth-middleware`). If the generated slug collides with an existing session file, append a numeric suffix.
   - Initialize `<project>/.claude/css/sessions/<slug>.json` if new, or load it if resuming.
   - New sessions MUST start with `kind:"epic"` and `single_phase:false` so the first plan is a skeleton eligible for `/css:phase`. Do not add these fields while merely resuming a kind-less legacy session; legacy sessions retain the detailed single-session compatibility path.
   - **Capture repo metadata** (whenever the fields are absent — new sessions and resumed legacy sessions alike):
     - `repo_root = git -C <project> rev-parse --show-toplevel`
     - `repo_name = basename(repo_root)`
     - `base_branch = git -C <project> rev-parse --abbrev-ref HEAD` (fallback `main` when detached or not a git repo) — worktree creation and the PR base default to this later.
     - Write to session JSON: `session.repo_root`, `session.repo_name`, `session.base_branch`.
     - If `git rev-parse` fails (not a git repo), use `repo_root = <project>`, `repo_name = basename(<project>)` and continue.
   - **Load pipeline config** (when `session.config` is absent): deep-merge the user config `~/.claude/css/config.json` (if present) over the bundled `config/default-config.json` (under the plugin dir in plugin mode, `~/.claude/css/` in script mode). If neither is readable, use the documented defaults: `verify.coverage_threshold` 85, `review.max_loopback_attempts` 2, `verify.max_loopback_attempts` 3, `execute.tdd_self_heal_max` 2. Store the merged object as `session.config` and initialize `session.retries = {review: 0, verify: 0}` — downstream stages read both.
   - Update `<project>/.claude/css/sessions/_active.json` with `{"latest_slug": "<slug>", "active_epic": "<slug>", "active_phase": null}` (a new session is always an Epic at this point, so `active_epic` is itself).
   - Acquire the interview lock: `<project>/.claude/css/locks/{slug}-interview.lock` with `{acquired_at}` (stale after 60 min → replace with a note; a fresh lock from another run → abort with guidance).

3. **Verify superpowers is enabled**: read `~/.claude/settings.json`. If `enabledPlugins["superpowers@claude-plugins-official"]` is not true, abort with: "CSS requires the superpowers plugin. Enable via /plugin and retry."

4. **Echo header**: print `[css:interview @ slug={slug}]` on the first line of the response.

5. **Invoke brainstorming**:
   ```
   Skill("superpowers:brainstorming")
   ```
   Pass the idea text as the user's initial request inside the invoked skill's context. **Important override**: when brainstorming reaches its terminal "Invoke writing-plans skill" step, do NOT auto-invoke writing-plans. CSS calls `/css:plan` as a separate stage to keep each command independently runnable. Tell brainstorming: "Stop after the user-approves-spec gate; CSS will continue from there."

   **Questioning depth — exhaustion over count**: instruct brainstorming to keep probing until the tacit knowledge behind the idea is exhausted — never until a question quota is met. Operational stop test: maintain a running spec outline (purpose/users, scope in/out, behavior scenarios, edge cases, error handling, integrations & constraints, non-functional needs, acceptance criteria). While any section would be filled by an assumption the user has not confirmed, that section generates the next question. End the interview only when (a) every section is user-confirmed or explicitly N/A, and (b) a final sweep question ("anything we haven't covered?") surfaces nothing new. Never pad with filler questions; never stop while an answer could still change the spec.

6. **On brainstorming completion**:
   - Locate the spec file written by brainstorming (typically `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`).
   - Update session file: `phases.interview.status = "completed"`, `phases.interview.artifact = "<spec path>"`, `phases.interview.completed_at = <ISO timestamp>`.
   - Refresh `_active.json`.

7. **Release lock** and announce next step:
   "Spec 작성 완료: `<spec path>`. 다음 단계: `/css:plan` 또는 `/css:ship --session <slug>`로 진행."
   Final line (its own line, exact prefix): `ARTIFACT=<spec path>`.

<self_check>
- [ ] Artifact written by brainstorming (spec markdown file exists)
- [ ] Interview ended by exhaustion: every spec-outline section user-confirmed or explicitly N/A
- [ ] session file (sessions/{slug}.json) phase status updated to completed
- [ ] _active.json.latest_slug updated
- [ ] Final line is `ARTIFACT=<spec path>`
- [ ] No policy violations
</self_check>

$ARGUMENTS
