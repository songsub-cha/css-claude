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

test_set_board_status_calls_item_edit() {
  setup
  jq '.github.project_number=7 | .github.project_owner="tester"' "$CSS_CONFIG" > "$CSS_CONFIG.x" && mv "$CSS_CONFIG.x" "$CSS_CONFIG"
  run __test_status PVTI_item Execute
  assert_contains "item-edit field" "$(ghlog)" "project item-edit --id PVTI_item"
  assert_contains "item-edit option" "$(ghlog)" "--single-select-option-id OPT_Execute"
  teardown
}

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
  : > "$GH_LOG"
  local out; out="$(run init-issue --session demo)"
  assert_eq "reuse number" "$out" "42"
  assert_not_contains "no second create" "$(ghlog)" "issue create"
  teardown
}

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
test_set_state_swaps_labels() {
  setup; seed_issue
  run set-state --session demo --state execute
  assert_contains "add label" "$(ghlog)" "--add-label css:execute"
  assert_contains "remove prev" "$(ghlog)" "--remove-label css:review"
  teardown
}
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
test_gate_close_removes_label_and_records() {
  setup; seed_issue
  run gate-close --session demo --gate 2 --decision approve --source issue_reply
  assert_contains "remove gate label" "$(ghlog)" "--remove-label css:awaiting-approval"
  assert_contains "decision comment" "$(ghlog)" "approve"
  teardown
}
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
test_link_child_creates_subissue() {
  setup
  jq '.github={issue_number:42,repo:"owner/repo",adrs:[]}' "$CSS_ROOT/.claude/css/sessions/demo.json" > t && mv t "$CSS_ROOT/.claude/css/sessions/demo.json"
  jq -n '{slug:"demo-p1", github:{issue_number:43}}' > "$CSS_ROOT/.claude/css/sessions/demo-p1.json"
  run link-child --epic demo --child demo-p1 --index 1 --label "first slice"
  assert_contains "fetch child db id" "$(ghlog)" "api repos/owner/repo/issues/43"
  assert_contains "post sub-issue"    "$(ghlog)" "--method POST repos/owner/repo/issues/42/sub_issues"
  assert_contains "send db id"        "$(ghlog)" "sub_issue_id=9943"
  assert_not_contains "no checklist fallback" "$(ghlog)" "Phase 1 — first slice #43"
  teardown
}
test_link_child_subissue_idempotent() {
  setup
  jq '.github={issue_number:42,repo:"owner/repo",adrs:[]}' "$CSS_ROOT/.claude/css/sessions/demo.json" > t && mv t "$CSS_ROOT/.claude/css/sessions/demo.json"
  jq -n '{slug:"demo-p1", github:{issue_number:43}}' > "$CSS_ROOT/.claude/css/sessions/demo-p1.json"
  export FAKE_SUBISSUES='43'        # already nested → no POST
  run link-child --epic demo --child demo-p1 --index 1 --label "first slice"
  assert_not_contains "no second add" "$(ghlog)" "--method POST"
  unset FAKE_SUBISSUES
  teardown
}
test_link_child_appends_checklist() {
  setup
  jq '.github={issue_number:42,adrs:[]}' "$CSS_ROOT/.claude/css/sessions/demo.json" > t && mv t "$CSS_ROOT/.claude/css/sessions/demo.json"
  jq -n '{slug:"demo-p1", github:{issue_number:43}}' > "$CSS_ROOT/.claude/css/sessions/demo-p1.json"
  export FAKE_ISSUE_VIEW='{"body":"Epic body"}'
  export FAKE_ISSUE_ID=''           # sub-issue API can't resolve child id → fall back to checklist
  run link-child --epic demo --child demo-p1 --index 1 --label "first slice"
  assert_contains "child link line" "$(ghlog)" "Phase 1 — first slice #43"
  unset FAKE_ISSUE_ID
  teardown
}

test_init_issue_ensures_labels() {
  setup
  run init-issue --session demo >/dev/null
  assert_contains "label create tracked" "$(ghlog)" "label create css:tracked"
  assert_contains "label create awaiting" "$(ghlog)" "label create css:awaiting-approval"
  teardown
}

test_config_path_resolution() {
  local sb; sb="$(mktemp -d)"
  # explicit override wins
  assert_eq "explicit CSS_CONFIG" \
    "$(CSS_CONFIG="$sb/x.json" bash "$SCRIPT" __test_config_path)" "$sb/x.json"
  # no override, no user config -> bundled default beside the script
  assert_contains "bundled default" \
    "$(CSS_CONFIG= HOME="$sb/home" bash "$SCRIPT" __test_config_path)" \
    "config/default-config.json"
  # user config present -> used
  mkdir -p "$sb/home/.claude/css"; printf '{}' > "$sb/home/.claude/css/config.json"
  assert_eq "user config" \
    "$(CSS_CONFIG= HOME="$sb/home" bash "$SCRIPT" __test_config_path)" \
    "$sb/home/.claude/css/config.json"
  rm -rf "$sb"
}

# --- registry (append new test_* names here) ---
TESTS=( test_usage_exits_2 test_enabled_true test_enabled_off_when_flag_false test_set_board_status_calls_item_edit test_init_issue_creates_and_persists test_init_issue_idempotent test_init_issue_ensures_labels test_comment_summary_review test_comment_full_plan_embeds_doc test_comment_chunks_when_oversized test_set_state_swaps_labels test_adr_numbers_and_persists test_gate_open_mentions_and_labels test_gate_wait_returns_new_reply test_gate_wait_empty_on_timeout test_gate_close_removes_label_and_records test_pr_link_comments_and_sets_pr test_finalize_sets_done test_link_child_creates_subissue test_link_child_subissue_idempotent test_link_child_appends_checklist test_config_path_resolution )
for t in "${TESTS[@]}"; do "$t"; done
printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
[[ "$FAIL" -eq 0 ]]
