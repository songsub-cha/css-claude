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
