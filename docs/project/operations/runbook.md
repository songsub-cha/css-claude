<!-- css:updated: 079b623 2026-07-04 -->

# 운영 런북

## 1. 사전 요구사항

- Claude Code (데스크톱 앱 또는 CLI), 최소 1회 실행해 `~/.claude/` 생성 (`docs/installation.md:7`).
- `superpowers` 플러그인 활성화: `/plugin enable superpowers@claude-plugins-official` (`docs/installation.md:8`).
- `gh` CLI 설치 및 인증(`gh auth status`) (`docs/installation.md:9`).
- `git >= 2.5` (`docs/installation.md:10`).
- `ast-grep`(`sg`) — 다수 에이전트가 사용하는 구조적 코드 패턴 검색 도구. `npm install -g @ast-grep/cli` 또는 `cargo install ast-grep --locked` (`docs/installation.md:11-19`).
- Ubuntu만: `jq` — 설정 파싱에 필요 (`docs/installation.md:20`, `scripts/install.sh:34-40`).

## 2. 로컬 실행

플러그인 설치(택1):

```
/plugin marketplace add songsub-cha/css-claude
/plugin install css@css-claude
```
(`docs/installation.md:24-29`)

또는 스크립트 설치 — [operations/configuration.md](configuration.md) §2 참조.

설치 검증:
```
/css:ship "add a hello-world function"
```
브레인스토밍 흐름이 시작되면 정상입니다. `Ctrl+C`는 언제나 안전하며 세션 상태가 보존됩니다 (`docs/installation.md:53-61`).

## 3. 빌드·테스트

이 저장소 자체에는 빌드 산출물이 없습니다(마크다운 프롬프트 + 셸/파이썬 도구). 테스트는 세 갈래입니다:

- **Python 도구 단위 테스트** (`tools/css_schema`, `tools/agent_registry`, `tools/codex_install`, `tools/plugin_packaging`, `tools/gh_sync_bridge`):
  ```bash
  python -m unittest discover -s tools -t tools -v
  ```
  (근거: `docs/epic-phase-pipeline/README.md:271-273`. pytest는 부재하며 표준 `unittest`로 대체된 구성.)
- **`gh_sync.sh` bash 테스트 하네스** (fake `gh` 스텁 + 샌드박스, assert 카운트 방식):
  ```bash
  bash tests/gh_sync/test_gh_sync.sh
  ```
  (근거: `tests/gh_sync/test_gh_sync.sh:1-27` — `assert_eq`/`assert_contains`/`assert_not_contains` 헬퍼로 PASS/FAIL 카운트.)
- **골든 스펙 테스트** (커맨드/에이전트 산출물의 구조적 계약을 `grep -c` 단정문으로 검증):
  ```
  tests/golden/*.spec.md   # 예: tests/golden/wiki-project-docs.spec.md
  ```
  각 스펙은 "Acceptance criteria"로 `grep -c "<pattern>" <file>` >= N 형태의 단정문을 나열합니다 (`tests/golden/wiki-project-docs.spec.md:1-21`). 실행기는 미확인(수동/CI 스크립트로 소비되는 것으로 추정, 저장소 내 실행 러너 파일 없음).

CI 워크플로(`.github/workflows/`)는 이 저장소에 존재하지 않습니다 — 위 테스트는 로컬에서 수동 실행합니다 (미확인: 자동화 여부).

## 4. 배포

### 4.1 Claude Code 플러그인 (권장)

```
/plugin marketplace add songsub-cha/css-claude
/plugin install css@css-claude
```
릴리스마다 `.claude-plugin/plugin.json`의 `version`을 올려야 기존 설치자에게 업데이트가 전달됩니다 (`docs/installation.md:31`, `.claude-plugin/plugin.json:5`).

### 4.2 Windows (스크립트 설치)

```powershell
git clone https://github.com/songsub-cha/css-claude.git
cd css-claude
powershell -ExecutionPolicy Bypass -File scripts\install.ps1   # -Force로 덮어쓰기
```
(`docs/installation.md:33-41`)

### 4.3 Ubuntu 22.04 (스크립트 설치)

```bash
git clone https://github.com/songsub-cha/css-claude.git
cd css-claude
bash scripts/install.sh   # FORCE=1로 덮어쓰기
```
`scripts/install.sh`는 `git`/`gh`/`jq` 사전 요구사항과 `~/.claude/` 존재를 먼저 검사하고 실패 시 중단합니다 (`scripts/install.sh:29-53`).

### 4.4 Codex App/CLI (실험적)

```bash
bash scripts/install-codex.sh          # Windows: scripts\install-codex.ps1
```
자세한 내용은 [features/codex-compatibility.md](../features/codex-compatibility.md) 참조.

### 4.5 제거

```
Windows: powershell -ExecutionPolicy Bypass -File scripts\uninstall.ps1
Ubuntu:  bash scripts/uninstall.sh
```
개인 설정(`~/.claude/css/config.json`)과 프로젝트 산출물(`<project>/.claude/css/`)은 남으며 수동 삭제가 필요합니다 (`docs/installation.md:63-68`).

## 5. 정기 작업·백업/복구

이 프로젝트에는 전통적인 DB 백업/복구 절차가 없습니다(영속 저장소가 파일 기반 세션 JSON뿐 — [data/schema.md](../data/schema.md) 참조). 대신 다음 하우스키핑 절차가 있습니다:

- **머지 후 정리**: `/css:clean --session <slug>`가 dirty·미푸시·미머지 안전 점검 후 worktree/로컬 브랜치를 정리합니다. 확인 없이 삭제하지 않습니다 (`commands/clean.md:8-19`).
- **stale 락 자동 회수**: 60분 넘은 락은 다음 실행이 자동으로 교체·기록합니다 (`docs/session-schema.md:85-88`).
- **실패한 세션 수동 정리**:
  ```bash
  rm <project>/.claude/css/sessions/<slug>.json
  git worktree remove ../<repo>-css-<slug>
  git branch -D css/<slug>   # 푸시되지 않았을 때만
  ```
  (`docs/troubleshooting.md:65-76`)
- **`docs/project/` 동기화**: `/css:wiki`를 아무 때나 실행해 living docs를 최신 상태로 유지 — 자세한 내용은 [features/project-docs-curation.md](../features/project-docs-curation.md).
