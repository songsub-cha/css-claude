<!-- css:updated: 079b623 2026-07-04 -->

# 기능 인덱스

기능 영역은 파이프라인 slug(변경 단위)가 아니라 **capability(역량) 단위**입니다. 새 slug/커밋이 들어오면 아래 표를 기준으로 어느 영역 페이지에 병합할지 판단합니다. 이 표가 영역↔slug 매핑의 정본입니다.

| 기능 영역 | 한 줄 설명 | 상태 | 관련 slug | 관련 ADR |
|---|---|---|---|---|
| [pipeline-orchestration](pipeline-orchestration.md) | interview→plan→phase→review→execute→verify→document→pr 8단계 오케스트레이션과 `/css:ship` 3-게이트 마스터 플로우, `/css:clean` 정리 | 안정 | — | [ADR-0001](../decisions/ADR-0001-pipeline-core-architecture.md) |
| [epic-phase-decomposition](epic-phase-decomposition.md) | 대형 아이디어를 Epic(저비용) → Phase(수직 슬라이스, 독립 PR)로 분해해 세션 토큰 폭증을 방지 | 안정 | `epic-phase-pipeline` | [ADR-0002](../decisions/ADR-0002-epic-phase-decomposition.md) |
| [domain-specialists](domain-specialists.md) | 11개 도메인 전문가(백엔드 3종·db·ui·infra·async·llm·ml·prompt·architect) + dispatch table + 정합성 가드 | 안정 | `domain-expert-expansion` | [ADR-0003](../decisions/ADR-0003-domain-expert-expansion.md) |
| [codex-compatibility](codex-compatibility.md) | Claude Code 커맨드/에이전트를 Codex App/CLI skills로 변환해 동일 파이프라인을 이중 실행 | 안정 (실험적 표기) | — | [ADR-0004](../decisions/ADR-0004-codex-compatibility.md) |
| [github-tracking](github-tracking.md) | GitHub Issues + Projects 보드 미러링, 원격(이슈) 승인 게이트, ADR 코멘트, Epic→Phase 서브이슈 | 안정 | — | [ADR-0005](../decisions/ADR-0005-github-issues-projects-tracking.md) |
| [plugin-distribution](plugin-distribution.md) | Claude Code 마켓플레이스 플러그인 배포 + Windows/Ubuntu 레거시 스크립트 설치 병행 | 안정 | — | [ADR-0006](../decisions/ADR-0006-plugin-marketplace-distribution.md) |
| [project-docs-curation](project-docs-curation.md) | `docs/project/` 현재 상태 문서 큐레이션(`/css:wiki` + `css-doc-curator`) + GitHub Wiki 읽기전용 미러 | 안정 | — | [ADR-0007](../decisions/ADR-0007-project-docs-curation.md) |
