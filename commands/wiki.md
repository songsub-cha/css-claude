---
description: Curate docs/project/ living docs (feature SoT, architecture, schema, ops, ADRs) and mirror them to the GitHub Wiki
argument-hint: "[--init] [--no-publish]"
---

# /css:wiki

Maintain `docs/project/` as the **current-state** documentation of this repository — the
projection that per-slug snapshots and issue threads never give you — and optionally mirror
it to the GitHub Wiki. Session-independent: works on any git repo, whether or not the changes
went through the CSS pipeline. Reads session JSONs but never writes them and never touches
`_active.json`.

## Steps

1. Parse `--init` (force full rebuild) and `--no-publish` (skip the Wiki mirror). Preflight:
   require a git repo with at least one commit. If on a non-default branch or the tree is
   dirty, warn and continue — the docs commit is scoped to `docs/project/` so unrelated
   changes are never swept in.
2. Acquire the lock `locks/_project-wiki.lock` (stale after 60 min → replace with a note; a
   fresh lock from another run → abort with guidance). Release it on every exit path,
   including cancel and errors.
3. Resolve the sync baseline: read the `<!-- css:last-synced: <sha> ... -->` marker from
   `docs/project/README.md`. Marker or file missing, or `--init` given → **bootstrap** mode;
   otherwise **incremental** from that SHA. Record `head_sha = git rev-parse HEAD` (short
   form for messages) — the curator stamps this into every touched page.
4. Harvest the input bundle. Define the GHS helper first and re-define it in every Bash
   invocation that uses it (shell state does not persist):
   `CSS_PLUGIN_DIR="${CLAUDE_PLUGIN_ROOT}"; CSS_PLUGIN_DIR="${CSS_PLUGIN_DIR:-$HOME/.claude/css}"; GHS() { bash "${CSS_LIB:-$CSS_PLUGIN_DIR/lib}/gh_sync.sh" "$@"; }`
   Never export the install dir as `CSS_ROOT` (gh_sync.sh reads `CSS_ROOT` as the project
   root). Always run `GHS` from the project root.
   - Incremental: `git diff --name-status <last_sha>..HEAD`, `git log --oneline <last_sha>..HEAD`,
     and the `docs/<slug>/` folders touched in that range.
   - Bootstrap: full tree listing (respecting .gitignore), all `docs/<slug>/` folders, and ADR
     backfill — for each `<project>/.claude/css/sessions/*.json` except `_active.json`, run
     `GHS adr-list --session <slug>` and collect the bodies (gh unavailable → fall back to the
     `github.adrs[]` titles in the session JSONs).
   - Both modes: schema-ish files present in the scope (migrations/, `*.sql`, model/entity files).
   - Oversized incremental diff (more than ~200 changed files): do not feed a partial view —
     recommend `/css:wiki --init`, release the lock, and abort cleanly.
5. Dispatch `css-doc-curator` with: mode, head_sha, the harvest above, and the docs root
   `docs/project/`. The curator edits pages in place, preserves hand edits on living pages,
   and returns a per-page change summary. It never commits.
6. Approval gate — show the per-page summary plus `git diff --stat docs/project/`, then
   AskUserQuestion: [승인 / 페이지 제외 / 취소].
   - 페이지 제외 → revert the excluded paths (`git checkout -- <path>`; delete newly created
     files), re-show the remaining summary, ask again.
   - 취소 → revert all `docs/project/` changes, release the lock, exit 0.
7. Commit exactly the docs scope: `git add docs/project/` then
   `git commit -m "docs(project): sync @ <short-sha>"`.
8. Wiki mirror (skip when `--no-publish`): `GHS wiki-publish --sha <short-sha>`. The helper
   skips itself with one warning line when gh is unauthenticated, the repo has no remote, the
   Wiki is disabled (private repo on the Free plan), or the wiki repo is uninitialized — the
   command still succeeds.
9. Report: pages changed, commit hash, whether the Wiki was published, and the new baseline
   SHA now recorded in the Home footer.

<self_check>
- [ ] Baseline came from the Home footer marker (or bootstrap/--init) — no state files used
- [ ] Curator wrote only under docs/project/; no session JSON or _active.json was modified
- [ ] Gate shown; excluded pages actually reverted before the commit
- [ ] Commit contains docs/project/ paths only
- [ ] wiki-publish skipped gracefully when unavailable; lock released on every exit path
</self_check>

$ARGUMENTS
