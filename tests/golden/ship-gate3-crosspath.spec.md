# Golden Test: ship-gate3-crosspath (T2.4)

Asserts that `commands/ship.md` contains the cross-path Gate 3 branching logic with Draft PR option.

```bash
# RED: these must all return 0 before implementation
grep -c "gate3_pre_pr" commands/ship.md   # expect 0 pre-impl
grep -c "Draft PR" commands/ship.md       # expect 0 pre-impl
```

## Acceptance criteria

- `grep -c "gate3_pre_pr" commands/ship.md` >= 3
- `grep -c "Draft PR" commands/ship.md` >= 1
