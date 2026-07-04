<!-- css:updated: 079b623 2026-07-04 -->

# Codex 호환성

## 1. 현재 동작

CSS는 Claude Code 외에 OpenAI Codex App/CLI에서도 동일한 파이프라인을 실행할 수 있습니다(실험적). `commands/`·`agents/`가 유일한 소스이며, 설치 시 이를 변환·복사해 Codex 전용 산출물을 만듭니다 — Claude Code 쪽 파일은 전혀 수정하지 않습니다 (`docs/installation.md:70-97`, `tools/codex_install/installer.py:1-9`).

- 커맨드/에이전트는 Codex skills로 변환되어 `~/.agents/skills`에 설치되고, 런타임/에이전트 데이터는 `~/.codex/css`에 설치됩니다 (`docs/installation.md:72`).
- 세션 상태는 `<project>/.claude/css/`에 공유되므로 Claude Code에서 시작한 세션을 Codex에서 이어서 진행(또는 반대)할 수 있습니다 (`docs/installation.md:97`).
- 병렬 전문가 실행은 `~/.codex/config.toml`의 `[features] multi_agent = true`가 있으면 `spawn_agent`로 병렬화되고, 없으면 순차 단일 에이전트로 폴백합니다 — 결과는 동일합니다 (`docs/installation.md:90-95`, D2).

## 2. 인터페이스

```
bash scripts/install-codex.sh          # Windows: scripts\install-codex.ps1
$css-ship "<아이디어>"                  # App/CLI skill 메뉴 또는 직접 mention
$css-interview / $css-plan / $css-phase / $css-review / $css-execute / $css-verify / $css-document / $css-pr / $css-clean
```

(출처: `docs/installation.md:74-88`, `docs/usage.md:34-43`)

Skill 호출 텍스트는 커맨드의 `$ARGUMENTS`로 취급되며, 실행 세부사항은 `~/.codex/css/RUNTIME.md`(설치 시 생성, 소스는 `codex/RUNTIME.md`)가 규정합니다 (`docs/usage.md:43`).

## 3. 내부 설계 요점

- **단일 소스 + 설치 시 변환**(D3): repo의 `commands`/`agents`가 유일한 소스이고, Claude 파일은 무수정 — drift 없음, 회귀 위험 최소화 (`docs/superpowers/specs/2026-06-03-css-codex-compat-design.md:70`).
- **`model:` frontmatter 제거**(D5): 런타임 중화는 매 호출 토큰 낭비이므로, Codex 복사본에서 아예 떼어낸다 (`docs/superpowers/specs/2026-06-03-css-codex-compat-design.md:72`, `tools/codex_install/installer.py`의 변환 로직).
- **`Task()` → 행동 해석**(D6, α안 채택): 본문 무수정 + `RUNTIME.md`가 매핑을 해석 — 설치 시 재작성(β)이나 `AGENTS.md` 주입(γ)은 취약/침범적이라 기각 (`docs/superpowers/specs/2026-06-03-css-codex-compat-design.md:73`).
- **i18n 파일 제외**: `*.ko.md`는 언어 접미사가 있는 stem이므로 기능 skill/agent로 설치되지 않도록 걸러진다 (`tools/codex_install/installer.py:18-22`).
- **하이브리드 에이전트 실행 모델**(D2): `multi_agent` 감지 후 병렬/순차 폴백 — 양쪽 환경 커버 (`docs/superpowers/specs/2026-06-03-css-codex-compat-design.md:69`).

## 4. 데이터

세션 JSON 스키마는 Claude Code와 완전히 동일하며 별도 Codex 전용 필드는 없다 (D4 — 공유 상태, `docs/superpowers/specs/2026-06-03-css-codex-compat-design.md:71`).

## 5. 제약·알려진 한계

- 배포 범위는 개인 설치로 한정되며, 발행용 자산(예: Codex 마켓플레이스 등록)은 범위 밖이다 (D1, `docs/superpowers/specs/2026-06-03-css-codex-compat-design.md:68`).
- 구버전 Codex 설치가 생성한 레거시 프롬프트 파일(`~/.codex/prompts/css-*.md`)은 현재 설치가 자동 제거하지 않는다 — 수동 삭제 필요 (`docs/troubleshooting.md:51-63`).
- Codex 사전 요구사항: Python 3(설치 시), `codex`/`git`/선택적 `gh` (`docs/installation.md:97`).

## 6. 변경 이력

| 날짜 | slug | 요약 | PR |
|---|---|---|---|
| 2026-06-03 | (설계, 미확인 slug) | Codex App/CLI 호환 계층 도입 — 단일 소스 변환·공유 세션 | 미확인 |
| 2026-07-04 | (bootstrap) | `docs/project/` 최초 생성 — 이 페이지 신설 | — |
