# GitHub Pipeline Tracking — P3: Dashboard Removal + Install/Docs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Delete the local dashboard (app + bridge + scripts + config), make the installers copy the P1 `lib/`, strip dashboard coupling from `interview.md`/golden specs, and replace the README dashboard section with GitHub-tracking docs — so the feature is installable and the repo has no dead dashboard infra.

**Architecture:** Mechanical removals + installer/doc edits. Installers gain a "Copying lib" step so `~/.claude/css/lib/gh_sync.sh` exists at runtime (the path `ship.md` calls). Already-committed historical `/css:document` outputs and design specs are **kept** as provenance (the new design doc records that it supersedes them); only the live dashboard assets + untracked WIP plans are deleted.

**Tech Stack:** bash + PowerShell installers; Markdown; git.

---

## Depends on / scope

- Depends on P1 (`lib/gh_sync.sh`) + P2 (ship.md references `~/.claude/css/lib/gh_sync.sh`).
- **Delete:** `dashboard/`, `scripts/install-dashboard.sh`, `scripts/uninstall-dashboard.sh`, `config/dashboard-config.example.json`, `.gitignore` `dashboard/.env` line, the `interview.md` dashboard block, dashboard golden specs, untracked `docs/superpowers/plans/*dashboard-epic-phase-view*` WIP.
- **Keep (provenance):** committed `docs/superpowers/specs/2026-05-28-pipeline-dashboard-*`, `docs/superpowers/plans/2026-05-28-pipeline-dashboard.md`, `docs/pipeline-dashboard/`, `docs/dashboard-epic-phase-view/`, `docs/epic-phase-pipeline/` — historical records of completed work. (Dangling code refs are acceptable in history; the new design doc notes supersession.)

### File map (P3)

- Modify: `scripts/install.sh`, `scripts/install.ps1`, `scripts/uninstall.sh`, `scripts/uninstall.ps1`, `commands/interview.md`, `README.md`, `README.en.md`, `.gitignore`.
- Delete: `dashboard/` (tree), `scripts/install-dashboard.sh`, `scripts/uninstall-dashboard.sh`, `config/dashboard-config.example.json`, `tests/golden/{bridge-systemd,dashboard-config,dashboard-scaffold,interview-projects-register}.spec.md`, untracked WIP plan docs.

---

## Task 1: Installers copy `lib/`

**Files:** Modify `scripts/install.sh`, `scripts/install.ps1`

- [ ] **Step 1 (install.sh):** after the "Copying agents" section (before "Installing default config"), insert:

```bash
section "Copying lib"
lib_dir="$css_dir/lib"
mkdir -p "$lib_dir"
lib_count=0
if compgen -G "$SOURCE_PATH/lib/*.sh" >/dev/null; then
  for f in "$SOURCE_PATH"/lib/*.sh; do
    cp "$f" "$lib_dir/"
    echo "  $(basename "$f")"
    lib_count=$((lib_count + 1))
  done
fi
echo "  ($lib_count lib files copied)"
```

- [ ] **Step 2 (install.ps1):** after the "Copying agents" section, insert:

```powershell
Write-Section "Copying lib"
$libDir = Join-Path $cssDir "lib"
New-Item -ItemType Directory -Force -Path $libDir | Out-Null
$srcLib = Join-Path $SourcePath "lib"
$libFiles = Get-ChildItem $srcLib -Filter "*.sh" -ErrorAction SilentlyContinue
foreach ($f in $libFiles) {
  Copy-Item $f.FullName -Destination $libDir -Force
  Write-Host "  $($f.Name)"
}
Write-Host "  ($($libFiles.Count) lib files copied)"
```

- [ ] **Step 3: Verify**

Run: `grep -c "Copying lib" scripts/install.sh scripts/install.ps1`
Expected: each file `1`.

- [ ] **Step 4: Smoke-test install.sh into a temp dir**

Run:
```bash
tmp="$(mktemp -d)"; CLAUDE_CONFIG_DIR="$tmp" bash scripts/install.sh >/dev/null 2>&1; ls "$tmp/css/lib/gh_sync.sh" && echo "LIB OK"; rm -rf "$tmp"
```
Expected: prints the path + `LIB OK`. (Prereqs git/gh/jq are present.)

- [ ] **Step 5: Commit**

```bash
git add scripts/install.sh scripts/install.ps1
git commit -m "feat(css): installers copy lib/ to ~/.claude/css/lib"
```

---

## Task 2: Uninstallers remove `lib/`

**Files:** Modify `scripts/uninstall.sh`, `scripts/uninstall.ps1`

- [ ] **Step 1 (uninstall.sh):** add `lib` removal — change the loop target line:

```bash
cmd_dir="$CLAUDE_HOME/commands/css"
agent_dir="$CLAUDE_HOME/agents/css"
lib_dir="$CLAUDE_HOME/css/lib"

for d in "$cmd_dir" "$agent_dir" "$lib_dir"; do
```

- [ ] **Step 2 (uninstall.ps1):** add `lib`:

```powershell
$cmdDir   = Join-Path $claudeHome "commands\css"
$agentDir = Join-Path $claudeHome "agents\css"
$libDir   = Join-Path $claudeHome "css\lib"

foreach ($d in @($cmdDir, $agentDir, $libDir)) {
```

- [ ] **Step 3: Verify**

Run: `grep -c "css/lib\|css\\\\lib" scripts/uninstall.sh scripts/uninstall.ps1`
Expected: each `>= 1`.

- [ ] **Step 4: Commit**

```bash
git add scripts/uninstall.sh scripts/uninstall.ps1
git commit -m "feat(css): uninstallers remove ~/.claude/css/lib"
```

---

## Task 3: Delete dashboard assets

**Files:** Delete `dashboard/`, `scripts/install-dashboard.sh`, `scripts/uninstall-dashboard.sh`, `config/dashboard-config.example.json`; Modify `.gitignore`

- [ ] **Step 1: Remove the `.gitignore` dashboard line** — delete:

```gitignore

# dashboard local config
dashboard/.env
```

- [ ] **Step 2: git rm the tracked assets**

```bash
git rm -r dashboard
git rm scripts/install-dashboard.sh scripts/uninstall-dashboard.sh config/dashboard-config.example.json
```

- [ ] **Step 3: Verify gone**

Run: `ls dashboard 2>/dev/null; ls scripts/*dashboard* 2>/dev/null; echo "exit=$?"`
Expected: no `dashboard/`, no dashboard scripts.

- [ ] **Step 4: Commit**

```bash
git add .gitignore
git commit -m "refactor(css): remove local dashboard app, scripts, and config"
```

---

## Task 4: Strip dashboard block from interview.md

**Files:** Modify `commands/interview.md`

- [ ] **Step 1: Delete the "Register project in dashboard" bullet + its sub-bullets** (the block beginning `- **Register project in dashboard** (NEW, if dashboard enabled):` through `- Release lock. On failure, log and continue (best-effort; pipeline must not block).`). Keep the surrounding `repo_root` capture bullet (before) and the `_active.json` update bullet (after).

- [ ] **Step 2: Verify no dashboard refs remain**

Run: `grep -niE "dashboard|projects\.json|flock" commands/interview.md; echo "exit=$?"`
Expected: no matches.

- [ ] **Step 3: Commit**

```bash
git add commands/interview.md
git commit -m "refactor(css): drop dashboard project-registration from interview.md"
```

---

## Task 5: Delete dashboard golden specs

**Files:** Delete `tests/golden/bridge-systemd.spec.md`, `tests/golden/dashboard-config.spec.md`, `tests/golden/dashboard-scaffold.spec.md`, `tests/golden/interview-projects-register.spec.md`

- [ ] **Step 1: git rm**

```bash
git rm tests/golden/bridge-systemd.spec.md tests/golden/dashboard-config.spec.md tests/golden/dashboard-scaffold.spec.md tests/golden/interview-projects-register.spec.md
```

- [ ] **Step 2: Verify remaining golden specs are dashboard-free**

Run: `grep -rliE "dashboard|projects\.json" tests/golden/ ; echo "exit=$?"`
Expected: no matches (empty).

- [ ] **Step 3: Commit**

```bash
git commit -m "test(css): remove dashboard golden specs"
```

---

## Task 6: README — replace Dashboard section with GitHub tracking

**Files:** Modify `README.md` (Korean), `README.en.md` (English)

- [ ] **Step 1 (README.md):** replace the `## Dashboard (Optional)` section (through its `dashboard/README.ko.md` link line) with:

```markdown
## GitHub 추적 (기본 내장)

`/css:ship <아이디어>`를 실행하면 해당 slug에 대한 **GitHub 이슈**가 생성되고, 단계마다 라벨(`css:<state>`)·요약 코멘트(스펙/계획/문서 단계는 전문)가 갱신되며, 유저 단위 **GitHub Projects 칸반 보드**에 카드로 표시됩니다. 승인 게이트(Gate 2/3)에서는 이슈에 `@멘션`이 남고, 터미널에서 바로 답하거나 이슈 댓글로 답하면(원격) 그 결정으로 진행합니다. 개발이 끝나면 PR이 생성되어 `Closes #<이슈>`로 이슈에 연결됩니다.

- 사람용 미러일 뿐, 파이프라인 정본 상태는 `<project>/.claude/css/sessions/<slug>.json`입니다.
- 끄려면 `~/.claude/css/config.json`의 `github.tracking_enabled`를 `false`로 두거나, GitHub 리모트가 없으면 자동으로 기존 터미널 게이트로 폴백합니다.
- 최초 1회 `gh auth refresh -s project`로 Projects 스코프를 부여하세요.
```

- [ ] **Step 2 (README.en.md):** replace the matching `## Dashboard (Optional)` section with:

```markdown
## GitHub tracking (built in)

Running `/css:ship "<idea>"` opens a **GitHub issue** for the slug; each stage updates a label (`css:<state>`) and posts a summary comment (the interview/plan/document stages embed the full document), and the issue appears as a card on a user-level **GitHub Projects** board. At approval gates (Gate 2/3) the issue gets an `@mention`; answer in the terminal or reply on the issue (remote) and the pipeline proceeds on that decision. When development finishes, the PR is created and linked to the issue via `Closes #<issue>`.

- It's a human-facing mirror only — the pipeline's source of truth stays in `<project>/.claude/css/sessions/<slug>.json`.
- Disable by setting `github.tracking_enabled` to `false` in `~/.claude/css/config.json`; with no GitHub remote it automatically falls back to the terminal-only gates.
- Grant the Projects scope once with `gh auth refresh -s project`.
```

- [ ] **Step 3: Verify**

Run: `grep -c "GitHub 추적" README.md; grep -c "GitHub tracking" README.en.md; grep -ciE "install-dashboard|dashboard/README" README.md README.en.md`
Expected: first two `>= 1`; the dashboard-link grep `0`.

- [ ] **Step 4: Commit**

```bash
git add README.md README.en.md
git commit -m "docs(css): replace dashboard README section with GitHub tracking"
```

---

## Task 7: Delete untracked WIP dashboard plans

**Files:** Delete untracked `docs/superpowers/plans/2026-05-30-dashboard-epic-phase-view-skeleton.md`, `docs/superpowers/plans/dashboard-epic-phase-view-p1.md` … `-p4.md`

> These were never committed (irreversible delete). They are obsolete WIP for the removed dashboard Epic/Phase view; the user approved their removal in the design review.

- [ ] **Step 1: Confirm they are untracked, then remove**

```bash
git status --porcelain docs/superpowers/plans/ | grep dashboard-epic-phase-view
rm -f docs/superpowers/plans/2026-05-30-dashboard-epic-phase-view-skeleton.md \
      docs/superpowers/plans/dashboard-epic-phase-view-p1.md \
      docs/superpowers/plans/dashboard-epic-phase-view-p2.md \
      docs/superpowers/plans/dashboard-epic-phase-view-p3.md \
      docs/superpowers/plans/dashboard-epic-phase-view-p4.md
```

- [ ] **Step 2: Verify**

Run: `ls docs/superpowers/plans/ | grep -c dashboard-epic-phase-view`
Expected: `0`.

- [ ] **Step 3:** (nothing to commit — untracked files; note completion in the PR description instead.)

---

## Task 8: Final full verification

- [ ] **Step 1: No dashboard refs in any active (non-doc) source**

Run:
```bash
grep -rniE "dashboard|CSS_DASHBOARD_RESUME" commands/ agents/ config/ scripts/ lib/ tests/golden/ ; echo "exit=$?"
```
Expected: no matches (history under `docs/` is intentionally kept).

- [ ] **Step 2: P1 suite + golden still green**

Run:
```bash
bash tests/gh_sync/test_gh_sync.sh 2>/dev/null | tail -1
[ "$(grep -c 'GHS init-issue' commands/ship.md)" -ge 1 ] && echo "ship sync OK"
```
Expected: `33 passed, 0 failed` + `ship sync OK`.

- [ ] **Step 3: install.ps1 + install.sh both reference lib; uninstallers too**

Run: `grep -lc "Copying lib" scripts/install.sh scripts/install.ps1`
Expected: both listed.

---

## Self-Review

**Spec coverage (design §12 + §11.2 setup):**
- Delete dashboard dir/scripts/config/.gitignore line → Task 3. ✅
- Installers copy lib (so `~/.claude/css/lib/gh_sync.sh` exists for ship.md) → Task 1; uninstallers remove it → Task 2. ✅
- interview.md dashboard block removed → Task 4. ✅
- Dashboard golden specs removed → Task 5. ✅
- README dashboard section → GitHub tracking → Task 6. ✅
- Untracked WIP dashboard plans removed → Task 7. ✅
- Setup note (`gh auth refresh -s project`) surfaced in README → Task 6. ✅

**Placeholder scan:** none; every step has exact commands/edits + a grep/smoke verification.

**Kept intentionally (not a gap):** committed historical design specs + `/css:document` outputs under `docs/` (provenance), per the approved scope.
