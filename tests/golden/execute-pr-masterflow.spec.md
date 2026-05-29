# Golden Test: execute-pr-masterflow (T2.5)

Asserts that `commands/execute.md` and `commands/pr.md` contain master_flow gate-state guards.

```bash
# RED: these must all return 0 before implementation
grep -c "gate2_pre_execute.state" commands/execute.md   # expect 0 pre-impl
grep -c "gate3_pre_pr.state" commands/pr.md             # expect 0 pre-impl
```

## Acceptance criteria

- `grep -c "gate2_pre_execute.state" commands/execute.md` >= 1
- `grep -c "gate3_pre_pr.state" commands/pr.md` >= 1
