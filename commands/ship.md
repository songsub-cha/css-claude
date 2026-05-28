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

3. **Acquire lock**.

4. **Stage 1 — interview**:
   - Invoke `/css:interview <idea>` (or resume) inheriting the slug.
   - Gate 1 is implicit: brainstorming's own "user reviews spec" step.

5. **Stage 2 — plan**:
   - Invoke `/css:plan --session <slug>`.

6. **Stage 3 — review (loop)**:
   - Invoke `/css:review --session <slug>`.
   - On `LOOPBACK_TO_PLAN`, the review command itself loops back to plan up to 2 attempts.
   - On `LOOPBACK_TO_INTERVIEW`, ask user to confirm before re-entering interview.
   - On `ESCALATE`, stop and surface options.

7. **Gate 2 — pre-execute** (cross-path):

   ```
   is_resume = ($CSS_DASHBOARD_RESUME == "1")
   gate = session.gates.gate2_pre_execute
   state = gate.state if gate else null

   if state == "approved": proceed to step 8; return

   if not is_resume and config.dashboard_enabled:
       banner = "Plan 검증 완료. worktree '../<repo>-css-<session>' 생성 후 execute 시작."
       if state == "pending": banner += " (대시보드 승인 대기 중 — 여기서 승인해도 됩니다)"
       answer = AskUserQuestion(banner, options=["Yes (여기서 승인)", "Wait for dashboard (대시보드에서 드래그)", "Cancel"])
       if answer == "Yes (여기서 승인)":
           session.gates.gate2_pre_execute = {state:"approved", source:"terminal_ask", reached_at: gate.reached_at or now(), approved_at: now(), approved_by:"terminal"}
           save_session(); proceed to step 8
       elif answer startswith "Wait for dashboard":
           if state != "pending":
               session.gates.gate2_pre_execute = {state:"pending", reached_at: now(), source:null, approved_at:null, approved_by:null}
               save_session()
           release_lock(); exit 0
       else: release_lock(); exit 0
   elif not is_resume and not config.dashboard_enabled:
       answer = AskUserQuestion(banner, options=["Yes", "Cancel"])
       if answer == "Yes":
           session.gates.gate2_pre_execute = {state:"approved", source:"terminal_ask", approved_at:now()}
           save_session(); proceed
       else: release_lock(); exit 0
   else:  # is_resume — daemon-bridge spawned us
       if state != "approved":
           session.gates.gate2_pre_execute = {state:"pending", reached_at:now()}
           save_session()
       release_lock(); exit 0
   ```

8. **Stage 4 — execute**: invoke `/css:execute --session <slug>`. The `master_flow` flag tells `/css:execute` not to ask Gate 2 again (it inherits the answer from this step).

9. **Stage 5 — verify (loop)**:
   - Invoke `/css:verify --session <slug>`.
   - On `LOOPBACK_TO_EXECUTE`, the verify command itself loops back to execute up to 3 attempts.
   - On `ESCALATE`, stop with options.

10. **Stage 6 — document**: invoke `/css:document --session <slug>`.

11. **Gate 3 — pre-pr** (cross-path):

    ```
    is_resume = ($CSS_DASHBOARD_RESUME == "1")
    gate = session.gates.gate3_pre_pr
    state = gate.state if gate else null

    if state == "approved": proceed to step 12; return

    if not is_resume and config.dashboard_enabled:
        banner = "구현 + 문서 완료. 브랜치 'css/<session>'를 origin에 push하고 PR 생성."
        if state == "pending": banner += " (대시보드 승인 대기 중 — 여기서 승인해도 됩니다)"
        answer = AskUserQuestion(banner, options=["Yes (PR 생성)", "Draft PR (대시보드에서 드래그 후 PR draft 모드)", "Cancel"])
        if answer == "Yes (PR 생성)":
            session.gates.gate3_pre_pr = {state:"approved", source:"terminal_ask", reached_at: gate.reached_at or now(), approved_at: now(), approved_by:"terminal"}
            save_session(); proceed to step 12
        elif answer startswith "Draft PR":
            session.gates.gate3_pre_pr = {state:"approved", source:"terminal_ask", reached_at: gate.reached_at or now(), approved_at: now(), approved_by:"terminal", draft: true}
            save_session(); proceed to step 12
        else: release_lock(); exit 0
    elif not is_resume and not config.dashboard_enabled:
        answer = AskUserQuestion(banner, options=["Yes (PR 생성)", "Draft PR", "Cancel"])
        if answer startswith "Yes" or answer startswith "Draft PR":
            session.gates.gate3_pre_pr = {state:"approved", source:"terminal_ask", approved_at:now(), draft: answer startswith "Draft PR"}
            save_session(); proceed
        else: release_lock(); exit 0
    else:  # is_resume — daemon-bridge spawned us
        if state != "approved":
            session.gates.gate3_pre_pr = {state:"pending", reached_at:now()}
            save_session()
        release_lock(); exit 0
    ```

12. **Stage 7 — pr**: invoke `/css:pr --session <slug>` (with `--draft` if user chose). The `master_flow` flag tells `/css:pr` not to ask Gate 3 again.

13. **Finalize**: mark all phases completed, release lock, print summary:
    "Pipeline 완료. PR: `<URL>`. 산출물: `<paths>`."

<self_check>
- [ ] All 7 phases recorded as completed in session
- [ ] Each gate prompt was shown when applicable
- [ ] PR URL captured
- [ ] Lock released
</self_check>

$ARGUMENTS
