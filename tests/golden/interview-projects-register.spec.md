# Golden Test: interview-projects-register (T2.2)

Asserts that `commands/interview.md` contains the projects.json auto-registration block.

```bash
# RED: these must all return 0 before implementation
grep -c "projects.json" commands/interview.md   # expect 0 pre-impl
grep -c "flock" commands/interview.md            # expect 0 pre-impl
grep -c "dashboard_enabled" commands/interview.md # expect 0 pre-impl
```

## Acceptance criteria

- `grep -c "projects.json" commands/interview.md` >= 2
- `grep -c "flock" commands/interview.md` >= 1
- `grep -c "dashboard_enabled" commands/interview.md` >= 1
