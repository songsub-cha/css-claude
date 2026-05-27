# 설치

## 사전 조건

- Claude Code 설치 (데스크톱 앱 또는 CLI). 최소 한 번 실행해서 `~/.claude/` 디렉토리가 생성되어 있어야 합니다.
- `superpowers` 플러그인 활성화 (`/plugin enable superpowers@claude-plugins-official`).
- `gh` CLI 설치 및 인증 완료 (`gh auth status`).
- `git` >= 2.5.
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
