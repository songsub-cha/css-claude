---
description: Master pipeline - runs interview, plan, phase, review, execute, verify, document, and pr with three approval gates
argument-hint: "[--session <name>] <idea>"
---

# /css:ship

Run the full CSS pipeline while preserving approval gates and Phase dependencies.
All pipeline state and task artifacts live under `<project>/.claude/css/`.

## Flow

1. Resolve or initialize the session, set `master_flow:true`, acquire the master lock, and run `/css:interview`. A newly initialized session starts with `kind:"epic"` and `single_phase:false`; an existing kind-less session remains a legacy single-session.
2. Gate 1 is the interview/spec approval.
3. Run `/css:plan --session <slug>` then `/css:phase --session <slug>`.
4. If `single_phase:true`, `/css:phase` has already expanded the skeleton into a detailed plan. Run rich `/css:review`, Gate 2, execute, verify, document, Gate 3, and PR in the same session.
5. If multi-Phase, run one Epic architecture review. Then process child sessions in dependency order:
   - detailed plan -> rich review -> per-Phase Gate 2 -> execute -> verify -> document -> per-Phase Gate 3 -> PR using the child base_branch.
6. Gate 2 must be approved before execute and Gate 3 before PR. Dashboard resume may persist a pending gate and exit; terminal approval persists the approved state. Child gates are independent.
7. On review or verify loopback, let the stage command enforce retry counters and re-enter the required earlier stage.
8. Finalize only after all required sessions and PRs complete; record artifacts and release locks.

<self_check>
- [ ] Single-Phase path used a detailed plan and Rich Specs
- [ ] Multi-Phase children inherited the parent spec and ran in dependency order
- [ ] Gate 2 preceded every execute; Gate 3 preceded every PR
- [ ] Final summary includes PR and artifact paths
</self_check>

$ARGUMENTS
