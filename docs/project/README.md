<!-- css:updated: 079b623 2026-07-04 -->

# css-claude 프로젝트 문서

> 최종 동기화: `079b623` · 2026-07-04 · `/css:wiki`가 관리

## 프로젝트 개요

css-claude("CSS — Claude Super System")는 Claude Code(및 실험적으로 Codex App/CLI)에서 실행되는 개인용 아이디어→PR 소프트웨어 개발 자동화 파이프라인 플러그인입니다 (`.claude-plugin/plugin.json:3-6`). 아이디어 하나를 입력하면 interview→plan→phase→review→execute→verify→document→pr 8단계를 22개 전문 에이전트가 나눠 수행하며, 실행 전/PR 전 등 고비용 결정 지점마다 사람의 승인 게이트가 개입합니다 (`README.md:13,89-100`). 대형 아이디어는 Epic/Phase로 자동 분해되어 세션 토큰 폭증을 방지하고, 진행 상황은 상주 서버 없이 GitHub Issues/Projects에 미러링됩니다. 이 `docs/project/` 트리 자신도 CSS의 한 기능(`/css:wiki` + `css-doc-curator`)이 큐레이션하는 "현재 상태" 문서입니다.

## 문서 지도

| 문서 | 내용 |
|---|---|
| [architecture.md](architecture.md) | 시스템 컨텍스트, 모듈 구성, 핵심 시나리오 시퀀스, 기술 스택, 모듈 경계, 횡단 관심사 |
| [features/README.md](features/README.md) | 기능 영역 인덱스 (영역↔slug↔ADR 매핑) |
| [features/pipeline-orchestration.md](features/pipeline-orchestration.md) | 8단계 파이프라인 + `/css:ship` 마스터 플로우 |
| [features/epic-phase-decomposition.md](features/epic-phase-decomposition.md) | Epic/Phase 세션 분해 |
| [features/domain-specialists.md](features/domain-specialists.md) | 11개 도메인 전문가 + dispatch table |
| [features/codex-compatibility.md](features/codex-compatibility.md) | Codex App/CLI 호환 |
| [features/github-tracking.md](features/github-tracking.md) | GitHub Issues/Projects 추적 |
| [features/plugin-distribution.md](features/plugin-distribution.md) | 마켓플레이스 플러그인 배포 |
| [features/project-docs-curation.md](features/project-docs-curation.md) | `docs/project/` 큐레이션 (`/css:wiki`) |
| [data/schema.md](data/schema.md) | 세션 JSON 스키마 (ERD) — 전통적 DB 없음 |
| [operations/runbook.md](operations/runbook.md) | 설치, 로컬 실행, 빌드·테스트, 배포, 정기 작업 |
| [operations/configuration.md](operations/configuration.md) | 환경변수, 설정 파일, 시크릿 |
| [operations/troubleshooting.md](operations/troubleshooting.md) | 증상별 원인/진단/조치 |
| [decisions/README.md](decisions/README.md) | ADR 인덱스 |

## 최근 변경

**2026-07-04 — bootstrap (최초 생성)**: `docs/project/` 부재 상태에서 저장소 전체(`.claude-plugin/`, `commands/`, `agents/`, `lib/gh_sync.sh`, `tools/`, `docs/`, `scripts/`, `config/`)를 스캔하고 `docs/domain-expert-expansion/`·`docs/epic-phase-pipeline/` 스냅샷 및 `docs/superpowers/specs/*-design.md` 7건의 확정 결정을 근거로 전체 트리를 신규 생성했습니다.

- `architecture.md` — 시스템 컨텍스트·모듈 구성·3개 시나리오 시퀀스·기술 스택·모듈 경계·횡단 관심사 신설
- `features/README.md` — 기능 영역 인덱스(7개 영역) 신설
- `features/pipeline-orchestration.md`, `features/epic-phase-decomposition.md`, `features/domain-specialists.md`, `features/codex-compatibility.md`, `features/github-tracking.md`, `features/plugin-distribution.md`, `features/project-docs-curation.md` — 각 기능 영역 페이지 신설
- `data/schema.md` — 세션 JSON ERD + 테이블 상세 신설 (`data/migrations.md`는 마이그레이션 개념이 없어 생성하지 않음)
- `operations/runbook.md`, `operations/configuration.md`, `operations/troubleshooting.md` — 운영 문서 3건 신설
- `decisions/README.md` + `decisions/ADR-0001` ~ `ADR-0007` — ADR 인덱스 + 7건 신설 (GitHub 이슈 ADR 백필 대상 없음 — `docs/superpowers/specs/*-design.md` 확정 결정 소급 정리)

`tests/fixtures/toy-*` 더미 프로젝트는 실제 프로젝트 상태에서 제외했습니다.

<!-- css:last-synced: 079b623258840901cc9b12becf25bcdda3dfd55f 2026-07-04 -->
