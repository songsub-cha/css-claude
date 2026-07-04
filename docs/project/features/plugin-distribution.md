<!-- css:updated: 079b623 2026-07-04 -->

# 플러그인 배포

## 1. 현재 동작

CSS는 Claude Code 마켓플레이스 플러그인으로 배포됩니다. `.claude-plugin/marketplace.json`은 저장소 자신을 마켓플레이스로 선언(`source: "./"`)하고, `.claude-plugin/plugin.json`이 플러그인 메타데이터(`name: css`, `version: 0.2.0`)를 담습니다 (`.claude-plugin/marketplace.json:1-12`, `.claude-plugin/plugin.json:1-12`). 기존 Windows/Ubuntu 스크립트 설치도 동등하게 계속 지원됩니다 — 아무것도 폐기(deprecate)되지 않습니다 (D2).

## 2. 인터페이스

```
/plugin marketplace add songsub-cha/css-claude
/plugin install css@css-claude
```
(`docs/installation.md:24-29`)

레거시 스크립트:
```bash
# Windows
powershell -ExecutionPolicy Bypass -File scripts\install.ps1 [-Force]
# Ubuntu 22.04
bash scripts/install.sh   # 또는 FORCE=1 bash scripts/install.sh
```
(`docs/installation.md:33-51`, `scripts/install.sh:1-13`)

제거: `scripts/uninstall.{ps1,sh}`. 개인 설정(`~/.claude/css/config.json`)과 프로젝트 산출물(`<project>/.claude/css/`)은 제거되지 않으며 수동 삭제가 필요합니다 (`docs/installation.md:63-68`).

## 3. 내부 설계 요점

- **플러그인 이름이 커맨드 네임스페이스를 결정**: 플러그인 `css` + `commands/ship.md` → `/css:ship`이므로 플러그인 이름은 반드시 `css`여야 기존 네임스페이스가 유지된다 (`docs/superpowers/specs/2026-06-25-css-plugin-packaging-design.md:44`).
- **에이전트는 bare 이름으로 dispatch**: `Task(subagent_type="css-executor")`가 플러그인 모드에서도 그대로 동작 — 에이전트 이름 변경이나 dispatch 코드 수정이 불필요했다 (`docs/superpowers/specs/2026-06-25-css-plugin-packaging-design.md:45`).
- **`${CLAUDE_PLUGIN_ROOT}` 인라인 치환**: 커맨드/에이전트 본문에서 치환되고 하위 프로세스 env로도 export되어, 듀얼 모드 경로 해석기(`CSS_PLUGIN_DIR="${CLAUDE_PLUGIN_ROOT}"; CSS_PLUGIN_DIR="${CSS_PLUGIN_DIR:-$HOME/.claude/css}"`)가 가능하다 (`docs/superpowers/specs/2026-06-25-css-plugin-packaging-design.md:46`, `commands/ship.md:21`).
- **auto-discovery 유지**: `plugin.json`에 `commands`/`agents` 매니페스트 필드를 명시하지 않아 `commands/`·`agents/` 디렉터리 자동 스캔에 의존한다 — 이 때문에 `.ko.md` 번역이 `i18n/`으로 이동해야 했다(D3) (`docs/superpowers/specs/2026-06-25-css-plugin-packaging-design.md:47`).
- **버전 고정**: `plugin.json`의 `version`을 릴리스마다 올려야 설치된 사용자에게 업데이트가 전달된다(생략 시 커밋 SHA가 버전이 되어 매 커밋마다 업데이트됨) (`docs/superpowers/specs/2026-06-25-css-plugin-packaging-design.md:49`, `.claude-plugin/plugin.json:5`).

## 4. 데이터

해당 없음 — 배포 계층은 영속 데이터를 소유하지 않는다.

## 5. 제약·알려진 한계

- `tools/plugin_packaging/test_structure.py`가 `commands/`·`agents/`에 `.ko.md` 잔존, dotted stem, i18n 파일 개수(commands 9개·agents 21개) 불일치를 회귀 검사한다 — 어긋나면 패키징 테스트가 RED (`tools/plugin_packaging/test_structure.py:8-20`).
- 배포는 "개인 사용" 기조이며 현 단계에서 재배포는 불가로 명시되어 있다 (`README.md:270`).

## 6. 변경 이력

| 날짜 | slug | 요약 | PR |
|---|---|---|---|
| 2026-06-25 | (설계, 미확인 slug) | 마켓플레이스 플러그인 배포 도입 (단일 소스, i18n 분리) | 미확인 |
| 2026-07-04 | (bootstrap) | `docs/project/` 최초 생성 — 이 페이지 신설 | — |
