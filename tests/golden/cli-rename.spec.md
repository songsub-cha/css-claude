# Golden: CLI rename --slug → --session

For each command file in commands/*.md:
1. `argument-hint` frontmatter must contain `--session <name>` not `--slug <name>`
2. Body text must reference `--session <name>` in all flag examples
3. Internal references to `session.slug` JSON field are preserved as-is
4. File path templates (`sessions/{slug}.json`, `{slug}.lock`, etc.) preserved as-is

Run: `grep -r "\-\-slug" commands/` → must return 0 matches.
Run: `grep -r "\-\-session" commands/` → must return ≥8 matches (one per file).
