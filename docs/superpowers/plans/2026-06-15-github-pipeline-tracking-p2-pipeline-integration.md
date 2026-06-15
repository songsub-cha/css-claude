# GitHub Pipeline Tracking — P2: Pipeline Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the P1 `gh_sync` helper into `commands/ship.md` (and `pr.md`, `phase.md`, `agents/pr-creator.md`, `config/default-config.json`) so `/css:ship` creates a GitHub issue, mirrors each stage, drives gates via issue replies, and links the PR.

**Architecture:** `ship.md` is the sole orchestrator of GitHub sync. At session start it calls `gh_sync init-issue`; around each stage it calls `set-state` (label = current stage) then `comment` (summary, or full doc for interview/plan/document); at Gate 2/3 it calls `gate-open` + (on the "remote" path) `gate-wait` and interprets the reply, then `gate-close`; after PR creation it calls `pr-link`; at the end `finalize`; for multi-Phase Epics it calls `link-child`. Every call is guarded so a non-GitHub repo falls back to today's terminal-only behavior. Stage commands stay unchanged (no double-posting). Verification is grep-based golden specs (repo convention).

**Tech Stack:** Markdown command/agent prompts; `bash ~/.claude/css/lib/gh_sync.sh` (P1); JSON config; golden `.spec.md` grep tests.

---

## Depends on / contracts

- **P1 must be merged/available**: `lib/gh_sync.sh` installed to `~/.claude/css/lib/gh_sync.sh` (P3 updates the installer; until then, dogfooding uses the repo copy via `"$CSS_LIB/gh_sync.sh"` where `CSS_LIB` defaults to `$HOME/.claude/css/lib`).
- **Helper invocation convention** (used verbatim in every ship.md step):
  `bash "${CSS_LIB:-$HOME/.claude/css/lib}/gh_sync.sh" <subcommand> --session <slug> [args]`
- **Guard**: ship.md computes `gh_on = (bash gh_sync.sh enabled --session <slug>) == "1"` once after init and only runs sync calls when `gh_on`. When `!gh_on`, the existing terminal-only gates run unchanged.
- **Reply interpretation** (Gate 2/3 remote path): Claude reads the raw reply text returned by `gate-wait` and maps free-form/multilingual intent → `approve` | `draft` (Gate 3 only) | `cancel`. Ambiguous → post a clarifying issue comment and re-poll.

### File structure (P2)

- Modify: `config/default-config.json` (add `github` block).
- Modify: `commands/ship.md` (init/finalize, per-stage sync, Gate 2/3 rewrite, pr-link, link-child, drop dashboard branches).
- Modify: `commands/pr.md`, `agents/pr-creator.md` (`Closes #`, pr-link note).
- Modify: `commands/phase.md` (link-child on child creation).
- Modify: `tests/golden/ship-gate2-crosspath.spec.md`, `tests/golden/ship-gate3-crosspath.spec.md` (assert new flow).
- Create: `tests/golden/ship-github-sync.spec.md` (assert init/comment/set-state/pr-link/finalize wiring).

> Not in P2 (P3): deleting `dashboard/`, removing `interview.md`'s `projects.json` block, installer/README/uninstall updates, deleting dashboard golden specs.

---

## Task 1: Config — add `github` block

**Files:** Modify `config/default-config.json`

- [ ] **Step 1: Add the block** — insert before the closing `}` (after the `pr` block):

```json
  "pr": {
    "default_base_branch": null,
    "default_draft": false
  },
  "github": {
    "tracking_enabled": true,
    "project_owner": null,
    "project_number": null,
    "mention_user": null,
    "auto_close_issue": true,
    "poll_interval_sec": 20
  }
```

- [ ] **Step 2: Verify JSON validity**

Run: `jq . config/default-config.json >/dev/null && echo OK`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add config/default-config.json
git commit -m "feat(css): add github tracking config block"
```

---

## Task 2: ship.md — issue init + finalize

**Files:** Modify `commands/ship.md`

- [ ] **Step 1: Extend step 2 ("Resolve or initialize session")** — append a sub-bullet after `Set session.master_flow = true.`:

```markdown
   - **GitHub tracking init**: define `GHS() { bash "${CSS_LIB:-$HOME/.claude/css/lib}/gh_sync.sh" "$@"; }`.
     Set `gh_on = ("$(GHS enabled --session <slug>)" == "1")`. If `gh_on`, run `GHS init-issue --session <slug>`
     (idempotent — creates the issue + adds it to the user Projects board, or reuses the stored issue on resume).
     Record nothing extra in the session beyond what the helper writes (`session.github`).
```

- [ ] **Step 2: Extend step 14 ("Finalize")** — add before printing the summary:

```markdown
   - If `gh_on`, run `GHS finalize --session <slug>` (label `css:done` + board `Done`).
```

- [ ] **Step 3: Verify wiring**

Run: `grep -c "GHS init-issue" commands/ship.md; grep -c "GHS finalize" commands/ship.md`
Expected: each `>= 1`

- [ ] **Step 4: Commit**

```bash
git add commands/ship.md
git commit -m "feat(css): ship.md creates + finalizes the tracking issue"
```

---

## Task 3: ship.md — per-stage label + comment at boundaries

**Files:** Modify `commands/ship.md`

- [ ] **Step 1: Add a "GitHub stage sync" convention block** after step 2 (so every stage step can reference it):

```markdown
### GitHub stage sync (when `gh_on`)

Wrap every stage invocation below:
- **Before** invoking `/css:<stage>`: `GHS set-state --session <slug> --state <stage>` (issue label → `css:<stage>`, board Status → matching column).
- **After** it completes: `GHS comment --session <slug> --stage <stage>`.
  - `interview` / `plan` / `document` → the helper embeds the **full** artifact document (`session.phases.<stage>.artifact`) in a collapsible block (chunked if it exceeds GitHub's comment limit).
  - all other stages → a one-line summary built from `session.phases.<stage>`.

These run only when `gh_on`; otherwise they are skipped and the pipeline behaves exactly as before.
```

- [ ] **Step 2: Annotate each stage step** — append `(GitHub: set-state before, comment after — see "GitHub stage sync")` to steps 4 (interview), 5 (plan), 6 (review), 8 (execute), 9 (verify), 10 (document). Example for step 4:

```markdown
4. **Stage 1 — interview**:
   - Invoke `/css:interview <idea>` (or resume) inheriting the slug.
   - Gate 1 is implicit: brainstorming's own "user reviews spec" step.
   - GitHub: `set-state --state interview` before, `comment --stage interview` (full spec doc) after — see "GitHub stage sync".
```

- [ ] **Step 3: Verify**

Run: `grep -c "GitHub stage sync" commands/ship.md`
Expected: `>= 2` (the heading + at least one reference)

- [ ] **Step 4: Commit**

```bash
git add commands/ship.md
git commit -m "feat(css): ship.md mirrors each stage to the issue (label + comment)"
```

---

## Task 4: ship.md — Gate 2 rewrite (GitHub flow)

**Files:** Modify `commands/ship.md`

- [ ] **Step 1: Replace the entire step-7 fenced pseudo-code block** (the one containing `CSS_DASHBOARD_RESUME` and `Wait for dashboard`) with:

````markdown
7. **Gate 2 — pre-execute (cross-path)** *(single-Phase / legacy path)*:

   ```
   gate  = session.gates.gate2_pre_execute
   if gate and gate.state == "approved": proceed to step 8; return

   banner = "Plan 검증 완료. worktree 생성 후 execute 시작."
   if gh_on:
       GHS gate-open --session <slug> --gate 2          # @mention + css:awaiting-approval
       options = ["Yes (여기서 승인)", "원격(이슈)에서 답변 대기", "Cancel"]
   else:
       options = ["Yes", "Cancel"]
   answer = AskUserQuestion(banner, options)

   if answer startswith "Yes":
       decision = "approve"; source = "terminal_ask"
   elif answer startswith "원격":
       # inline poll — no servers; each call returns within ~9 min, re-poll until a human replies
       loop:
           reply = GHS gate-wait --session <slug> --gate 2 --timeout 540
           if reply is non-empty:
               interpret reply → decision in {approve, cancel}   # free-form/Korean OK
               if ambiguous: GHS comment ... "approve/cancel 중 무엇인가요?"; continue
               break
           else:
               inform user "이슈 #<n> 답변 대기 중 (9분째)"; continue
       source = "issue_reply"
   else:
       decision = "cancel"; source = "terminal_ask"

   if decision == "approve":
       session.gates.gate2_pre_execute = {state:"approved", source:source, reached_at: gate.reached_at or now(), approved_at: now(), approved_by: source}
       save_session()
       if gh_on: GHS gate-close --session <slug> --gate 2 --decision approve --source <source>
       proceed to step 8
   else:
       if gh_on: GHS gate-close --session <slug> --gate 2 --decision cancel --source <source>
       release_lock(); exit 0
   ```
````

- [ ] **Step 2: Verify dashboard removed + GitHub added (Gate 2)**

Run: `grep -c "CSS_DASHBOARD_RESUME" commands/ship.md; grep -c "gate-open --session <slug> --gate 2" commands/ship.md; grep -c "gate-wait --session <slug> --gate 2" commands/ship.md`
Expected: first counts **decrease** (the gate-2 occurrence is gone), the two `GHS` greps `>= 1`.

- [ ] **Step 3: Commit**

```bash
git add commands/ship.md
git commit -m "feat(css): ship.md Gate 2 via issue @mention + inline reply poll"
```

---

## Task 5: ship.md — Gate 3 rewrite (GitHub flow, with draft)

**Files:** Modify `commands/ship.md`

- [ ] **Step 1: Replace the entire step-11 fenced pseudo-code block** (the Gate 3 one containing `CSS_DASHBOARD_RESUME` / `Draft PR (대시보드`) with:

````markdown
11. **Gate 3 — pre-pr (cross-path)** *(single-Phase / legacy path)*:

    ```
    gate = session.gates.gate3_pre_pr
    if gate and gate.state == "approved": proceed to step 12; return

    banner = "구현+문서 완료. 브랜치 'css/<slug>'를 push하고 PR 생성."
    if gh_on:
        GHS gate-open --session <slug> --gate 3          # @mention + css:awaiting-approval
        options = ["Yes (PR 생성)", "Draft PR", "원격(이슈)에서 답변 대기", "Cancel"]
    else:
        options = ["Yes (PR 생성)", "Draft PR", "Cancel"]
    answer = AskUserQuestion(banner, options)

    if answer startswith "Yes":        decision = "approve"; source = "terminal_ask"
    elif answer startswith "Draft":    decision = "draft";   source = "terminal_ask"
    elif answer startswith "원격":
        loop:
            reply = GHS gate-wait --session <slug> --gate 3 --timeout 540
            if reply is non-empty:
                interpret reply → decision in {approve, draft, cancel}
                if ambiguous: GHS comment ... "approve / draft / cancel 중?"; continue
                break
            else:
                inform user "이슈 #<n> 답변 대기 중 (9분째)"; continue
        source = "issue_reply"
    else: decision = "cancel"; source = "terminal_ask"

    if decision in {approve, draft}:
        session.gates.gate3_pre_pr = {state:"approved", source:source, reached_at: gate.reached_at or now(), approved_at: now(), approved_by: source, draft: (decision == "draft")}
        save_session()
        if gh_on: GHS gate-close --session <slug> --gate 3 --decision <decision> --source <source>
        proceed to step 12
    else:
        if gh_on: GHS gate-close --session <slug> --gate 3 --decision cancel --source <source>
        release_lock(); exit 0
    ```
````

- [ ] **Step 2: Verify**

Run: `grep -c "gate-open --session <slug> --gate 3" commands/ship.md; grep -c "CSS_DASHBOARD_RESUME" commands/ship.md`
Expected: first `>= 1`; second `0` (all dashboard resume refs now gone).

- [ ] **Step 3: Commit**

```bash
git add commands/ship.md
git commit -m "feat(css): ship.md Gate 3 via issue reply (with draft option)"
```

---

## Task 6: ship.md — pr-link, link-child, drop remaining dashboard refs

**Files:** Modify `commands/ship.md`

- [ ] **Step 1: Extend step 12 (pr)** — append:

```markdown
   - After `/css:pr` returns the PR URL, if `gh_on`: `GHS pr-link --session <slug> --url <PR URL>` (issue comment + label `css:pr` + board `PR`; the PR body itself carries `Closes #<issue>` — see Task 7).
```

- [ ] **Step 2: Extend step 5b + step 13 (multi-Phase)** — in step 5b after child Phase sessions are created, and in step 13 per child:

```markdown
   - If `gh_on`: for each child Phase, `GHS init-issue --session <child>` then `GHS link-child --epic <epic> --child <child> --index <phase_index> --label "<phase label>"` (adds a checklist row to the Epic issue). Each child's gates/pr use the child slug exactly like the single-Phase path.
```

- [ ] **Step 3: Remove any leftover dashboard references** in prose (e.g., `config.dashboard_enabled`, "대시보드"). Replace conceptually with `gh_on` / "이슈".

Run: `grep -niE "dashboard|CSS_DASHBOARD_RESUME" commands/ship.md`
Expected: no matches (empty output).

- [ ] **Step 4: Verify pr-link + link-child**

Run: `grep -c "GHS pr-link" commands/ship.md; grep -c "GHS link-child" commands/ship.md`
Expected: each `>= 1`

- [ ] **Step 5: Commit**

```bash
git add commands/ship.md
git commit -m "feat(css): ship.md pr-link + Epic link-child; drop dashboard refs"
```

---

## Task 7: pr.md + pr-creator — `Closes #` + pr-link awareness

**Files:** Modify `commands/pr.md`, `agents/pr-creator.md`

- [ ] **Step 1: In `agents/pr-creator.md`**, in the PR-body construction instructions, add a sentence:

```markdown
If the session was started under GitHub tracking (`session.github.issue_number` is set) and `config.github.auto_close_issue != false`, include a `Closes #<issue_number>` line in the PR description body (use `Refs #<issue_number>` when `auto_close_issue == false`). This links the PR to its tracking issue (and auto-closes the issue on merge).
```

- [ ] **Step 2: In `commands/pr.md`**, in the `<task>` prompt passed to the PR creator (step 7 `<inputs>`), add `issue_number: {session.github.issue_number or null}` and `auto_close_issue: {config.github.auto_close_issue, default true}` so the agent has them.

- [ ] **Step 3: Verify**

Run: `grep -c "Closes #" agents/pr-creator.md; grep -c "issue_number" commands/pr.md`
Expected: each `>= 1`

- [ ] **Step 4: Commit**

```bash
git add commands/pr.md agents/pr-creator.md
git commit -m "feat(css): PR body links the tracking issue via Closes #"
```

---

## Task 8: phase.md — link-child on child creation

**Files:** Modify `commands/phase.md`

- [ ] **Step 1: Where child Phase sessions are created**, add a sub-step:

```markdown
- If GitHub tracking is on for the Epic (`<epic>.github.issue_number` set), after creating each child Phase session run:
  `bash "${CSS_LIB:-$HOME/.claude/css/lib}/gh_sync.sh" init-issue --session <child>` then
  `... link-child --epic <epic> --child <child> --index <phase_index> --label "<phase label>"`.
  (Best-effort; skip silently when tracking is off.)
```

- [ ] **Step 2: Verify**

Run: `grep -c "link-child" commands/phase.md`
Expected: `>= 1`

- [ ] **Step 3: Commit**

```bash
git add commands/phase.md
git commit -m "feat(css): phase.md links child Phase issues to the Epic issue"
```

---

## Task 9: ADR hook after review

**Files:** Modify `commands/ship.md`

- [ ] **Step 1: In step 6 (review) / step 5b (epic review)**, append:

```markdown
   - If `gh_on` and the review produced a notable architectural decision or a non-trivial verdict rationale, post it as an ADR:
     `GHS adr --session <slug> --title "<short>" --context "<why>" --decision "<what>" --consequences "<tradeoffs>"`.
     Post at most the decisions that matter (not every finding); the helper numbers them (ADR-1, ADR-2, …) and de-dupes on resume.
```

- [ ] **Step 2: Verify**

Run: `grep -c "GHS adr" commands/ship.md`
Expected: `>= 1`

- [ ] **Step 3: Commit**

```bash
git add commands/ship.md
git commit -m "feat(css): ship.md records review ADRs on the issue"
```

---

## Task 10: Golden specs

**Files:** Modify `tests/golden/ship-gate2-crosspath.spec.md`, `tests/golden/ship-gate3-crosspath.spec.md`; Create `tests/golden/ship-github-sync.spec.md`

- [ ] **Step 1: Rewrite `ship-gate2-crosspath.spec.md`** to assert the new flow:

```markdown
# Golden Test: ship-gate2-crosspath (GitHub)

Asserts `commands/ship.md` drives Gate 2 through the issue, not the dashboard.

## Acceptance criteria

- `grep -c "CSS_DASHBOARD_RESUME" commands/ship.md` == 0
- `grep -c "gate-open --session <slug> --gate 2" commands/ship.md` >= 1
- `grep -c "gate-wait --session <slug> --gate 2" commands/ship.md` >= 1
- `grep -c "gate-close --session <slug> --gate 2" commands/ship.md` >= 1
- `grep -c "원격(이슈)에서 답변" commands/ship.md` >= 1
```

- [ ] **Step 2: Rewrite `ship-gate3-crosspath.spec.md`** analogously (replace `2`→`3`, keep a `draft` assertion):

```markdown
# Golden Test: ship-gate3-crosspath (GitHub)

## Acceptance criteria

- `grep -c "gate-open --session <slug> --gate 3" commands/ship.md` >= 1
- `grep -c "gate-wait --session <slug> --gate 3" commands/ship.md` >= 1
- `grep -c "gate-close --session <slug> --gate 3" commands/ship.md` >= 1
- `grep -c "Draft PR" commands/ship.md` >= 1
```

- [ ] **Step 3: Create `ship-github-sync.spec.md`**:

```markdown
# Golden Test: ship-github-sync

Asserts `commands/ship.md` mirrors the pipeline to the issue + board.

## Acceptance criteria

- `grep -c "GHS init-issue" commands/ship.md` >= 1
- `grep -c "GitHub stage sync" commands/ship.md` >= 2
- `grep -c "GHS pr-link" commands/ship.md` >= 1
- `grep -c "GHS finalize" commands/ship.md` >= 1
- `grep -c "GHS link-child" commands/ship.md` >= 1
- `grep -c "GHS adr" commands/ship.md` >= 1
```

- [ ] **Step 4: Run all three golden specs' criteria**

Run (each acceptance line); example:
```bash
[ "$(grep -c 'CSS_DASHBOARD_RESUME' commands/ship.md)" -eq 0 ] && echo OK1
[ "$(grep -c 'GHS init-issue' commands/ship.md)" -ge 1 ] && echo OK2
[ "$(grep -c 'GHS finalize' commands/ship.md)" -ge 1 ] && echo OK3
```
Expected: `OK1 OK2 OK3` (extend to all criteria).

- [ ] **Step 5: Commit**

```bash
git add tests/golden/ship-gate2-crosspath.spec.md tests/golden/ship-gate3-crosspath.spec.md tests/golden/ship-github-sync.spec.md
git commit -m "test(css): golden specs assert GitHub gate + sync wiring"
```

---

## Self-Review

**Spec coverage (P2 portion of the design doc):**
- §5 issue creation at ship start → Task 2. ✅
- §6 per-stage label + comment (full doc for interview/plan/document) → Task 3 (delegates content rules to P1 `comment`). ✅
- §7 ADR after review → Task 9. ✅
- §8 gates: @mention + terminal-first + remote poll + same-effect close → Tasks 4–5. ✅
- §9 pr-link + Closes # → Tasks 6, 7. ✅
- §10 Epic/Phase link-child → Tasks 6, 8. ✅
- §11.3 graceful fallback → `gh_on` guard gates every call; `!gh_on` path keeps terminal-only options. ✅
- §12 dashboard refs removed from ship.md → Task 6 (interview.md + dir removal is P3). ✅

**Placeholder scan:** no TBD; every step gives the exact insert/replace text + a grep verification. `<slug>` etc. are literal prompt placeholders (ship.md is itself a template), matching the existing golden-spec greps. ✅

**Consistency:** `GHS()` wrapper, `gh_on`, subcommand names, and `--session <slug>` usage match P1's CLI exactly (`enabled/init-issue/comment/set-state/adr/gate-open/gate-wait/gate-close/pr-link/finalize/link-child`). Gate decision values (`approve|draft|cancel`) and `--source` (`terminal_ask|issue_reply`) match P1's `gate-close`. ✅

**Deferred to P3 (correctly):** delete `dashboard/`, remove `interview.md` `projects.json`/`dashboard_enabled` block, delete `tests/golden/{bridge-systemd,dashboard-config,dashboard-scaffold}.spec.md`, installer/README/uninstall updates.
