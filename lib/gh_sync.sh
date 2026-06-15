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

# --- read layer ---------------------------------------------------------------
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

# --- board --------------------------------------------------------------------
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

# --- init-issue ---------------------------------------------------------------
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

# --- comment ------------------------------------------------------------------
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

main() {
  local sub="${1:-}"; shift || true
  case "$sub" in
    enabled)       cmd_enabled "$@" ;;
    init-issue)    cmd_init_issue "$@" ;;
    comment)       cmd_comment "$@" ;;
    __test_status) __test_status "$@" ;;
    -h|--help|"") usage; exit 2 ;;
    *)            usage; die "unknown subcommand: $sub" ;;
  esac
}
main "$@"
