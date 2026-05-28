# Golden Test: ship-gate2-crosspath (T2.3)

Asserts that `commands/ship.md` contains the cross-path Gate 2 branching logic.

```bash
# RED: these must all return 0 before implementation
grep -c "CSS_DASHBOARD_RESUME" commands/ship.md  # expect 0 pre-impl
grep -c "Wait for dashboard" commands/ship.md    # expect 0 pre-impl
grep -c "gate2_pre_execute" commands/ship.md     # expect 0 pre-impl
```

## Acceptance criteria

- `grep -c "CSS_DASHBOARD_RESUME" commands/ship.md` >= 1
- `grep -c "Wait for dashboard" commands/ship.md` >= 1
- `grep -c "gate2_pre_execute" commands/ship.md` >= 3
