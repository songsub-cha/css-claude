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
   - **Capture repo metadata** (NEW):
     - `repo_root = git -C <project> rev-parse --show-toplevel`
     - `repo_name = basename(repo_root)`
     - Write to session JSON: `session.repo_root`, `session.repo_name`.
     - If `git rev-parse` fails (not a git repo), use `repo_root = <project>`, `repo_name = basename(<project>)` and continue.
   - Update `<project>/.claude/css/sessions/_active.json` with `{"latest_slug": "<slug>"}`.
   - Acquire phase lock.

3. **Verify superpowers is enabled**: read `~/.claude/settings.json`. If `enabledPlugins["superpowers@claude-plugins-official"]` is not true, abort with: "CSS requires the superpowers plugin. Enable via /plugin and retry."

4. **Echo header**: print `[css:interview @ slug={slug}]` on the first line of the response.

5. **Invoke brainstorming**:
   ```
   Skill("superpowers:brainstorming")
   ```
   Pass the idea text as the user's initial request inside the invoked skill's context. **Important override**: when brainstorming reaches its terminal "Invoke writing-plans skill" step, do NOT auto-invoke writing-plans. CSS calls `/css:plan` as a separate stage to keep each command independently runnable. Tell brainstorming: "Stop after the user-approves-spec gate; CSS will continue from there."

   **Minimum questioning depth**: instruct brainstorming to ask **at least 10** substantive questions to fully concretize the idea before drafting the spec. Do not shortcut to the spec with fewer — keep probing requirements, scope, edge cases, and design trade-offs until the idea is concrete.

6. **On brainstorming completion**:
   - Locate the spec file written by brainstorming (typically `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`).
   - Update session file: `phases.interview.status = "completed"`, `phases.interview.artifact = "<spec path>"`, `phases.interview.completed_at = <ISO timestamp>`.
   - Refresh `_active.json`.

7. **Release lock** and announce next step:
   "Spec 작성 완료: `<spec path>`. 다음 단계: `/css:plan` 또는 `/css:ship --session <slug>`로 진행."

<self_check>
- [ ] Artifact written by brainstorming (spec markdown file exists)
- [ ] session file (sessions/{slug}.json) phase status updated to completed
- [ ] _active.json.latest_slug updated
- [ ] Final line contains NEXT=plan or ARTIFACT=<spec path>
- [ ] No policy violations
</self_check>

$ARGUMENTS
