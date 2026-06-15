# GitHub Pipeline Tracking — P1: `gh_sync` Helper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `lib/gh_sync.sh`, a standalone bash CLI that mirrors CSS pipeline state to GitHub Issues + Projects and reads gate replies, with pure-bash unit tests (mocked `gh`).

**Architecture:** A single bash script with a subcommand dispatch (`init-issue`, `comment`, `set-state`, `adr`, `gate-open/wait/close`, `pr-link`, `finalize`, `link-child`). It reads the CSS session JSON (`<root>/.claude/css/sessions/<slug>.json`) and global config (`~/.claude/css/config.json`) via `jq`, and performs all GitHub side effects via the `gh` CLI. A graceful guard (`gh_enabled`) makes every subcommand a no-op when GitHub tracking is off / unavailable. Tests mock `gh` with a PATH shim that logs invocations and returns canned JSON.

**Tech Stack:** bash (POSIX-ish, Git Bash on Windows), `jq`, `gh` CLI; pure-bash assert tests + a Python `unittest` bridge for CI discovery.

---

## Plan set (whole feature)

This feature ships in three dependency-ordered plans. **This document is P1.**

| Plan | Scope | Depends on |
|---|---|---|
| **P1** (this) | `lib/gh_sync.sh` helper + bash tests | — |
| **P2** | Wire `gh_sync` into `commands/ship.md`, stage commands, `pr.md`, `phase.md`, `agents/pr-creator.md`, `config/default-config.json` | P1 |
| **P3** | Delete `dashboard/`, update `scripts/install.*`/`uninstall.*`, README, golden specs | P2 |

### Whole-feature file map

**New (P1):**
- `lib/gh_sync.sh` — the helper (one file, function-per-subcommand).
- `tests/gh_sync/test_gh_sync.sh` — pure-bash assert suite.
- `tests/gh_sync/fake-gh` — PATH-shim mock for `gh`.
- `tests/gh_sync/fixtures/config.json`, `tests/gh_sync/fixtures/session.json`, `tests/gh_sync/fixtures/doc.md` — fixtures.
- `tools/gh_sync_bridge/__init__.py`, `tools/gh_sync_bridge/test_gh_sync_bridge.py` — runs the bash suite under `unittest`.
- `.gitattributes` — force LF on `lib/*.sh` and `tests/gh_sync/*`.

**Modified (P2):** `commands/ship.md`, `commands/{interview,plan,review,execute,verify,document}.md`, `commands/pr.md`, `commands/phase.md`, `agents/pr-creator.md`, `config/default-config.json`.

**Modified (P3):** `scripts/install.sh`, `scripts/install.ps1`, `scripts/uninstall.sh`, `scripts/uninstall.ps1`, `README.md`, `README.en.md`, `.gitignore`.

**Deleted (P3):** `dashboard/`, `scripts/install-dashboard.sh`, `scripts/uninstall-dashboard.sh`, `config/dashboard-config.example.json`, `tests/golden/{bridge-systemd,dashboard-config,dashboard-scaffold}.spec.md`, untracked `docs/superpowers/plans/2026-05-30-dashboard-epic-phase-view-*.md` + `dashboard-epic-phase-view-p1..p4.md`.

---

## Contracts (used across all P1 tasks — keep names identical)

**Session `github` block** (the only session keys `gh_sync` writes):
```json
"github": {
  "issue_number": 42,
  "issue_url": "https://github.com/owner/repo/issues/42",
  "repo": "owner/repo",
  "project_item_id": "PVTI_xxx",
  "gate2": { "opened_at": "2026-06-15T00:00:00Z" },
  "gate3": { "opened_at": "2026-06-15T00:00:00Z" },
  "adrs": [ { "n": 1, "title": "...", "posted_at": "..." } ]
}
```

**Config `github` block** (`~/.claude/css/config.json`, added in P2; tests supply a fixture):
```json
"github": { "tracking_enabled": true, "project_owner": null, "project_number": null,
            "mention_user": null, "auto_close_issue": true, "poll_interval_sec": 20 }
```

**Env overrides (tests):** `CSS_CONFIG` (config path), `CSS_ROOT` (project root for session lookup), `GH_COMMENT_LIMIT` (chunk threshold), `PATH` (to inject `fake-gh`).

**Board:** a user-level Projects v2 board titled `CSS Pipeline` with a custom single-select field **`CSS Stage`** (options `Interview,Plan,Review,Execute,Verify,Document,PR,Done`). Board updates are **best-effort**: if field/option/project-id resolution fails, log and continue (the label is the primary state signal).

---

## Task 1: Test harness + scaffolding

**Files:**
- Create: `tests/gh_sync/fake-gh`
- Create: `tests/gh_sync/fixtures/config.json`
- Create: `tests/gh_sync/fixtures/session.json`
- Create: `tests/gh_sync/fixtures/doc.md`
- Create: `tests/gh_sync/test_gh_sync.sh`
- Create: `lib/gh_sync.sh`
- Create: `.gitattributes`

- [ ] **Step 1: Write the fake `gh` shim** — `tests/gh_sync/fake-gh`

```bash
#!/usr/bin/env bash
# Mock gh: log every invocation to $GH_LOG, emit canned stdout for read calls.
printf '%s\n' "$*" >> "${GH_LOG:?GH_LOG unset}"
case "$1 $2" in
  "auth status")      exit 0 ;;
  "repo view")        # --json owner,name -q ... OR --json nameWithOwner
                      echo "owner/repo" ;;
  "api user")         echo "tester" ;;
  "issue create")     echo "https://github.com/owner/repo/issues/42" ;;
  "project create")   echo '{"number":7,"id":"PVT_board","url":"u"}' ;;
  "project field-list") echo '{"fields":[{"id":"FLD","name":"CSS Stage","options":[{"id":"OPT_Interview","name":"Interview"},{"id":"OPT_Execute","name":"Execute"},{"id":"OPT_Done","name":"Done"},{"id":"OPT_PR","name":"PR"}]}]}' ;;
  "project view")     echo '{"id":"PVT_board"}' ;;
  "project item-add") echo '{"id":"PVTI_item"}' ;;
  "issue view")       echo "${FAKE_ISSUE_VIEW:-}" ;;
  *)                  : ;;  # comment/edit/item-edit/field-create: log only
esac
exit 0
```

- [ ] **Step 2: Write fixtures**

`tests/gh_sync/fixtures/config.json`:
```json
{ "github": { "tracking_enabled": true, "project_owner": null, "project_number": null, "mention_user": null, "auto_close_issue": true, "poll_interval_sec": 0 } }
```

`tests/gh_sync/fixtures/session.json`:
```json
{
  "slug": "demo", "idea": "demo idea text",
  "phases": {
    "review":  { "verdict": "PASS", "findings": { "critical": 0, "high": 0, "medium": 0, "low": 3 } },
    "execute": { "branch": "css/demo", "commit_count": 12, "test_summary": { "tests": 28, "passed": 28, "coverage_pct": 97 } },
    "verify":  { "verdict": "PASS", "test_summary": { "coverage_pct": 97 } },
    "plan":    { "artifact": "FIXTURE_DOC" }
  }
}
```

`tests/gh_sync/fixtures/doc.md`:
```markdown
# Demo doc
Full plan content line 1.
Full plan content line 2.
```

- [ ] **Step 3: Write the assert harness with the first (failing) test** — `tests/gh_sync/test_gh_sync.sh`

```bash
#!/usr/bin/env bash
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../../lib/gh_sync.sh"
PASS=0; FAIL=0
assert_eq()       { if [[ "$2" == "$3" ]]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); printf 'FAIL %s\n  exp: %q\n  got: %q\n' "$1" "$3" "$2"; fi; }
assert_contains() { if grep -qF -- "$3" <<<"$2"; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); printf 'FAIL %s\n  missing: %q\n  in: %q\n' "$1" "$3" "$2"; fi; }
assert_not_contains(){ if grep -qF -- "$3" <<<"$2"; then FAIL=$((FAIL+1)); printf 'FAIL %s\n  unexpected: %q\n' "$1" "$3"; else PASS=$((PASS+1)); fi; }

# Per-test sandbox: temp root with session + config + fake gh on PATH.
setup() {
  SANDBOX="$(mktemp -d)"
  mkdir -p "$SANDBOX/.claude/css/sessions" "$SANDBOX/bin"
  cp "$HERE/fixtures/session.json" "$SANDBOX/.claude/css/sessions/demo.json"
  cp "$HERE/fixtures/config.json"  "$SANDBOX/config.json"
  cp "$HERE/fixtures/doc.md"       "$SANDBOX/doc.md"
  # point the plan fixture's artifact at the real temp doc
  local t="$SANDBOX/.claude/css/sessions/demo.json"
  jq --arg p "$SANDBOX/doc.md" '.phases.plan.artifact=$p' "$t" > "$t.x" && mv "$t.x" "$t"
  cp "$HERE/fake-gh" "$SANDBOX/bin/gh"; chmod +x "$SANDBOX/bin/gh"
  export GH_LOG="$SANDBOX/gh.log"; : > "$GH_LOG"
  export CSS_CONFIG="$SANDBOX/config.json"
  export CSS_ROOT="$SANDBOX"
  export PATH="$SANDBOX/bin:$PATH"
  unset FAKE_ISSUE_VIEW
}
teardown() { rm -rf "$SANDBOX"; }
run() { bash "$SCRIPT" "$@"; }            # stdout passthrough
ghlog() { cat "$GH_LOG"; }

test_usage_exits_2() {
  setup
  local rc=0; bash "$SCRIPT" >/dev/null 2>&1 || rc=$?
  assert_eq "usage exits 2" "$rc" "2"
  teardown
}

# --- registry (append new test_* names here) ---
TESTS=( test_usage_exits_2 )
for t in "${TESTS[@]}"; do "$t"; done
printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
[[ "$FAIL" -eq 0 ]]
```

- [ ] **Step 4: Run the suite — expect FAIL (no script yet)**

Run: `bash tests/gh_sync/test_gh_sync.sh`
Expected: error/`FAIL usage exits 2` (script missing or no usage).

- [ ] **Step 5: Create `lib/gh_sync.sh` scaffolding**

```bash
#!/usr/bin/env bash
# gh_sync.sh — CSS pipeline <-> GitHub Issues/Projects bridge.
set -euo pipefail
GH_SYNC_VERSION="0.1.0"

log() { printf '[gh_sync] %s\n' "$*" >&2; }
die() { log "ERROR: $*"; exit 1; }

usage() {
  cat >&2 <<'USAGE'
gh_sync.sh <subcommand> [--flag value ...]
  enabled | init-issue | comment | set-state | adr
  gate-open | gate-wait | gate-close | pr-link | finalize | link-child
USAGE
}

declare -A OPT
parse_opts() {
  OPT=()
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --*) OPT["${1#--}"]="${2:-}"; shift 2 ;;
      *)   die "unexpected arg: $1" ;;
    esac
  done
}

main() {
  local sub="${1:-}"; shift || true
  case "$sub" in
    -h|--help|"") usage; exit 2 ;;
    *)            usage; die "unknown subcommand: $sub" ;;
  esac
}
main "$@"
```

- [ ] **Step 6: Write `.gitattributes`**

```gitattributes
lib/*.sh           text eol=lf
tests/gh_sync/*    text eol=lf
```

- [ ] **Step 7: Run the suite — expect PASS**

Run: `bash tests/gh_sync/test_gh_sync.sh`
Expected: `1 passed, 0 failed`

- [ ] **Step 8: Commit**

```bash
git add lib/gh_sync.sh tests/gh_sync .gitattributes
git commit -m "feat(gh_sync): scaffold helper + bash test harness"
```

---

## Task 2: Read layer + `enabled` guard

**Files:** Modify `lib/gh_sync.sh`, `tests/gh_sync/test_gh_sync.sh`

- [ ] **Step 1: Add tests** (append to `test_gh_sync.sh`, and add names to `TESTS=(...)`)

```bash
test_enabled_true() {
  setup
  assert_eq "enabled=1" "$(run enabled --session demo)" "1"
  teardown
}
test_enabled_off_when_flag_false() {
  setup
  jq '.github.tracking_enabled=false' "$CSS_CONFIG" > "$CSS_CONFIG.x" && mv "$CSS_CONFIG.x" "$CSS_CONFIG"
  assert_eq "enabled=0 (flag off)" "$(run enabled --session demo)" "0"
  teardown
}
```
Update registry: `TESTS=( test_usage_exits_2 test_enabled_true test_enabled_off_when_flag_false )`

- [ ] **Step 2: Run — expect FAIL** (`enabled` unknown subcommand)

Run: `bash tests/gh_sync/test_gh_sync.sh`
Expected: 2 new failures.

- [ ] **Step 3: Implement read layer + guard** — add to `lib/gh_sync.sh` above `main()`

```bash
config_path() { printf '%s' "${CSS_CONFIG:-$HOME/.claude/css/config.json}"; }
cfg() { # cfg <jq-filter> <default>
  local p; p="$(config_path)"
  [[ -f "$p" ]] || { printf '%s' "${2:-}"; return; }
  local v; v="$(jq -r "$1 // empty" "$p" 2>/dev/null || true)"
  [[ -n "$v" ]] && printf '%s' "$v" || printf '%s' "${2:-}"
}
session_file() { printf '%s' "${CSS_ROOT:-$PWD}/.claude/css/sessions/$1.json"; }
sess() { jq -r "$2 // empty" "$(session_file "$1")" 2>/dev/null || true; }
sess_set() { # sess_set <slug> <jq-expr>
  local f; f="$(session_file "$1")"; local tmp="$f.tmp.$$"
  jq "$2" "$f" > "$tmp" && mv "$tmp" "$f"
}

gh_enabled() {
  [[ "$(cfg '.github.tracking_enabled' 'false')" == "true" ]] || return 1
  command -v gh >/dev/null 2>&1 || return 1
  gh auth status >/dev/null 2>&1 || return 1
  gh repo view --json nameWithOwner >/dev/null 2>&1 || return 1
  return 0
}
cmd_enabled() { if gh_enabled; then echo 1; else echo 0; fi; }
```

- [ ] **Step 4: Route `enabled` in `main()`** — add before the `-h` case

```bash
    enabled) cmd_enabled "$@" ;;
```

- [ ] **Step 5: Run — expect PASS** (`3 passed, 0 failed`)

Run: `bash tests/gh_sync/test_gh_sync.sh`

- [ ] **Step 6: Commit**

```bash
git add lib/gh_sync.sh tests/gh_sync/test_gh_sync.sh
git commit -m "feat(gh_sync): config/session read layer + enabled guard"
```

---

## Task 3: Board bootstrap + status setter

**Files:** Modify `lib/gh_sync.sh`, `tests/gh_sync/test_gh_sync.sh`

- [ ] **Step 1: Add test** (verifies `set_board_status` issues the right `item-edit`)

```bash
test_set_board_status_calls_item_edit() {
  setup
  # seed board number into config + an item id into session
  jq '.github.project_number=7 | .github.project_owner="tester"' "$CSS_CONFIG" > "$CSS_CONFIG.x" && mv "$CSS_CONFIG.x" "$CSS_CONFIG"
  run __test_status PVTI_item Execute
  assert_contains "item-edit field" "$(ghlog)" "project item-edit --id PVTI_item"
  assert_contains "item-edit option" "$(ghlog)" "--single-select-option-id OPT_Execute"
  teardown
}
```
Registry: add `test_set_board_status_calls_item_edit`.

- [ ] **Step 2: Run — expect FAIL**

Run: `bash tests/gh_sync/test_gh_sync.sh`
Expected: unknown subcommand `__test_status`.

- [ ] **Step 3: Implement board helpers + a test hook** — add to `lib/gh_sync.sh`

```bash
board_owner() {
  local o; o="$(cfg '.github.project_owner' '')"
  [[ -n "$o" ]] || o="$(gh api user -q '.login')"
  printf '%s' "$o"
}
ensure_board() {
  BOARD_OWNER="$(board_owner)"
  BOARD_NUMBER="$(cfg '.github.project_number' '')"
  [[ -n "$BOARD_NUMBER" ]] && return 0
  local out; out="$(gh project create --owner "$BOARD_OWNER" --title 'CSS Pipeline' --format json)"
  BOARD_NUMBER="$(printf '%s' "$out" | jq -r '.number')"
  gh project field-create "$BOARD_NUMBER" --owner "$BOARD_OWNER" --name 'CSS Stage' \
    --data-type SINGLE_SELECT \
    --single-select-options 'Interview,Plan,Review,Execute,Verify,Document,PR,Done' >/dev/null
  local p; p="$(config_path)"; local tmp="$p.tmp.$$"
  jq --argjson n "$BOARD_NUMBER" --arg o "$BOARD_OWNER" \
     '.github.project_number=$n | .github.project_owner=(.github.project_owner // $o)' \
     "$p" > "$tmp" && mv "$tmp" "$p"
}
set_board_status() { # <item_id> <status_name>
  local item="$1" status="$2" owner num fields fid oid pid
  owner="$(board_owner)"; num="$(cfg '.github.project_number' '')"
  [[ -n "$num" ]] || { log "no board number — skip status"; return 0; }
  fields="$(gh project field-list "$num" --owner "$owner" --format json 2>/dev/null || echo '{}')"
  fid="$(printf '%s' "$fields" | jq -r '.fields[]? | select(.name=="CSS Stage") | .id')"
  oid="$(printf '%s' "$fields" | jq -r --arg s "$status" '.fields[]? | select(.name=="CSS Stage") | .options[]? | select(.name==$s) | .id')"
  pid="$(gh project view "$num" --owner "$owner" --format json 2>/dev/null | jq -r '.id // empty')"
  if [[ -z "$fid" || -z "$oid" || -z "$pid" ]]; then log "board ids unresolved — skip status"; return 0; fi
  gh project item-edit --id "$item" --project-id "$pid" --field-id "$fid" --single-select-option-id "$oid" >/dev/null
}
status_name() {
  case "$1" in
    interview) echo Interview ;; plan) echo Plan ;; review) echo Review ;;
    execute) echo Execute ;; verify) echo Verify ;; document) echo Document ;;
    pr) echo PR ;; done) echo Done ;; *) echo Interview ;;
  esac
}
__test_status() { set_board_status "$1" "$2"; }   # test-only hook
```
Route in `main()`: add `__test_status) __test_status "$@" ;;`

- [ ] **Step 4: Run — expect PASS** (`4 passed, 0 failed`)

Run: `bash tests/gh_sync/test_gh_sync.sh`

- [ ] **Step 5: Commit**

```bash
git add lib/gh_sync.sh tests/gh_sync/test_gh_sync.sh
git commit -m "feat(gh_sync): Projects board bootstrap + best-effort status setter"
```

---

## Task 4: `init-issue` (idempotent)

**Files:** Modify `lib/gh_sync.sh`, `tests/gh_sync/test_gh_sync.sh`

- [ ] **Step 1: Add tests**

```bash
test_init_issue_creates_and_persists() {
  setup
  local out; out="$(run init-issue --session demo)"
  assert_eq "prints issue number" "$out" "42"
  assert_contains "create called" "$(ghlog)" "issue create --title [CSS] demo idea text"
  assert_contains "labels" "$(ghlog)" "--label css:tracked --label css:interview"
  assert_contains "item-add" "$(ghlog)" "project item-add"
  local n; n="$(jq -r '.github.issue_number' "$CSS_ROOT/.claude/css/sessions/demo.json")"
  assert_eq "persisted number" "$n" "42"
  teardown
}
test_init_issue_idempotent() {
  setup
  run init-issue --session demo >/dev/null
  : > "$GH_LOG"                     # clear log
  local out; out="$(run init-issue --session demo)"
  assert_eq "reuse number" "$out" "42"
  assert_not_contains "no second create" "$(ghlog)" "issue create"
  teardown
}
```
Registry: add both.

- [ ] **Step 2: Run — expect FAIL** (unknown subcommand `init-issue`)

Run: `bash tests/gh_sync/test_gh_sync.sh`

- [ ] **Step 3: Implement** — add to `lib/gh_sync.sh`

```bash
init_body() { # <slug>
  printf 'Tracked by the CSS pipeline.\n\nIdea: %s\n\n- [ ] interview\n- [ ] plan\n- [ ] review\n- [ ] execute\n- [ ] verify\n- [ ] document\n- [ ] pr\n' "$(sess "$1" '.idea')"
}
cmd_init_issue() {
  parse_opts "$@"; local slug="${OPT[session]}"
  gh_enabled || { log "tracking off — skip init-issue"; return 0; }
  local existing; existing="$(sess "$slug" '.github.issue_number')"
  if [[ -n "$existing" ]]; then echo "$existing"; return 0; fi
  ensure_board
  local idea title url num item repo
  idea="$(sess "$slug" '.idea')"
  title="[CSS] $(printf '%s' "$idea" | tr '\n' ' ' | cut -c1-60)"
  url="$(gh issue create --title "$title" --body "$(init_body "$slug")" --label css:tracked --label css:interview)"
  num="${url##*/}"
  item="$(gh project item-add "$BOARD_NUMBER" --owner "$BOARD_OWNER" --url "$url" --format json | jq -r '.id')"
  repo="$(gh repo view --json nameWithOwner -q '.nameWithOwner' 2>/dev/null || echo '')"
  sess_set "$slug" ".github = {issue_number: ($num|tonumber), issue_url: \"$url\", repo: \"$repo\", project_item_id: \"$item\", adrs: []}"
  set_board_status "$item" Interview
  echo "$num"
}
```
Route: `init-issue) cmd_init_issue "$@" ;;`

> Note: `gh issue create` prints the issue URL to stdout; the trailing path segment is the number. `ensure_board` sets `BOARD_NUMBER`/`BOARD_OWNER`.

- [ ] **Step 4: Run — expect PASS** (`6 passed, 0 failed`)

Run: `bash tests/gh_sync/test_gh_sync.sh`

- [ ] **Step 5: Commit**

```bash
git add lib/gh_sync.sh tests/gh_sync/test_gh_sync.sh
git commit -m "feat(gh_sync): idempotent init-issue (create + board add + persist)"
```

---

## Task 5: `comment` (summary + full-doc + chunking)

**Files:** Modify `lib/gh_sync.sh`, `tests/gh_sync/test_gh_sync.sh`

- [ ] **Step 1: Add tests** (seed an issue number first via a helper)

```bash
seed_issue() { jq '.github={issue_number:42,project_item_id:"PVTI_item",adrs:[]}' \
  "$CSS_ROOT/.claude/css/sessions/demo.json" > "$CSS_ROOT/.claude/css/sessions/demo.json.x" \
  && mv "$CSS_ROOT/.claude/css/sessions/demo.json.x" "$CSS_ROOT/.claude/css/sessions/demo.json"; }

test_comment_summary_review() {
  setup; seed_issue
  run comment --session demo --stage review
  assert_contains "review summary" "$(ghlog)" "verdict=PASS"
  assert_contains "findings" "$(ghlog)" "c0/h0/m0/l3"
  teardown
}
test_comment_full_plan_embeds_doc() {
  setup; seed_issue
  run comment --session demo --stage plan
  assert_contains "details block" "$(ghlog)" "<details>"
  assert_contains "doc content" "$(ghlog)" "Full plan content line 1."
  teardown
}
test_comment_chunks_when_oversized() {
  setup; seed_issue
  GH_COMMENT_LIMIT=20 run comment --session demo --stage plan
  assert_contains "chunk header" "$(ghlog)" "(1/"
  teardown
}
```
Registry: add all three.

- [ ] **Step 2: Run — expect FAIL** (unknown subcommand `comment`)

Run: `bash tests/gh_sync/test_gh_sync.sh`

- [ ] **Step 3: Implement** — add to `lib/gh_sync.sh`

```bash
GH_COMMENT_LIMIT="${GH_COMMENT_LIMIT:-60000}"
summary_body() { # <slug> <stage>
  local slug="$1" stage="$2"
  case "$stage" in
    review)  printf '✅ review 완료 — verdict=%s, findings c%s/h%s/m%s/l%s' \
               "$(sess "$slug" '.phases.review.verdict')" \
               "$(sess "$slug" '.phases.review.findings.critical')" \
               "$(sess "$slug" '.phases.review.findings.high')" \
               "$(sess "$slug" '.phases.review.findings.medium')" \
               "$(sess "$slug" '.phases.review.findings.low')" ;;
    execute) printf '✅ execute 완료 — branch %s, %s commits, tests %s/%s, cov %s%%' \
               "$(sess "$slug" '.phases.execute.branch')" \
               "$(sess "$slug" '.phases.execute.commit_count')" \
               "$(sess "$slug" '.phases.execute.test_summary.passed')" \
               "$(sess "$slug" '.phases.execute.test_summary.tests')" \
               "$(sess "$slug" '.phases.execute.test_summary.coverage_pct')" ;;
    verify)  printf '✅ verify 완료 — verdict=%s, cov %s%%' \
               "$(sess "$slug" '.phases.verify.verdict')" \
               "$(sess "$slug" '.phases.verify.test_summary.coverage_pct')" ;;
    *)       printf '✅ %s 완료' "$stage" ;;
  esac
}
full_doc_body() { # <stage> <path>
  local stage="$1" path="$2"
  if [[ -z "$path" || ! -f "$path" ]]; then printf '✅ %s 완료 (문서 경로 없음)' "$stage"; return; fi
  printf '✅ %s 완료\n\n<details><summary>📄 %s</summary>\n\n```markdown\n%s\n```\n</details>' \
    "$stage" "$path" "$(cat "$path")"
}
post_chunked() { # <num> <body>
  local num="$1" body="$2"
  if [[ "${#body}" -le "$GH_COMMENT_LIMIT" ]]; then gh issue comment "$num" --body "$body" >/dev/null; return; fi
  local total=$(( (${#body} + GH_COMMENT_LIMIT - 1) / GH_COMMENT_LIMIT )) i=1 off=0
  while [[ $off -lt ${#body} ]]; do
    gh issue comment "$num" --body "($i/$total)"$'\n'"${body:off:GH_COMMENT_LIMIT}" >/dev/null
    off=$(( off + GH_COMMENT_LIMIT )); i=$(( i + 1 ))
  done
}
cmd_comment() {
  parse_opts "$@"; local slug="${OPT[session]}" stage="${OPT[stage]}" full="${OPT[full]:-}"
  gh_enabled || return 0
  local num; num="$(sess "$slug" '.github.issue_number')"; [[ -n "$num" ]] || { log "no issue — skip"; return 0; }
  case "$stage" in
    interview|plan|document)
      local path="$full"; [[ -n "$path" ]] || path="$(sess "$slug" ".phases.\"$stage\".artifact")"
      post_chunked "$num" "$(full_doc_body "$stage" "$path")" ;;
    *)
      gh issue comment "$num" --body "$(summary_body "$slug" "$stage")" >/dev/null ;;
  esac
}
```
Route: `comment) cmd_comment "$@" ;;`

- [ ] **Step 4: Run — expect PASS** (`9 passed, 0 failed`)

Run: `bash tests/gh_sync/test_gh_sync.sh`

- [ ] **Step 5: Commit**

```bash
git add lib/gh_sync.sh tests/gh_sync/test_gh_sync.sh
git commit -m "feat(gh_sync): stage comments (summary + full-doc + chunking)"
```

---

## Task 6: `set-state` (label swap + board)

**Files:** Modify `lib/gh_sync.sh`, `tests/gh_sync/test_gh_sync.sh`

- [ ] **Step 1: Add test**

```bash
test_set_state_swaps_labels() {
  setup; seed_issue
  run set-state --session demo --state execute
  assert_contains "add label" "$(ghlog)" "--add-label css:execute"
  assert_contains "remove prev" "$(ghlog)" "--remove-label css:review"
  teardown
}
```
Registry: add it.

- [ ] **Step 2: Run — expect FAIL**

Run: `bash tests/gh_sync/test_gh_sync.sh`

- [ ] **Step 3: Implement** — add to `lib/gh_sync.sh`

```bash
STAGE_LABELS=(interview plan review execute verify document pr done)
cmd_set_state() {
  parse_opts "$@"; local slug="${OPT[session]}" state="${OPT[state]}"
  gh_enabled || return 0
  local num; num="$(sess "$slug" '.github.issue_number')"; [[ -n "$num" ]] || return 0
  local rm=() s
  for s in "${STAGE_LABELS[@]}"; do [[ "$s" == "$state" ]] || rm+=( --remove-label "css:$s" ); done
  gh issue edit "$num" --add-label "css:$state" "${rm[@]}" >/dev/null 2>&1 \
    || gh issue edit "$num" --add-label "css:$state" >/dev/null 2>&1 || true
  local item; item="$(sess "$slug" '.github.project_item_id')"
  [[ -n "$item" ]] && set_board_status "$item" "$(status_name "$state")"
}
```
Route: `set-state) cmd_set_state "$@" ;;`

> `--remove-label` for an absent label can error on some `gh` versions; the `|| add-only` fallback keeps it idempotent.

- [ ] **Step 4: Run — expect PASS** (`10 passed, 0 failed`)

Run: `bash tests/gh_sync/test_gh_sync.sh`

- [ ] **Step 5: Commit**

```bash
git add lib/gh_sync.sh tests/gh_sync/test_gh_sync.sh
git commit -m "feat(gh_sync): set-state label swap + board status lockstep"
```

---

## Task 7: `adr`

**Files:** Modify `lib/gh_sync.sh`, `tests/gh_sync/test_gh_sync.sh`

- [ ] **Step 1: Add test** (number increments, marker persisted)

```bash
test_adr_numbers_and_persists() {
  setup; seed_issue
  run adr --session demo --title T1 --context C --decision D --consequences X
  assert_contains "ADR-1" "$(ghlog)" "ADR-1: T1"
  run adr --session demo --title T2 --context C --decision D --consequences X
  assert_contains "ADR-2" "$(ghlog)" "ADR-2: T2"
  local len; len="$(jq -r '.github.adrs|length' "$CSS_ROOT/.claude/css/sessions/demo.json")"
  assert_eq "2 markers" "$len" "2"
  teardown
}
```
Registry: add it.

- [ ] **Step 2: Run — expect FAIL**

Run: `bash tests/gh_sync/test_gh_sync.sh`

- [ ] **Step 3: Implement** — add to `lib/gh_sync.sh`

```bash
cmd_adr() {
  parse_opts "$@"; local slug="${OPT[session]}"
  gh_enabled || return 0
  local num; num="$(sess "$slug" '.github.issue_number')"; [[ -n "$num" ]] || return 0
  local n; n="$(sess "$slug" '.github.adrs | length')"; [[ -n "$n" ]] || n=0; n=$(( n + 1 ))
  local body
  body="$(printf '### 🏛️ ADR-%s: %s\n- **Context**: %s\n- **Decision**: %s\n- **Consequences**: %s' \
    "$n" "${OPT[title]}" "${OPT[context]}" "${OPT[decision]}" "${OPT[consequences]}")"
  gh issue comment "$num" --body "$body" >/dev/null
  sess_set "$slug" ".github.adrs += [{n:$n, title:\"${OPT[title]}\", posted_at:\"$(date -u +%FT%TZ)\"}]"
}
```
Route: `adr) cmd_adr "$@" ;;`

- [ ] **Step 4: Run — expect PASS** (`11 passed, 0 failed`)

Run: `bash tests/gh_sync/test_gh_sync.sh`

- [ ] **Step 5: Commit**

```bash
git add lib/gh_sync.sh tests/gh_sync/test_gh_sync.sh
git commit -m "feat(gh_sync): ADR comments with incrementing numbers"
```

---

## Task 8: `gate-open` + `gate-wait`

**Files:** Modify `lib/gh_sync.sh`, `tests/gh_sync/test_gh_sync.sh`

- [ ] **Step 1: Add tests**

```bash
test_gate_open_mentions_and_labels() {
  setup; seed_issue
  export FAKE_ISSUE_VIEW='{"comments":[{"createdAt":"2026-06-15T00:00:00Z","body":"gate"}]}'
  run gate-open --session demo --gate 2
  assert_contains "mention" "$(ghlog)" "@tester"
  assert_contains "gate label" "$(ghlog)" "--add-label css:awaiting-approval"
  local at; at="$(jq -r '.github.gate2.opened_at' "$CSS_ROOT/.claude/css/sessions/demo.json")"
  assert_eq "baseline stored" "$at" "2026-06-15T00:00:00Z"
  teardown
}
test_gate_wait_returns_new_reply() {
  setup; seed_issue
  jq '.github.gate2={opened_at:"2026-06-15T00:00:00Z"}' "$CSS_ROOT/.claude/css/sessions/demo.json" > t && mv t "$CSS_ROOT/.claude/css/sessions/demo.json"
  export FAKE_ISSUE_VIEW='{"comments":[{"createdAt":"2026-06-15T00:00:00Z","body":"gate"},{"createdAt":"2026-06-15T00:05:00Z","body":"approve please"}]}'
  local out; out="$(run gate-wait --session demo --gate 2 --timeout 1)"
  assert_eq "reply body" "$out" "approve please"
  teardown
}
test_gate_wait_empty_on_timeout() {
  setup; seed_issue
  jq '.github.gate2={opened_at:"2026-06-15T00:00:00Z"}' "$CSS_ROOT/.claude/css/sessions/demo.json" > t && mv t "$CSS_ROOT/.claude/css/sessions/demo.json"
  export FAKE_ISSUE_VIEW='{"comments":[{"createdAt":"2026-06-15T00:00:00Z","body":"gate"}]}'
  local out; out="$(run gate-wait --session demo --gate 2 --timeout 1)"
  assert_eq "empty output" "$out" ""
  teardown
}
```
Registry: add all three.

- [ ] **Step 2: Run — expect FAIL**

Run: `bash tests/gh_sync/test_gh_sync.sh`

- [ ] **Step 3: Implement** — add to `lib/gh_sync.sh`

```bash
cmd_gate_open() {
  parse_opts "$@"; local slug="${OPT[session]}" gate="${OPT[gate]}"
  gh_enabled || return 0
  local num; num="$(sess "$slug" '.github.issue_number')"; [[ -n "$num" ]] || return 0
  local who; who="$(cfg '.github.mention_user' '')"; [[ -n "$who" ]] || who="$(gh api user -q '.login')"
  local label desc draft=""
  if [[ "$gate" == "2" ]]; then label="pre-execute"; desc="plan 검증 완료. 승인 시 execute 시작."
  else label="pre-pr"; desc="구현+문서 완료. 승인 시 PR 생성."; draft=" / \`draft\`"; fi
  local body
  body="$(printf '@%s ✋ **Gate %s — %s**\n%s\n답글: `approve` / `cancel`%s (자유 문장·한국어 OK).' \
    "$who" "$gate" "$label" "$desc" "$draft")"
  gh issue comment "$num" --body "$body" >/dev/null
  gh issue edit "$num" --add-label css:awaiting-approval >/dev/null 2>&1 || true
  # baseline = the gate comment's own server timestamp (last comment) → wait reads strictly after it
  local base; base="$(gh issue view "$num" --json comments 2>/dev/null | jq -r '.comments[-1].createdAt // empty')"
  [[ -n "$base" ]] || base="$(date -u +%FT%TZ)"
  sess_set "$slug" ".github.gate$gate = {opened_at: \"$base\"}"
}
cmd_gate_wait() {
  parse_opts "$@"; local slug="${OPT[session]}" gate="${OPT[gate]}" timeout="${OPT[timeout]:-540}"
  gh_enabled || return 0
  local num; num="$(sess "$slug" '.github.issue_number')"; [[ -n "$num" ]] || return 0
  local since; since="$(sess "$slug" ".github.gate$gate.opened_at")"
  local interval; interval="$(cfg '.github.poll_interval_sec' '20')"
  local elapsed=0 reply
  while [[ $elapsed -lt $timeout ]]; do
    reply="$(gh issue view "$num" --json comments 2>/dev/null \
      | jq -r --arg s "$since" '[.comments[]? | select(.createdAt > $s)] | .[0].body // empty')"
    if [[ -n "$reply" ]]; then printf '%s\n' "$reply"; return 0; fi
    [[ "$interval" -gt 0 ]] && sleep "$interval"
    elapsed=$(( elapsed + interval + 1 ))
  done
  log "gate-wait: ${timeout}s 무응답 — 아직 대기 중"
  return 0
}
```
Route: `gate-open) cmd_gate_open "$@" ;;` and `gate-wait) cmd_gate_wait "$@" ;;`

> The poll loop's `sleep` lives **inside** a bounded `until`/`while` (≤ `--timeout`), so a single invocation returns within the cap; the caller (ship.md) re-invokes for longer waits. With `poll_interval_sec: 0` (test fixture) the loop runs once and exits immediately.

- [ ] **Step 4: Run — expect PASS** (`14 passed, 0 failed`)

Run: `bash tests/gh_sync/test_gh_sync.sh`

- [ ] **Step 5: Commit**

```bash
git add lib/gh_sync.sh tests/gh_sync/test_gh_sync.sh
git commit -m "feat(gh_sync): gate-open (@mention) + bounded gate-wait poll"
```

---

## Task 9: `gate-close`

**Files:** Modify `lib/gh_sync.sh`, `tests/gh_sync/test_gh_sync.sh`

- [ ] **Step 1: Add test**

```bash
test_gate_close_removes_label_and_records() {
  setup; seed_issue
  run gate-close --session demo --gate 2 --decision approve --source issue_reply
  assert_contains "remove gate label" "$(ghlog)" "--remove-label css:awaiting-approval"
  assert_contains "decision comment" "$(ghlog)" "approve"
  teardown
}
```
Registry: add it.

- [ ] **Step 2: Run — expect FAIL**

Run: `bash tests/gh_sync/test_gh_sync.sh`

- [ ] **Step 3: Implement** — add to `lib/gh_sync.sh`

```bash
cmd_gate_close() {
  parse_opts "$@"; local slug="${OPT[session]}" gate="${OPT[gate]}" decision="${OPT[decision]}" source="${OPT[source]:-terminal_ask}"
  gh_enabled || return 0
  local num; num="$(sess "$slug" '.github.issue_number')"; [[ -n "$num" ]] || return 0
  gh issue edit "$num" --remove-label css:awaiting-approval >/dev/null 2>&1 || true
  local src_ko="터미널"; [[ "$source" == "issue_reply" ]] && src_ko="이슈 답글"
  gh issue comment "$num" --body "$(printf '게이트 %s 결정: **%s** (%s)' "$gate" "$decision" "$src_ko")" >/dev/null
}
```
Route: `gate-close) cmd_gate_close "$@" ;;`

- [ ] **Step 4: Run — expect PASS** (`15 passed, 0 failed`)

Run: `bash tests/gh_sync/test_gh_sync.sh`

- [ ] **Step 5: Commit**

```bash
git add lib/gh_sync.sh tests/gh_sync/test_gh_sync.sh
git commit -m "feat(gh_sync): gate-close (clear label + record decision)"
```

---

## Task 10: `pr-link` + `finalize`

**Files:** Modify `lib/gh_sync.sh`, `tests/gh_sync/test_gh_sync.sh`

- [ ] **Step 1: Add tests**

```bash
test_pr_link_comments_and_sets_pr() {
  setup; seed_issue
  run pr-link --session demo --url https://github.com/owner/repo/pull/9
  assert_contains "pr comment" "$(ghlog)" "PR 생성: https://github.com/owner/repo/pull/9"
  assert_contains "pr label" "$(ghlog)" "--add-label css:pr"
  teardown
}
test_finalize_sets_done() {
  setup; seed_issue
  run finalize --session demo
  assert_contains "done label" "$(ghlog)" "--add-label css:done"
  teardown
}
```
Registry: add both.

- [ ] **Step 2: Run — expect FAIL**

Run: `bash tests/gh_sync/test_gh_sync.sh`

- [ ] **Step 3: Implement** — add to `lib/gh_sync.sh`

```bash
cmd_pr_link() {
  parse_opts "$@"; local slug="${OPT[session]}" url="${OPT[url]}"
  gh_enabled || return 0
  local num; num="$(sess "$slug" '.github.issue_number')"; [[ -n "$num" ]] || return 0
  gh issue comment "$num" --body "$(printf '🔀 PR 생성: %s' "$url")" >/dev/null
  cmd_set_state --session "$slug" --state pr
}
cmd_finalize() {
  parse_opts "$@"; local slug="${OPT[session]}"
  gh_enabled || return 0
  cmd_set_state --session "$slug" --state done
}
```
Route: `pr-link) cmd_pr_link "$@" ;;` and `finalize) cmd_finalize "$@" ;;`

- [ ] **Step 4: Run — expect PASS** (`17 passed, 0 failed`)

Run: `bash tests/gh_sync/test_gh_sync.sh`

- [ ] **Step 5: Commit**

```bash
git add lib/gh_sync.sh tests/gh_sync/test_gh_sync.sh
git commit -m "feat(gh_sync): pr-link + finalize"
```

---

## Task 11: `link-child` + `unittest` bridge + final wiring

**Files:** Modify `lib/gh_sync.sh`, `tests/gh_sync/test_gh_sync.sh`; Create `tools/gh_sync_bridge/__init__.py`, `tools/gh_sync_bridge/test_gh_sync_bridge.py`

- [ ] **Step 1: Add `link-child` test**

```bash
test_link_child_appends_checklist() {
  setup
  # epic + child sessions both with issue numbers
  jq '.github={issue_number:42,adrs:[]}' "$CSS_ROOT/.claude/css/sessions/demo.json" > t && mv t "$CSS_ROOT/.claude/css/sessions/demo.json"
  jq -n '{slug:"demo-p1", github:{issue_number:43}}' > "$CSS_ROOT/.claude/css/sessions/demo-p1.json"
  export FAKE_ISSUE_VIEW='{"body":"Epic body"}'
  run link-child --epic demo --child demo-p1 --index 1 --label "first slice"
  assert_contains "child link line" "$(ghlog)" "Phase 1 — first slice #43"
  teardown
}
```
Registry: add it.

- [ ] **Step 2: Run — expect FAIL**

Run: `bash tests/gh_sync/test_gh_sync.sh`

- [ ] **Step 3: Implement `link-child`** — add to `lib/gh_sync.sh`

```bash
cmd_link_child() {
  parse_opts "$@"; local epic="${OPT[epic]}" child="${OPT[child]}" idx="${OPT[index]}" label="${OPT[label]}"
  gh_enabled || return 0
  local enum cnum; enum="$(sess "$epic" '.github.issue_number')"; cnum="$(sess "$child" '.github.issue_number')"
  [[ -n "$enum" && -n "$cnum" ]] || return 0
  local cur; cur="$(gh issue view "$enum" --json body 2>/dev/null | jq -r '.body // empty')"
  gh issue edit "$enum" --body "$cur"$'\n'"$(printf -- '- [ ] Phase %s — %s #%s' "$idx" "$label" "$cnum")" >/dev/null
}
```
Route: `link-child) cmd_link_child "$@" ;;`

- [ ] **Step 4: Run — expect PASS** (`18 passed, 0 failed`)

Run: `bash tests/gh_sync/test_gh_sync.sh`

- [ ] **Step 5: Add the `unittest` bridge** — `tools/gh_sync_bridge/__init__.py` (empty) and `tools/gh_sync_bridge/test_gh_sync_bridge.py`:

```python
import shutil
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SUITE = REPO / "tests" / "gh_sync" / "test_gh_sync.sh"


class GhSyncBashSuite(unittest.TestCase):
    def test_bash_suite_passes(self):
        bash = shutil.which("bash")
        if bash is None:
            self.skipTest("bash not available")
        if not SUITE.exists():
            self.skipTest("gh_sync bash suite missing")
        proc = subprocess.run(
            [bash, str(SUITE)], cwd=str(REPO),
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 6: Run the bridge under unittest — expect PASS**

Run: `python -m unittest discover -s tools -t tools -v -k gh_sync` (Windows: use the explicit `python.exe`)
Expected: the bash suite runs and passes (or skips if bash missing).

- [ ] **Step 7: Commit**

```bash
git add lib/gh_sync.sh tests/gh_sync/test_gh_sync.sh tools/gh_sync_bridge
git commit -m "feat(gh_sync): link-child + unittest bridge for CI discovery"
```

---

## Self-Review

**Spec coverage (P1 portion of `2026-06-15-github-pipeline-tracking-design.md`):**
- §3.1 helper owns only `github.*` JSON, no NLU → `sess_set` writes only `.github`; reply interpretation deferred to caller (gate-wait returns raw body). ✅
- §4 cross-platform (bash + jq, LF) → `.gitattributes`, no Windows-only calls. ✅
- §5 init-issue (idempotent, board add) → Task 4. ✅
- §6.1 summary vs full-doc (interview/plan/document) + chunking → Task 5. ✅
- §6.2 label swap (one stage label + tracked) → Task 6. ✅
- §6.3 board status lockstep, best-effort → Tasks 3, 6. ✅
- §7 ADR numbering + markers → Task 7. ✅
- §8 gate-open @mention + bounded gate-wait + gate-close → Tasks 8, 9. ✅
- §9 pr-link + finalize → Task 10. ✅
- §10 link-child (Epic checklist) → Task 11. ✅
- §11.3 graceful fallback → `gh_enabled` no-op guard in every cmd. ✅
- §14 pure bash assert + unittest discovery → Task 1 harness + Task 11 bridge. ✅

**Not in P1 (correctly deferred):** config block insertion (P2), command wiring (P2), `Closes #` in PR body (P2), dashboard deletion/install/docs (P3).

**Placeholder scan:** no TBD/TODO; every step has runnable code/commands. ✅

**Name consistency:** `gh_enabled`, `cfg`, `sess`, `sess_set`, `ensure_board`/`BOARD_NUMBER`/`BOARD_OWNER`, `set_board_status`, `status_name`, `summary_body`, `full_doc_body`, `post_chunked`, `STAGE_LABELS`, and `cmd_*` names are used identically across tasks; `cmd_set_state` is reused by `cmd_pr_link`/`cmd_finalize`. ✅
