# Golden Test: interview-repo-capture (T2.1)

Asserts that `commands/interview.md` contains the repo_root / repo_name capture block.

```bash
# RED: these must FAIL (count = 0) before implementation
grep -E "rev-parse --show-toplevel" commands/interview.md && echo PASS || echo FAIL  # must be FAIL pre-impl
```

## Acceptance criteria

- `grep -c "rev-parse --show-toplevel" commands/interview.md` >= 1
- `grep -c "repo_name" commands/interview.md` >= 2
