# /css:wiki 프로젝트 살아있는 문서 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** slug·이슈 단위로 파편화된 기록을 in-repo `docs/project/`의 현재 상태 문서(기능 SoT·아키텍처·스키마·운영·ADR)로 통합하는 `/css:wiki` 커맨드 + `css-doc-curator` 에이전트 + GitHub Wiki 미러를 구현한다.

**Architecture:** 세션 독립 커맨드가 Home 푸터의 `css:last-synced` SHA를 기준점으로 git diff·세션 JSON·이슈 ADR을 수확해 curator 에이전트에 전달하고, 승인 게이트 후 `docs/project/`만 스코프해 커밋한다. Wiki 발행과 ADR 회수는 `lib/gh_sync.sh`의 신규 서브커맨드 2개가 전담한다(gh 불가 시 경고 후 skip — 기존 폴백 철학).

**Tech Stack:** bash + jq + gh CLI (lib), Claude Code command/agent markdown, bash 테스트 하네스(`tests/gh_sync/`), pytest(`tools/agent_registry`).

**Spec:** `docs/superpowers/specs/2026-07-03-project-wiki-design.md` (승인 완료 — 페이지 골격 11종은 spec §4.3이 정본).

## Global Constraints

- `lib/gh_sync.sh`는 bash+jq 외 신규 의존성 금지, LF 라인 엔딩, `set -euo pipefail` 아래에서 안전해야 함.
- gh/Wiki 불가 시 **경고 1줄 + exit 0** (파이프라인 불변 폴백 철학).
- `/css:wiki`는 세션 JSON을 **읽기만** 한다 — 세션 쓰기·`_active.json` 갱신 금지.
- 커밋은 항상 `git add docs/project/`로 스코프. 커밋 메시지 `docs(project): sync @ <short-sha>`.
- 락: `<project>/.claude/css/locks/_project-wiki.lock`, 60분 stale 규칙, 모든 exit 경로에서 해제.
- Wiki 페이지 이름 매핑(spec §5): `Home`, `Architecture`, `Features`, `Features-<x>`, `Data-Schema`, `Data-Migrations`, `Ops-Runbook`, `Ops-Configuration`, `Ops-Troubleshooting`, `ADR-Index`, `ADR-NNNN-<x>`.
- 에이전트 본문에 `oh-my-claudecode:`, `/team`, `document-specialist`, `frontend-engineer`, `consult writer` 문자열 금지 (registry의 forbidden_runtime_refs 검사).
- 에이전트 frontmatter: `css_stages: [wiki]` (review+execute를 포함하지 않으므로 도메인 dispatch 표 요건 미적용 — 의도된 것).
- 작업 브랜치: `css/project-wiki` (Task 1 시작 시 생성).

---

### Task 1: `gh_sync.sh` — `adr-list` 서브커맨드

**Files:**
- Modify: `lib/gh_sync.sh` (usage 문자열, `# --- adr ---` 섹션 뒤, `main()` dispatch)
- Test: `tests/gh_sync/test_gh_sync.sh` (TESTS 레지스트리 포함)

**Interfaces:**
- Consumes: 기존 `gh_enabled`, `sess`, `repo_slug`, fake-gh의 `*/issues/*/comments*` 라우트(`FAKE_ISSUE_COMMENTS`).
- Produces: `bash lib/gh_sync.sh adr-list --session <slug>` — 이슈의 `### 🏛️ ADR-` 코멘트 본문 전문을 stdout에 출력(비ADR 코멘트 제외). gh 불가/이슈 없음 → 빈 출력 + exit 0. Task 5의 `commands/wiki.md`가 bootstrap 백필에 사용.

- [ ] **Step 1: 브랜치 생성**

```bash
git checkout -b css/project-wiki
```

- [ ] **Step 2: 실패하는 테스트 작성**

`tests/gh_sync/test_gh_sync.sh`의 `test_config_path_resolution` 함수 뒤에 추가:

```bash
test_adr_list_prints_only_adr_bodies() {
  setup; seed_issue
  export FAKE_ISSUE_COMMENTS='[{"created_at":"t1","body":"### 🏛️ ADR-1: pick X\n- **Context**: c1"},{"created_at":"t2","body":"not an adr"},{"created_at":"t3","body":"### 🏛️ ADR-2: pick Y\n- **Context**: c2"}]'
  local out; out="$(run adr-list --session demo)"
  assert_contains "adr1 body" "$out" "ADR-1: pick X"
  assert_contains "adr2 body" "$out" "ADR-2: pick Y"
  assert_not_contains "non-adr excluded" "$out" "not an adr"
  unset FAKE_ISSUE_COMMENTS
  teardown
}
test_adr_list_empty_when_tracking_off() {
  setup; seed_issue
  jq '.github.tracking_enabled=false' "$CSS_CONFIG" > "$CSS_CONFIG.x" && mv "$CSS_CONFIG.x" "$CSS_CONFIG"
  local out rc=0; out="$(run adr-list --session demo)" || rc=$?
  assert_eq "exit 0" "$rc" "0"
  assert_eq "empty output" "$out" ""
  teardown
}
```

같은 파일 맨 아래 `TESTS=(` 배열에 두 이름 추가: `test_adr_list_prints_only_adr_bodies test_adr_list_empty_when_tracking_off`

- [ ] **Step 3: 실패 확인**

Run: `bash tests/gh_sync/test_gh_sync.sh`
Expected: `FAIL` ≥ 1 — `unknown subcommand: adr-list` 경로로 adr-list 테스트 실패, 기존 22개는 통과.

- [ ] **Step 4: 구현**

`lib/gh_sync.sh`의 `cmd_adr` 함수 끝(`# --- gates ---` 주석 앞)에 추가:

```bash
# --- adr-list -------------------------------------------------------------
cmd_adr_list() { # print full ADR comment bodies from the issue (bootstrap backfill)
  parse_opts "$@"; local slug="${OPT[session]}"
  gh_enabled || return 0
  local num; num="$(sess "$slug" '.github.issue_number')"; [[ -n "$num" ]] || return 0
  local repo; repo="$(repo_slug "$slug")"; [[ -n "$repo" ]] || return 0
  gh api --paginate "repos/$repo/issues/$num/comments?per_page=100" 2>/dev/null \
    | jq -rs 'flatten | map(select(.body | startswith("### 🏛️ ADR-")) | .body) | join("\n\n")' \
    || true
}
```

주의: `repo_slug`는 파일 하단(link-child 섹션)에 정의되어 있지만 bash는 호출 시점에 해석하므로 위 위치에서 사용 가능(기존 `cmd_gate_open`도 동일 패턴).

`usage()` 히어독의 서브커맨드 목록 갱신:

```
  enabled | init-issue | comment | set-state | adr | adr-list
  gate-open | gate-wait | gate-close | pr-link | finalize | link-child | wiki-publish
```

`main()`의 case에 추가 (`adr)` 라인 뒤):

```bash
    adr-list)      cmd_adr_list "$@" ;;
```

- [ ] **Step 5: 통과 확인**

Run: `bash tests/gh_sync/test_gh_sync.sh`
Expected: `24 passed, 0 failed`

- [ ] **Step 6: Commit**

```bash
git add lib/gh_sync.sh tests/gh_sync/test_gh_sync.sh
git commit -m "feat(gh_sync): add adr-list to harvest ADR comment bodies"
```

---

### Task 2: `gh_sync.sh` — `wiki-publish` 가용성 판단·skip 경로

**Files:**
- Modify: `lib/gh_sync.sh`
- Modify: `tests/gh_sync/fake-gh` (has_wiki 라우트)
- Test: `tests/gh_sync/test_gh_sync.sh`

**Interfaces:**
- Consumes: `gh_enabled`, `log`, fake-gh api 라우팅.
- Produces: `wiki-publish --sha <sha>` 서브커맨드의 뼈대 — skip 경로 3종(docs/project 없음 / Wiki 비활성 / clone 실패)이 모두 **exit 0 + 경고**. 테스트 심 `CSS_WIKI_URL`(설정 시 gh 가용성 검사를 건너뛰고 해당 URL을 wiki 리모트로 사용). Task 3이 발행 본체를 채움.

- [ ] **Step 1: fake-gh에 has_wiki 라우트 추가**

`tests/gh_sync/fake-gh`의 `if [[ "$1" == "api" ]]; then` 블록 내 case에서 `*"--method POST"*` 라인 앞에 추가:

```bash
    *"--jq .has_wiki"*) printf '%s\n' "${FAKE_HAS_WIKI-true}"; exit 0 ;;   # repo wiki flag
```

- [ ] **Step 2: 실패하는 테스트 작성**

`test_gh_sync.sh`에 추가:

```bash
test_wiki_publish_skips_without_docs_dir() {
  setup
  local out rc=0; out="$(run wiki-publish --sha abc1234 2>&1)" || rc=$?
  assert_eq "exit 0 (no docs)" "$rc" "0"
  assert_contains "skip reason" "$out" "docs/project"
  teardown
}
test_wiki_publish_skips_when_wiki_disabled() {
  setup
  mkdir -p "$CSS_ROOT/docs/project"; printf '# home\n' > "$CSS_ROOT/docs/project/README.md"
  export FAKE_HAS_WIKI=false
  local out rc=0; out="$(run wiki-publish --sha abc1234 2>&1)" || rc=$?
  assert_eq "exit 0 (wiki off)" "$rc" "0"
  assert_contains "wiki off reason" "$out" "Wiki"
  unset FAKE_HAS_WIKI
  teardown
}
test_wiki_publish_skips_on_clone_failure() {
  setup
  mkdir -p "$CSS_ROOT/docs/project"; printf '# home\n' > "$CSS_ROOT/docs/project/README.md"
  export CSS_WIKI_URL="$SANDBOX/no-such-remote.wiki.git"
  local out rc=0; out="$(run wiki-publish --sha abc1234 2>&1)" || rc=$?
  assert_eq "exit 0 (clone fail)" "$rc" "0"
  assert_contains "clone fail reason" "$out" "clone"
  unset CSS_WIKI_URL
  teardown
}
```

`TESTS=(` 배열에 세 이름 추가.

- [ ] **Step 3: 실패 확인**

Run: `bash tests/gh_sync/test_gh_sync.sh`
Expected: 신규 3개 FAIL (`unknown subcommand: wiki-publish`), 기존 24개 통과.

- [ ] **Step 4: 구현 (skip 경로만)**

`lib/gh_sync.sh`의 `# --- link-child ...` 섹션 뒤, `main()` 앞에 추가:

```bash
# --- wiki-publish ---------------------------------------------------------
# One-way mirror: docs/project/ -> GitHub Wiki. Never a hard failure — every
# unavailable precondition logs one line and exits 0 (same fallback philosophy
# as the rest of this helper). CSS_WIKI_URL overrides the remote (test seam).
cmd_wiki_publish() {
  parse_opts "$@"; local sha="${OPT[sha]:-HEAD}"
  local src="${CSS_ROOT:-$PWD}/docs/project"
  [[ -d "$src" ]] || { log "wiki-publish: docs/project 없음 — skip"; return 0; }
  local url="${CSS_WIKI_URL:-}" repo=""
  if [[ -z "$url" ]]; then
    gh_enabled || { log "wiki-publish: gh 사용 불가 — skip"; return 0; }
    repo="$(gh repo view --json nameWithOwner -q '.nameWithOwner' 2>/dev/null || echo '')"
    [[ -n "$repo" ]] || { log "wiki-publish: repo 식별 실패 — skip"; return 0; }
    if [[ "$(gh api "repos/$repo" --jq '.has_wiki' 2>/dev/null)" != "true" ]]; then
      log "wiki-publish: 이 repo는 Wiki 비활성(설정 꺼짐 또는 private+Free 요금제) — skip"; return 0
    fi
    url="https://github.com/$repo.wiki.git"
  fi
  local tmp; tmp="$(mktemp -d)"; local wt="$tmp/wiki"
  if ! git clone -q "$url" "$wt" 2>/dev/null; then
    log "wiki-publish: wiki repo clone 실패 — 미초기화 wiki면 웹 UI에서 첫 페이지 생성 후 재실행. skip"
    rm -rf "$tmp"; return 0
  fi
  publish_wiki_tree "$src" "$wt" "$sha"   # Task 3에서 구현
  rm -rf "$tmp"
}
publish_wiki_tree() { :; }   # Task 3에서 대체
```

`main()` case에 추가 (`link-child)` 라인 뒤):

```bash
    wiki-publish)  cmd_wiki_publish "$@" ;;
```

- [ ] **Step 5: 통과 확인**

Run: `bash tests/gh_sync/test_gh_sync.sh`
Expected: `27 passed, 0 failed` (clone-실패 테스트는 `CSS_WIKI_URL`이 없는 경로를 가리키므로 clone 실패 분기 검증)

- [ ] **Step 6: Commit**

```bash
git add lib/gh_sync.sh tests/gh_sync/fake-gh tests/gh_sync/test_gh_sync.sh
git commit -m "feat(gh_sync): wiki-publish availability checks with graceful skips"
```

---

### Task 3: `gh_sync.sh` — `wiki-publish` 발행 본체 (매핑·배너·링크 재작성·사이드바)

**Files:**
- Modify: `lib/gh_sync.sh` (`publish_wiki_tree` placeholder 대체 + 헬퍼 3개)
- Test: `tests/gh_sync/test_gh_sync.sh`

**Interfaces:**
- Consumes: Task 2의 `cmd_wiki_publish` 뼈대(clone된 worktree `wt`, `src`, `sha` 전달), `log`.
- Produces: 완성된 `wiki-publish` — spec §5 이름 매핑, 페이지 상단 DO NOT EDIT 배너, docs/project 내부 상호 링크를 Wiki 페이지명으로 재작성, `_Sidebar.md`(정렬된 페이지 목록)·`_Footer.md`(`mirrored ... @ <sha>`) 생성, 소유 네임스페이스 페이지 삭제 후 재생성(rename-safe), 변경 없으면 push 생략.

- [ ] **Step 1: 실패하는 테스트 작성**

`test_gh_sync.sh`에 헬퍼와 테스트 추가:

```bash
seed_wiki_remote() { # local bare repo standing in for <repo>.wiki.git (already initialized)
  WIKI_REMOTE="$SANDBOX/remote.wiki.git"
  git init -q --bare "$WIKI_REMOTE"
  local w="$SANDBOX/wseed"; git init -q "$w"
  ( cd "$w" && printf 'seed\n' > Home.md && printf 'keep me\n' > Foreign-Page.md \
    && git add -A && git -c user.name=t -c user.email=t@t.t commit -qm seed \
    && git push -q "$WIKI_REMOTE" HEAD:refs/heads/master )
  export CSS_WIKI_URL="$WIKI_REMOTE"
}
seed_project_docs() {
  mkdir -p "$CSS_ROOT/docs/project/features" "$CSS_ROOT/docs/project/data" "$CSS_ROOT/docs/project/decisions"
  cat > "$CSS_ROOT/docs/project/README.md" <<'EOF'
# 데모 프로젝트 문서
[아키텍처](architecture.md) [기능](features/README.md)
<!-- css:last-synced: abc1234 2026-07-03 -->
EOF
  printf '# 아키텍처\n' > "$CSS_ROOT/docs/project/architecture.md"
  printf '# 기능 인덱스\n[auth](auth.md)\n' > "$CSS_ROOT/docs/project/features/README.md"
  printf '# auth\n[스키마](../data/schema.md) [인덱스](README.md)\n' > "$CSS_ROOT/docs/project/features/auth.md"
  printf '# 스키마\n' > "$CSS_ROOT/docs/project/data/schema.md"
  printf '# ADR-0001: X\n' > "$CSS_ROOT/docs/project/decisions/ADR-0001-x.md"
}
assert_file() { if [[ -f "$2" ]]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); printf 'FAIL %s\n  missing file: %s\n' "$1" "$2"; fi; }

test_wiki_publish_maps_pages_and_pushes() {
  setup; seed_wiki_remote; seed_project_docs
  run wiki-publish --sha abc1234
  local chk="$SANDBOX/check"; git clone -q "$WIKI_REMOTE" "$chk"
  assert_file "Home" "$chk/Home.md"
  assert_file "Architecture" "$chk/Architecture.md"
  assert_file "Features index" "$chk/Features.md"
  assert_file "Features-auth" "$chk/Features-auth.md"
  assert_file "Data-Schema" "$chk/Data-Schema.md"
  assert_file "ADR page" "$chk/ADR-0001-x.md"
  assert_contains "banner" "$(cat "$chk/Architecture.md")" "DO NOT EDIT"
  assert_contains "root link"    "$(cat "$chk/Home.md")" "](Architecture)"
  assert_contains "root subdir link" "$(cat "$chk/Home.md")" "](Features)"
  assert_contains "updir link"   "$(cat "$chk/Features-auth.md")" "](Data-Schema)"
  assert_contains "sibling link" "$(cat "$chk/Features-auth.md")" "](Features)"
  assert_contains "sidebar entry" "$(cat "$chk/_Sidebar.md")" "Features-auth"
  assert_contains "footer sha" "$(cat "$chk/_Footer.md")" "abc1234"
  assert_contains "foreign page kept" "$(cat "$chk/Foreign-Page.md")" "keep me"
  unset CSS_WIKI_URL
  teardown
}
test_wiki_publish_noop_when_unchanged() {
  setup; seed_wiki_remote; seed_project_docs
  run wiki-publish --sha abc1234
  local out; out="$(run wiki-publish --sha abc1234 2>&1)"
  assert_contains "no-change skip" "$out" "변경 없음"
  unset CSS_WIKI_URL
  teardown
}
```

`TESTS=(` 배열에 두 이름 추가.

- [ ] **Step 2: 실패 확인**

Run: `bash tests/gh_sync/test_gh_sync.sh`
Expected: 신규 2개 FAIL (placeholder `publish_wiki_tree`가 아무것도 안 쓰므로 페이지 파일 부재), 기존 27개 통과.

- [ ] **Step 3: 구현**

`lib/gh_sync.sh`에서 `publish_wiki_tree() { :; }` placeholder를 다음으로 대체(같은 위치, `cmd_wiki_publish` 앞에 헬퍼들 배치):

```bash
wiki_page_name() { # <relpath under docs/project/> -> wiki filename ('' = unmapped, skip)
  case "$1" in
    README.md)                     echo "Home.md" ;;
    architecture.md)               echo "Architecture.md" ;;
    features/README.md)            echo "Features.md" ;;
    features/*.md)                 echo "Features-$(basename "$1")" ;;
    data/schema.md)                echo "Data-Schema.md" ;;
    data/migrations.md)            echo "Data-Migrations.md" ;;
    operations/runbook.md)         echo "Ops-Runbook.md" ;;
    operations/configuration.md)   echo "Ops-Configuration.md" ;;
    operations/troubleshooting.md) echo "Ops-Troubleshooting.md" ;;
    decisions/README.md)           echo "ADR-Index.md" ;;
    decisions/*.md)                basename "$1" ;;
    *)                             echo "" ;;
  esac
}
rewrite_links() { # <relpath> <infile> — docs/project 내부 상호 링크를 Wiki 페이지명으로
  local rel="$1" f="$2" dir; dir="$(dirname "$rel")"
  local sed_args=() r page base
  for r in "${WIKI_RELS[@]}"; do
    page="$(wiki_page_name "$r")"; [[ -n "$page" ]] || continue
    base="${page%.md}"
    if [[ "$dir" == "." ]]; then
      sed_args+=( -e "s#](${r})#](${base})#g" )
    else
      sed_args+=( -e "s#](../${r})#](${base})#g" )
      [[ "$(dirname "$r")" == "$dir" ]] && sed_args+=( -e "s#]($(basename "$r"))#](${base})#g" )
    fi
  done
  if [[ ${#sed_args[@]} -gt 0 ]]; then sed "${sed_args[@]}" "$f"; else cat "$f"; fi
}
make_sidebar() { # sorted page list — 접두어(ADR-/Data-/Features/Ops-)가 곧 카테고리 그룹
  printf '## 프로젝트 문서\n- [Home](Home)\n'
  local rel page base
  for rel in "${WIKI_RELS[@]}"; do
    page="$(wiki_page_name "$rel")"
    [[ -n "$page" && "$page" != "Home.md" ]] || continue
    base="${page%.md}"
    printf -- '- [%s](%s)\n' "$base" "$base"
  done | sort -u
}
publish_wiki_tree() { # <src> <wiki worktree> <sha>
  local src="$1" wt="$2" sha="$3"
  local banner='> ⚠️ DO NOT EDIT — `docs/project/`에서 미러된 페이지입니다. 수정은 repo에서 하세요.'
  WIKI_RELS=()
  local f rel page
  while IFS= read -r f; do WIKI_RELS+=( "${f#"$src"/}" ); done < <(find "$src" -name '*.md' | sort)
  # 소유 네임스페이스를 지우고 재생성(rename-safe). 그 외 페이지는 보존.
  rm -f "$wt"/Home.md "$wt"/Architecture.md "$wt"/Features*.md "$wt"/Data-*.md \
        "$wt"/Ops-*.md "$wt"/ADR-*.md "$wt"/_Sidebar.md "$wt"/_Footer.md
  for rel in "${WIKI_RELS[@]}"; do
    page="$(wiki_page_name "$rel")"
    [[ -n "$page" ]] || { log "wiki-publish: 매핑 없는 파일 — skip $rel"; continue; }
    { printf '%s\n\n' "$banner"; rewrite_links "$rel" "$src/$rel"; } > "$wt/$page"
  done
  make_sidebar > "$wt/_Sidebar.md"
  printf 'mirrored from `docs/project/` @ %s\n' "$sha" > "$wt/_Footer.md"
  if [[ -z "$(git -C "$wt" status --porcelain)" ]]; then
    log "wiki-publish: 변경 없음 — push 생략"; return 0
  fi
  git -C "$wt" add -A
  git -C "$wt" -c user.name="css-wiki" -c user.email="css-wiki@local" \
    commit -qm "docs: sync from docs/project @ $sha"
  git -C "$wt" push -q origin HEAD
  log "wiki-publish: 발행 완료 @ $sha"
}
```

그리고 Task 2에서 넣은 `publish_wiki_tree "$src" "$wt" "$sha"   # Task 3에서 구현` 호출의 주석을 제거한다.

- [ ] **Step 4: 통과 확인**

Run: `bash tests/gh_sync/test_gh_sync.sh`
Expected: `29 passed, 0 failed`

- [ ] **Step 5: Commit**

```bash
git add lib/gh_sync.sh tests/gh_sync/test_gh_sync.sh
git commit -m "feat(gh_sync): wiki-publish page mapping, banner, link rewrite, sidebar"
```

---

### Task 4: `agents/doc-curator.md` — css-doc-curator 에이전트

**Files:**
- Create: `agents/doc-curator.md`
- Create: `tests/golden/wiki-project-docs.spec.md` (agent + command 기준 — command 항목은 Task 5에서 충족)

**Interfaces:**
- Consumes: spec §4(페이지 골격 11종·공통 규칙)와 §6(에이전트 계약).
- Produces: 에이전트 이름 `css-doc-curator`. 입력 번들 계약(Task 5의 dispatch가 전달): `mode`(bootstrap|incremental), `head_sha`, 변경 파일 목록+커밋 로그(증분) 또는 스캔 대상(부트스트랩), 신규/변경 `docs/<slug>/` 목록, 이슈 ADR 본문, 스키마성 파일 경로. 출력: 페이지별 변경 요약 + 최종 라인 `ARTIFACT=docs/project/`, **커밋 안 함**.

- [ ] **Step 1: 골든 스펙 작성 (실패 상태로 시작)**

Create `tests/golden/wiki-project-docs.spec.md`:

```markdown
# Golden Test: wiki-project-docs

Asserts `/css:wiki` + `css-doc-curator` keep the docs/project/ living-docs contract.

## Acceptance criteria

### agents/doc-curator.md
- `grep -c "name: css-doc-curator" agents/doc-curator.md` >= 1
- `grep -c "css_stages: \[wiki\]" agents/doc-curator.md` >= 1
- `grep -c "ARTIFACT=docs/project/" agents/doc-curator.md` >= 1
- `grep -c "css:updated" agents/doc-curator.md` >= 1
- `grep -c "features/README.md" agents/doc-curator.md` >= 1
- `grep -c "미확인" agents/doc-curator.md` >= 1
- `grep -c "git commit" agents/doc-curator.md` >= 1  (커밋 금지 조항)

### commands/wiki.md
- `grep -c "css-doc-curator" commands/wiki.md` >= 1
- `grep -c "css:last-synced" commands/wiki.md` >= 1
- `grep -c "wiki-publish" commands/wiki.md` >= 1
- `grep -c "adr-list" commands/wiki.md` >= 1
- `grep -c "_project-wiki.lock" commands/wiki.md` >= 1
- `grep -c "AskUserQuestion" commands/wiki.md` >= 1
- `grep -c "docs/project/" commands/wiki.md` >= 3
```

- [ ] **Step 2: 실패 확인**

Run: `grep -c "name: css-doc-curator" agents/doc-curator.md`
Expected: `grep: agents/doc-curator.md: No such file or directory` (exit 2)

- [ ] **Step 3: 에이전트 작성**

Create `agents/doc-curator.md` (전문):

```markdown
---
name: css-doc-curator
description: Living project docs curator for docs/project/ — feature SoT, architecture, schema, ops, ADRs (CSS pipeline, sonnet)
model: sonnet
color: cyan
memory: project
css_stages: [wiki]
---

<Agent_Prompt>
  <Role>
    You are CSS-Doc-Curator. Your mission is to keep `docs/project/` — the current-state
    documentation of the target repository (feature SoT, architecture, data schema,
    operations, ADRs) — accurate, by merging the supplied evidence bundle (git diff, commit
    log, pipeline artifacts, issue ADR bodies) into the affected pages only.
    You are not responsible for per-change snapshot docs (`docs/<slug>/` belongs to
    css-documenter), inline code comments, or committing — the `/css:wiki` command commits
    after its user approval gate.
  </Role>

  <Why_This_Matters>
    Event logs (issues, per-slug snapshots) answer "what happened at the time"; nobody can
    read the current schema or feature behavior out of them without replaying history in
    their head. A curated current-state view stays trustworthy only if updates are merges
    backed by real code citations — full rewrites destroy hand edits, and uncited prose
    rots into fiction.
  </Why_This_Matters>

  <Success_Criteria>
    - Only pages affected by the input bundle changed (bootstrap: all applicable pages created).
    - Every page obeys its Page_Contracts entry and type rule — living = merge in place
      preserving existing prose and hand edits; index = add/update table rows; append-only =
      new files plus `superseded` status edits only.
    - Every factual claim cites evidence (`path:line`, test, config, session artifact, or an
      issue ADR body). Operational facts you cannot verify are marked `미확인`.
    - No evidence → no section, no page, no category (e.g. no `data/` when the repo has no
      persistent store). Empty scaffolds are defects.
    - Every touched page gets a refreshed `<!-- css:updated: {head_sha} {date} -->` header;
      the Home footer becomes `<!-- css:last-synced: {head_sha} {date} -->` with the supplied
      HEAD SHA; Home "최근 변경" lists exactly this run's page changes.
    - Feature pages are capability-scoped, not slug-scoped: place changes via the
      features/README.md mapping table; create a new area page only when no existing area
      fits, and record it in that index.
    - A living page growing past ~300 lines → propose a split in the change summary instead
      of splitting unilaterally.
  </Success_Criteria>

  <Constraints>
    - Write only inside `<project>/docs/project/`. Never run `git commit` or `git push`.
    - Everything else is read-only: session JSONs, `docs/<slug>/`, code, configs.
    - All prose Korean; diagrams in Mermaid; identifiers/commands stay verbatim.
    - Never write secret values — secret names and injection method only.
    - Echo `[css:wiki @ mode={bootstrap|incremental}]` at the top.
  </Constraints>

  <Page_Contracts>
    Types: living(제자리 병합) / index(행 추가·수정) / append-only(파일 추가만).
    - README.md [living] Home: 프로젝트 개요(3–5문장) · 문서 지도 표 · 최근 변경(직전 1회분) ·
      푸터 `css:last-synced` 마커.
    - architecture.md [living]: 시스템 컨텍스트(C4 L1 mermaid) · 모듈 구성(C4 L2 + 모듈|책임|
      코드 위치 표) · 주요 흐름(핵심 시나리오 1–3개 sequenceDiagram) · 기술 스택 표(계층|기술|버전|
      선정 근거→ADR 링크) · 모듈 경계·의존 규칙 · 횡단 관심사.
    - features/README.md [index]: 표 기능 영역|한 줄 설명|상태(안정·개발중·폐기예정·폐기)|관련 slug|관련 ADR.
      영역↔slug 매핑의 정본.
    - features/<영역>.md [living]: 현재 동작(호출자 관점 명세) · 인터페이스(API/CLI/화면, path:line 인용,
      상세 계약은 docs/<slug>/api.md 링크) · 내부 설계 요점(architecture.md와 중복 금지) · 데이터
      (data/schema.md 해당 절 링크) · 제약·알려진 한계 · 변경 이력 표(날짜|slug|요약|PR — 행 추가만).
    - data/schema.md [living]: 저장소 요약 · ERD(mermaid erDiagram, 테이블 ~15개 초과 시 도메인 분할) ·
      테이블별 상세(용도·소유 기능 링크·컬럼 표·인덱스·정의 위치) · 저장소별 특기사항(TTL·캐시 무효화 등).
    - data/migrations.md [index]: 표 순번/파일|날짜|변경 요약|관련 slug/PR.
    - operations/runbook.md [living]: 사전 요구사항 · 로컬 실행 · 빌드·테스트 · 배포(환경별) ·
      정기 작업·백업/복구. 모든 명령은 근거 파일(package.json/Makefile/CI 워크플로) 인용.
    - operations/configuration.md [living]: 환경변수 표(키|필수|기본값|설명|정의·사용 위치) ·
      설정 파일별 절 · 시크릿(목록·주입 방법만).
    - operations/troubleshooting.md [living]: `## <증상>`마다 원인/진단/조치/관련(이슈·slug·ADR).
    - decisions/README.md [index]: 표 번호|제목|상태(proposed·accepted·superseded by)|날짜|출처.
    - decisions/ADR-NNNN-<제목>.md [append-only] Nygard: 상태·날짜·출처 메타 + 배경(Context) ·
      결정(Decision) · 결과(Consequences). `GHS adr` 4필드와 1:1 — 이슈 백필 무손실.
  </Page_Contracts>

  <Execution_Protocol>
    1) Read the input bundle: mode, head_sha, changed-file list + commit log (incremental) or
       scan targets (bootstrap), new/changed `docs/<slug>/` folders, issue ADR bodies, schema-ish
       file paths, and the existing `docs/project/` tree.
    2) Map each change to affected pages via features/README.md and Page_Contracts.
    3) Bootstrap: create categories sequentially (architecture → features → data → operations →
       decisions), only where evidence exists; backfill supplied ADR bodies into decisions/.
    4) Incremental: merge into affected sections only; append 변경 이력 rows; add new ADR files;
       promote new `docs/<slug>/` content into the matching features/ page.
    5) Refresh css:updated markers, the Home footer, and Home 최근 변경.
    6) Self-review: citations present? page types respected? no invented facts? Then emit the
       change summary.
  </Execution_Protocol>

  <Output_Contract>
    - Change summary: one line per page — `- <path> — created|updated|proposed-split: <요약>`.
    - Final line: `ARTIFACT=docs/project/`.
  </Output_Contract>
</Agent_Prompt>
```

- [ ] **Step 4: 골든 기준(agent 부분)·registry 통과 확인**

Run:
```bash
grep -c "name: css-doc-curator" agents/doc-curator.md   # expected: 1
grep -c "ARTIFACT=docs/project/" agents/doc-curator.md  # expected: 1
grep -c "미확인" agents/doc-curator.md                   # expected: >=1
python -m pytest tools/agent_registry -q
```
Expected: grep 모두 ≥1, pytest 전부 PASS (doc-curator는 review+execute가 아니므로 dispatch/README 표 요건 미적용, forbidden_runtime_refs 없음).

- [ ] **Step 5: Commit**

```bash
git add agents/doc-curator.md tests/golden/wiki-project-docs.spec.md
git commit -m "feat(agents): add css-doc-curator living-docs curator"
```

---

### Task 5: `commands/wiki.md` — /css:wiki 커맨드

**Files:**
- Create: `commands/wiki.md`
- Verify: `tests/golden/wiki-project-docs.spec.md` (command 항목)

**Interfaces:**
- Consumes: Task 1 `GHS adr-list --session <slug>`, Task 2–3 `GHS wiki-publish --sha <sha>`, Task 4 `css-doc-curator` 입력 번들 계약.
- Produces: `/css:wiki [--init] [--no-publish]` — 파이프라인 외부에서 단독 실행되는 문서 큐레이션 커맨드.

- [ ] **Step 1: 커맨드 작성**

Create `commands/wiki.md` (전문):

```markdown
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
```

- [ ] **Step 2: 골든 기준 전체 통과 확인**

Run (repo root):
```bash
grep -c "css-doc-curator" commands/wiki.md      # >= 1
grep -c "css:last-synced" commands/wiki.md      # >= 1
grep -c "wiki-publish" commands/wiki.md         # >= 1
grep -c "adr-list" commands/wiki.md             # >= 1
grep -c "_project-wiki.lock" commands/wiki.md   # >= 1
grep -c "AskUserQuestion" commands/wiki.md      # >= 1
grep -c "docs/project/" commands/wiki.md        # >= 3
```
Expected: 모두 기준 이상.

- [ ] **Step 3: 회귀 확인**

Run: `bash tests/gh_sync/test_gh_sync.sh && python -m pytest tools -q`
Expected: bash `29 passed, 0 failed`, pytest 전부 PASS (codex_install의 동적 glob이 새 커맨드를 자동 수용).

- [ ] **Step 4: Commit**

```bash
git add commands/wiki.md
git commit -m "feat(commands): add /css:wiki living-docs curation command"
```

---

### Task 6: 문서·버전 반영 (README ×2, usage ×2, session-schema, plugin.json)

**Files:**
- Modify: `README.md`, `README.en.md`, `docs/usage.ko.md`, `docs/usage.md`, `docs/session-schema.md`, `.claude-plugin/plugin.json`

**Interfaces:**
- Consumes: Task 5까지의 커맨드/에이전트 이름·플래그.
- Produces: 사용자 문서 일관성 + 플러그인 버전 0.2.0.

- [ ] **Step 1: README.md 갱신 (4곳)**

(1) 개요 문단(라인 13)의 `총 21개의 전문 에이전트` → `총 22개의 전문 에이전트`.

(2) 단계별 상세 표의 `후처리` 행 아래에 추가:

```markdown
| 보조 | `/css:wiki` | `css-doc-curator` (sonnet) | `docs/project/` 살아있는 문서(기능 SoT·아키텍처·스키마·운영·ADR) 갱신 + GitHub Wiki 미러 (`--init` 부트스트랩, `--no-publish` 미러 생략) |
```

(3) `## 주요 기능` 목록의 `**머지 후 정리**` 항목 아래에 추가:

```markdown
- **살아있는 프로젝트 문서**: `/css:wiki`가 `docs/project/`(기능 SoT·ADR·아키텍처·스키마·운영)를 diff 기반으로 갱신하고 GitHub Wiki에 읽기 전용 미러 발행 — 파이프라인을 거치지 않은 수정·기존 프로젝트도 커버
```

(4) Codex 단계별 skill 나열 문장(`$css-clean` 언급 라인)에 `$css-wiki` 추가:
`PR 머지 후 정리: $css-clean.` → `PR 머지 후 정리: $css-clean. 프로젝트 문서 큐레이션: $css-wiki.`

- [ ] **Step 2: README.en.md 갱신 (동일 4곳, 영어)**

(1) `21 specialized agents` → `22 specialized agents` (해당 표현을 grep으로 찾아 수정).

(2) stage table `post-merge`/`housekeeping` 행 아래:

```markdown
| aux | `/css:wiki` | `css-doc-curator` (sonnet) | Curates `docs/project/` living docs (feature SoT, architecture, schema, ops, ADRs) + read-only GitHub Wiki mirror (`--init` bootstrap, `--no-publish` to skip the mirror) |
```

(3) Key features 목록:

```markdown
- **Living project docs**: `/css:wiki` updates `docs/project/` (feature SoT, ADRs, architecture, schema, ops) from git diffs and publishes a read-only GitHub Wiki mirror — covering non-pipeline commits and pre-existing projects
```

(4) Codex 단계별 나열에 `$css-wiki` 추가 (한국어판과 대칭).

- [ ] **Step 3: usage.ko.md 갱신 (2곳)**

(1) `## 단독 커맨드` 코드 블록의 `/css:clean` 라인 아래에 추가:

```
/css:wiki                      # (수시) docs/project/ 살아있는 문서 갱신 + Wiki 미러
```

(2) `## 정리` 섹션 뒤에 새 섹션 추가:

````markdown
## 프로젝트 문서 (/css:wiki)

slug별 스냅샷(`docs/<slug>/`)과 별개로, `docs/project/`를 "현재 상태" 문서(기능 SoT ·
아키텍처 · 데이터 스키마 · 운영 · ADR)로 유지합니다. 세션과 무관하게 아무 때나 실행할 수
있고, 파이프라인을 거치지 않은 손 커밋도 diff 기반으로 반영됩니다.

```
/css:wiki                # docs/project/ 없으면 전체 부트스트랩, 있으면 증분 갱신
/css:wiki --init         # 전체 재생성 강제
/css:wiki --no-publish   # in-repo 커밋까지만 (Wiki 미러 생략)
```

- 변경은 페이지별 요약 + 승인 게이트 후 `docs/project/`만 스코프해 커밋됩니다.
- 동기화 기준점은 `docs/project/README.md` 푸터의 `css:last-synced` 마커입니다.
- GitHub Wiki가 불가한 환경(private + Free 요금제, 미초기화 wiki, gh 미인증)에서는 미러만
  건너뛰고 나머지는 동일하게 동작합니다.
````

- [ ] **Step 4: usage.md 갱신 (usage.ko.md와 대칭, 영어)**

(1) standalone commands 블록에 `/css:wiki   # (anytime) refresh docs/project/ living docs + Wiki mirror` 추가.
(2) cleanup 섹션 뒤에 새 섹션 추가:

````markdown
## Project docs (/css:wiki)

Independent of the per-slug snapshots (`docs/<slug>/`), keeps `docs/project/` as the
**current-state** documentation (feature SoT, architecture, data schema, operations, ADRs).
Runs anytime, session-free; commits that bypassed the pipeline are picked up via git diff.

```
/css:wiki                # bootstrap when docs/project/ is absent, incremental otherwise
/css:wiki --init         # force a full rebuild
/css:wiki --no-publish   # stop after the in-repo commit (skip the Wiki mirror)
```

- Changes land only after a per-page summary + approval gate, committed scoped to `docs/project/`.
- The sync baseline is the `css:last-synced` marker in the `docs/project/README.md` footer.
- When the GitHub Wiki is unavailable (private repo on the Free plan, uninitialized wiki,
  unauthenticated gh), only the mirror is skipped — everything else works the same.
````

- [ ] **Step 5: session-schema.md에 한 줄 명시**

`## Files` 표 아래 문단으로 추가:

```markdown
`/css:wiki` is session-independent: it **reads** session files (ADR backfill) but never
writes them and never updates `_active.json`. Its lock is `locks/_project-wiki.lock`.
```

- [ ] **Step 6: plugin.json 버전 범프**

`.claude-plugin/plugin.json`: `"version": "0.1.0"` → `"version": "0.2.0"`.

- [ ] **Step 7: 전체 검증**

Run:
```bash
bash tests/gh_sync/test_gh_sync.sh
python -m pytest tools -q
grep -c "css-doc-curator" README.md README.en.md   # 각 1 이상
```
Expected: bash `29 passed, 0 failed`; pytest 전부 PASS — 특히 `tools/agent_registry`(README가 참조하는 에이전트 실재 검사)와 `tools/codex_install`(라이브 repo 변환) 통과.

- [ ] **Step 8: Commit**

```bash
git add README.md README.en.md docs/usage.ko.md docs/usage.md docs/session-schema.md .claude-plugin/plugin.json
git commit -m "docs: document /css:wiki and bump plugin to 0.2.0"
```

---

## 검증 요약 (전 태스크 완료 후)

```bash
bash tests/gh_sync/test_gh_sync.sh   # 29 passed, 0 failed
python -m pytest tools -q            # all passed
```

수동 스모크(선택): 아무 토이 픽스처(`tests/fixtures/toy-typescript`)를 임시 git repo로 만들어 `/css:wiki` 실행 → bootstrap 생성물 확인 → 작은 커밋 후 재실행 → 증분 갱신 + `css:last-synced` 전진 확인.

## 범위 외 (spec §11)

`/css:clean` 연동 훅, review 스테이지 ADR dual-write, 다중 repo 통합 wiki, `i18n/` 번역(`clean.ko.md`도 부재 — 기존 관례), mermaid 파이프라인 다이어그램 노드 추가.
