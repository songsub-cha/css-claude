# Golden Test: ship-gate3-crosspath (GitHub)

Asserts that `commands/ship.md` drives Gate 3 through the GitHub issue, with a Draft PR option.

```bash
grep -c "gate-open --session <slug> --gate 3" commands/ship.md
grep -c "Draft PR" commands/ship.md
```

## Acceptance criteria

- `grep -c "gate-open --session <slug> --gate 3" commands/ship.md` >= 1
- `grep -c "gate-wait --session <slug> --gate 3" commands/ship.md` >= 1
- `grep -c "gate-close --session <slug> --gate 3" commands/ship.md` >= 1
- `grep -c "Draft PR" commands/ship.md` >= 1
