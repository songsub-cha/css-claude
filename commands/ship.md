---
description: Master pipeline — runs interview → plan → review → execute → verify → document → pr with three approval gates
argument-hint: "[--session <name>] <idea>"
---

# /css:ship

Run the full CSS pipeline. Three approval gates: Gate 1 is implicit (brainstorming's own user-review step); Gates 2 (pre-execute) and 3 (pre-pr) use AskUserQuestion.

## Steps

1. **Parse arguments**: extract `--session` if present; remainder is the idea.

2. **Resolve or initialize session**:
   - `--session` provided + existing `<project>/.claude/css/sessions/<slug>.json` → AskUserQuestion: "기존 세션 발견 (phase=`<current>`). 어떻게 진행할까요? [Resume / Restart / Cancel]".
   - `--session` provided + no file → init.
   - No `--session` → derive slug from idea (kebab-case, collision-suffixed if needed), init session, update `_active.json`.
   - Set `session.master_flow = true`.
   - A newly initialized session starts with `kind:"epic"` and `single_phase:false` (skeleton plan eligible for `/css:phase`); a kind-less legacy session stays a single-session.
   - **GitHub tracking init**: define `GHS() { bash "${CSS_LIB:-$HOME/.claude/css/lib}/gh_sync.sh" "$@"; }`. Set `gh_on = ("$(GHS enabled --session <slug>)" == "1")`. If `gh_on`, run `GHS init-issue --session <slug>` (idempotent — creates the issue + adds it to the user Projects board, or reuses the stored issue on resume).

3. **Acquire lock**.

### GitHub stage sync (when `gh_on`)

Wrap every stage invocation below:
- **Before** invoking `/css:<stage>`: `GHS set-state --session <slug> --state <stage>` (issue label → `css:<stage>`, board Status → matching column).
- **After** it completes: `GHS comment --session <slug> --stage <stage>`.
  - `interview` / `plan` / `document` → the helper embeds the **full** artifact document (`session.phases.<stage>.artifact`) in a collapsible block (chunked if it exceeds GitHub's comment limit).
  - all other stages → a one-line summary built from `session.phases.<stage>`.

These run only when `gh_on`; otherwise they are skipped and the pipeline behaves exactly as before.

4. **Stage 1 — interview**:
   - Invoke `/css:interview <idea>` (or resume) inheriting the slug.
   - Gate 1 is implicit: brainstorming's own "user reviews spec" step.
   - GitHub: `set-state --state interview` before, `comment --stage interview` (full spec doc) after — see "GitHub stage sync". Apply the same wrap to every stage below.

5. **Stage 2 — plan (skeleton)**:
   - Invoke `/css:plan --session <slug>`.

5b. **Stage 2.5 — phasing**:
   - Invoke `/css:phase --session <slug>` (creates child Phase sessions from the approved manifest).
   - If the Epic is sub-threshold, `/css:phase` sets `single_phase:true` and regenerates a detailed plan for the single session; continue the linear flow (one session, one PR) via steps 6–12.
   - If multi-Phase: run the Epic **architecture review** once (`/css:review --session <epic>`, kind=epic → coarse, no rich-specs), then run the per-child loop in step 13.
   - If `gh_on` and multi-Phase: for each child Phase, `GHS init-issue --session <child>` (its own issue, so each Phase syncs its content independently) then `GHS link-child --epic <epic> --child <child> --index <phase_index> --label "<phase label>"` (nests the Phase issue under the Epic as a native GitHub **sub-issue** — built-in nested list + progress bar; falls back to an Epic checklist row on older GitHub without the sub-issues API).

6. **Stage 3 — review (loop)** *(single-Phase / legacy path)*:
   - Invoke `/css:review --session <slug>`.
   - On `LOOPBACK_TO_PLAN`, the review command itself loops back to plan up to 2 attempts.
   - On `LOOPBACK_TO_INTERVIEW`, ask user to confirm before re-entering interview.
   - On `ESCALATE`, stop and surface options.
   - If `gh_on` and review produced a notable architectural decision or non-trivial verdict rationale, post it: `GHS adr --session <slug> --title "<short>" --context "<why>" --decision "<what>" --consequences "<tradeoffs>"` (post only decisions that matter; the helper numbers them ADR-1, ADR-2, … and de-dupes on resume).
   - *Multi-Phase Epics: the Epic architecture review was already run in step 5b. Skip to step 13 (per-Phase loop).*

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

8. **Stage 4 — execute** *(single-Phase / legacy path)*: invoke `/css:execute --session <slug>`. The `master_flow` flag tells `/css:execute` not to ask Gate 2 again (it inherits the answer from this step).

9. **Stage 5 — verify (loop)** *(single-Phase / legacy path)*:
   - Invoke `/css:verify --session <slug>`.
   - On `LOOPBACK_TO_EXECUTE`, the verify command itself loops back to execute up to 3 attempts.
   - On `ESCALATE`, stop with options.

10. **Stage 6 — document** *(single-Phase / legacy path)*: invoke `/css:document --session <slug>`.

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

12. **Stage 7 — pr** *(single-Phase / legacy path)*: invoke `/css:pr --session <slug>` (with `--draft` if user chose). The `master_flow` flag tells `/css:pr` not to ask Gate 3 again.
    - After `/css:pr` returns the PR URL, if `gh_on`: `GHS pr-link --session <slug> --url <PR URL>` (issue comment + label `css:pr` + board `PR`; the PR body itself carries `Closes #<issue>` — see `pr.md` / `pr-creator`).

13. **Stages plan→pr per Phase** *(multi-Phase Epics)*:
   For each child slug in topological order (by `phase_index`, respecting `depends_on`):
   a. `/css:plan --session <child>` (kind=phase → detailed) → `/css:review --session <child>` (kind=phase → rich-specs for this Phase).
   b. **Gate 2 (per Phase)** — AskUserQuestion: "Phase {idx} '{label}' execute 시작. base=`{base_branch}`. [Yes / Show / Skip / Cancel]".
   c. `/css:execute --session <child>` → `/css:verify --session <child>` → `/css:document --session <child>`.
   d. **Gate 3 (per Phase)** — AskUserQuestion: "Phase {idx} PR 생성 (base=`{base_branch}`). [Yes / Draft / Cancel]".
   e. `/css:pr --session <child> --base <base_branch>`.
   Independent Phases (disjoint `depends_on`) MAY be dispatched in separate sessions for parallel runs.

14. **Finalize**: mark all phases completed.
    - If `gh_on`, run `GHS finalize --session <slug>` (label `css:done` + board `Done`).
    - Release lock, print summary: "Pipeline 완료. PR: `<URL>`. 산출물: `<paths>`."

<self_check>
- [ ] All 7 phases recorded as completed in session
- [ ] Each gate prompt was shown when applicable
- [ ] PR URL captured
- [ ] Lock released
</self_check>

$ARGUMENTS
