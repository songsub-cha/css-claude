# Golden Test: ship-github-sync

Asserts that `commands/ship.md` mirrors the pipeline to the GitHub issue + Projects board.

```bash
grep -c "GHS init-issue" commands/ship.md
grep -c "GitHub stage sync" commands/ship.md
```

## Acceptance criteria

- `grep -c "GHS init-issue" commands/ship.md` >= 1
- `grep -c "GitHub stage sync" commands/ship.md` >= 2
- `grep -c "GHS pr-link" commands/ship.md` >= 1
- `grep -c "GHS finalize" commands/ship.md` >= 1
- `grep -c "GHS link-child" commands/ship.md` >= 1
- `grep -c "GHS adr" commands/ship.md` >= 1
