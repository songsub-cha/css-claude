# Golden Test: ship-gate2-crosspath (GitHub)

Asserts that `commands/ship.md` drives Gate 2 through the GitHub issue, not the dashboard.

```bash
# These reflect the GitHub-native flow (P2)
grep -c "CSS_DASHBOARD_RESUME" commands/ship.md            # expect 0
grep -c "gate-open --session <slug> --gate 2" commands/ship.md
```

## Acceptance criteria

- `grep -c "CSS_DASHBOARD_RESUME" commands/ship.md` == 0
- `grep -c "gate-open --session <slug> --gate 2" commands/ship.md` >= 1
- `grep -c "gate-wait --session <slug> --gate 2" commands/ship.md` >= 1
- `grep -c "gate-close --session <slug> --gate 2" commands/ship.md` >= 1
- `grep -c "원격(이슈)에서 답변" commands/ship.md` >= 1
