<!-- css:updated: 079b623 2026-07-04 -->

# ADR-0004: Codex App/CLI 호환 (단일 소스 변환)

- **상태**: accepted
- **날짜**: 2026-06-03
- **출처**: `docs/superpowers/specs/2026-06-03-css-codex-compat-design.md:64-73` (확정된 결정 D1–D6)

## 배경 (Context)

Claude Code 전용이던 CSS 파이프라인을 OpenAI Codex App/CLI에서도 실행 가능하게 만들고자 했다. Claude Code 쪽 파일(`commands/`, `agents/`)을 회귀 위험 없이 그대로 유지하면서 Codex 전용 산출물을 만들어야 했다.

## 결정 (Decision)

- 배포 범위는 **개인 설치만**(D1) — codex-tools 매핑/env 감지 패턴은 차용하되 발행용 자산은 제외.
- 에이전트 실행 모델은 **하이브리드**(D2): `multi_agent` 가능 시 `spawn_agent`로 병렬+격리, 없으면 순차 단일 에이전트.
- 소스 관리는 **단일 소스 + 설치 시 변환·복사**(D3): repo의 `commands`/`agents`가 유일한 소스, Claude 파일 무수정.
- 세션 상태 위치는 **공유**(D4): Claude Code와 Codex 둘 다 `<project>/.claude/css/` 사용 — cross-tool resume 가능.
- `model:` frontmatter는 **변환 시 제거**(D5) — 런타임 중화의 매 호출 토큰 낭비를 피함.
- `Task()` 호출은 **RUNTIME.md 매핑 해석**(α안, D6) — 본문 재작성(β)이나 AGENTS.md 주입(γ)은 취약/침범적이라 기각.

## 결과 (Consequences)

- `tools/codex_install/`이 변환·설치를 전담하며, Claude Code 쪽 `commands/agents`는 어떤 코드 변경도 필요 없었다.
- 세션 공유 덕분에 같은 프로젝트에서 Claude Code로 시작한 세션을 Codex로, 또는 그 반대로 이어갈 수 있다.
- 트레이드오프: `multi_agent` 미설정 환경에서는 병렬 전문가 실행이 불가능해 순차 실행만 지원된다(결과는 동일하지만 느릴 수 있음).
- 구버전 Codex 설치가 남긴 레거시 프롬프트 파일(`~/.codex/prompts/css-*.md`)은 자동 정리되지 않아 수동 삭제가 필요하다([operations/troubleshooting.md](../operations/troubleshooting.md) 참조).
