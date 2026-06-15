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

seed_issue() { jq '.github={issue_number:42,project_item_id:"PVTI_item",adrs:[]}' \
  "$CSS_ROOT/.claude/css/sessions/demo.json" > "$CSS_ROOT/.claude/css/sessions/demo.json.x" \
  && mv "$CSS_ROOT/.claude/css/sessions/demo.json.x" "$CSS_ROOT/.claude/css/sessions/demo.json"; }

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
