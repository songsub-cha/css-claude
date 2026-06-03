> [English](installation.md) · **한국어**

# 설치

## 사전 조건

- Claude Code 설치 (데스크톱 앱 또는 CLI). 최소 한 번 실행해서 `~/.claude/` 디렉토리가 생성되어 있어야 합니다.
- `superpowers` 플러그인 활성화 (`/plugin enable superpowers@claude-plugins-official`).
- `gh` CLI 설치 및 인증 완료 (`gh auth status`).
- `git` >= 2.5.
- `ast-grep` (`sg`) — 구조적 코드 패턴 검색. 에이전트 다수가 사용합니다.
  ```bash
  # npm (Node.js 필요, 크로스 플랫폼 권장)
  npm install -g @ast-grep/cli

  # 또는 cargo (Rust 필요)
  cargo install ast-grep --locked
  ```
  설치 확인: `sg --version`
- (Ubuntu 전용) 설정 파싱을 위해 `jq` 필요.

## Windows

```powershell
git clone https://github.com/songsub-cha/css-claude.git
cd css-claude
powershell -ExecutionPolicy Bypass -File scripts\install.ps1
```

기존 개인 설정을 덮어쓰려면: `powershell -ExecutionPolicy Bypass -File scripts\install.ps1 -Force`

## Ubuntu 22.04

```bash
git clone https://github.com/songsub-cha/css-claude.git
cd css-claude
bash scripts/install.sh
```

기존 개인 설정을 덮어쓰려면: `FORCE=1 bash scripts/install.sh`

## 설치 확인

설치 후, git을 사용하는 아무 프로젝트에서:

```
/css:ship "add a hello-world function"
```

brainstorming 흐름이 시작되면 정상입니다. `Ctrl+C`는 언제든 안전하며 세션 상태가 유지됩니다.

## 제거

Windows: `powershell -ExecutionPolicy Bypass -File scripts\uninstall.ps1`
Ubuntu:  `bash scripts/uninstall.sh`

개인 설정(`~/.claude/css/config.json`)과 프로젝트 산출물(`<project>/.claude/css/`)은 제거되지 않습니다. 필요 없으면 수동으로 삭제하세요.

## Codex CLI (실험적)

CSS는 OpenAI Codex CLI에서도 동작합니다. 동일한 `commands/`·`agents/` 소스를 `~/.codex` 아래 Codex 프롬프트 + 에이전트 데이터 파일로 변환하며, Claude Code 설치는 건드리지 않습니다.

```bash
bash scripts/install-codex.sh
# Windows:
powershell -ExecutionPolicy Bypass -File scripts\install-codex.ps1
```

이후 `/css-ship`, `/css-interview` … 로 호출합니다 (Codex는 `css:` 네임스페이스 대신 `css-` 프리픽스 사용).

선택 — 병렬 전문가를 켜려면 `~/.codex/config.toml`에 추가:

```toml
[features]
multi_agent = true
```

없으면 전문가가 단일 에이전트에서 순차 실행됩니다(병렬성만 포기, 결과 동일). 세션 상태는 `<project>/.claude/css/`에서 Claude Code와 공유되어 어느 도구에서 시작하든 다른 도구에서 이어집니다. 실행 동작은 `~/.codex/css/RUNTIME.md`가 규정합니다. 사전 조건: Python 3(설치 시), 런타임에 `codex`·`git`·(선택) `gh`.
