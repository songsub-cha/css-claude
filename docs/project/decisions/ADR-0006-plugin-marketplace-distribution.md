<!-- css:updated: 079b623 2026-07-04 -->

# ADR-0006: 플러그인 마켓플레이스 배포

- **상태**: accepted
- **날짜**: 2026-06-25
- **출처**: `docs/superpowers/specs/2026-06-25-css-plugin-packaging-design.md:32-49` (Confirmed Decisions + Verified Platform Facts)

## 배경 (Context)

기존 Windows/Ubuntu 스크립트 설치만으로는 업데이트가 불편했다. Claude Code의 마켓플레이스 플러그인 배포 방식을 도입하되, 레거시 설치 방식과 기존 `/css:*` 네임스페이스·에이전트 dispatch를 깨뜨리지 않아야 했다.

## 결정 (Decision)

- 배포 수준은 **마켓플레이스 배포**(D1) — `plugin.json` + `marketplace.json`을 같은 저장소에 둠.
- 레거시 설치 스크립트는 **완전 병행 유지** — 아무것도 deprecate하지 않음(D2).
- `.ko.md` auto-discovery 충돌 회피를 위해 `commands/*.ko.md`/`agents/*.ko.md`를 **`i18n/` 트리로 이동**(D3).
- 검증된 플랫폼 사실: 플러그인 이름이 커맨드 네임스페이스를 결정(`css`+`ship.md`→`/css:ship`이므로 플러그인 이름은 반드시 `css`), 에이전트는 bare frontmatter 이름으로 dispatch(변경 불필요), `${CLAUDE_PLUGIN_ROOT}`는 커맨드/에이전트 본문에 인라인 치환되고 하위 프로세스 env로도 export, `commands`/`agents` 매니페스트 필드를 생략하면 auto-discovery 유지, `version` 설정 시에만 사용자가 명시적 업데이트를 받음(생략 시 커밋 SHA가 버전).

## 결과 (Consequences)

- 사용자는 `/plugin marketplace add` + `/plugin install`만으로 설치·업데이트가 가능해졌고, 스크립트 설치자는 아무 영향을 받지 않는다.
- `i18n/` 분리로 인해 번역 파일 개수(`commands` 9개, `agents` 21개)가 회귀 테스트 대상이 되었다(`tools/plugin_packaging/test_structure.py:19-20`).
- 트레이드오프: 릴리스마다 `plugin.json`의 `version`을 수동으로 올려야 하며, 잊으면 기존 설치자가 업데이트를 받지 못한다.
- 이 결정 덕분에 에이전트 dispatch 코드(`Task(subagent_type="css-executor")` 등)는 플러그인 모드 전환 시 단 한 줄도 바뀌지 않았다.
