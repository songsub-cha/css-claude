> [English](README.en.md) · **한국어**

# css-claude

**CSS — Claude Super System**: [Claude Code](https://claude.com/claude-code)를 위한 개인용 글로벌 소프트웨어 개발 자동화 파이프라인.

상태: **v0.1.0**. 개인 사용 파이프라인. 설치 방법은 [`docs/installation.ko.md`](docs/installation.ko.md)를 참고하세요.

---

## 개요

아이디어를 입력하면 spec 작성 → 계획 → 검토 → TDD 구현 → 검증 → 문서화 → PR까지 자동으로 진행됩니다. 총 18개의 전문 에이전트가 단계별로 투입되며, 고비용 결정 시점에는 사람의 승인 게이트가 개입합니다.

```
/css:interview  →  /css:plan  →  /css:phase  →  /css:review  →  /css:execute  →  /css:verify  →  /css:document  →  /css:pr
                                                                                                                        ↑
                                                         /css:ship  ──── 3개 승인 게이트로 전체 실행 ────────────────────┘
```

### 파이프라인 + 에이전트 구조

```mermaid
flowchart TD
    START([💡 아이디어])

    subgraph S1["① interview"]
        I1(["superpowers:brainstorming"])
    end

    subgraph S2["② plan"]
        P1(["superpowers:writing-plans"])
    end

    subgraph S25["② .5 phasing"]
        PH1["css:phase\n임계치 초과 시 Phase 분해"]
    end

    subgraph S3["③ review"]
        R1["css-reviewer · css-architect"]
        R2["도메인 전문가 dispatch\napi · node · spring · db · ui · infra · async · llm · ml · prompt"]
        R1 -->|Rich Spec 위임| R2
    end

    GATE2{{"✋ Gate 2 — 실행 전 승인"}}

    subgraph S4["④ execute — TDD RED → GREEN → REFACTOR"]
        E1["css-executor"]
        E2[/"Rich Spec Cache\n(review 산출물 재사용)"/]
        E3["도메인 전문가\n(캐시 미스 fallback)"]
        E4["css-debugger\n(self-heal ×2)"]
        E5["css-test-engineer\n(커버리지 보완)"]
        E6["css-code-simplifier\n(REFACTOR 제안)"]
        E1 -->|캐시 히트| E2
        E1 -.->|캐시 미스| E3
        E1 --> E4
        E1 --> E5
        E1 -->|REFACTOR| E6
    end

    subgraph S5["⑤ verify"]
        V1["css-verifier"]
        V2["css-code-reviewer"]
        V3["css-security-reviewer"]
        V1 -->|병렬 dispatch| V2
        V1 -->|병렬 dispatch| V3
    end

    subgraph S6["⑥ document"]
        D1["css-documenter"]
    end

    GATE3{{"✋ Gate 3 — PR 전 승인"}}

    subgraph S7["⑦ pr"]
        PR1["css-pr-creator"]
    end

    END([🎉 PR 생성 완료])

    START --> S1 --> S2 --> S25 --> S3 --> GATE2 --> S4 --> S5 --> S6 --> GATE3 --> S7 --> END
```

### 단계별 상세

| 단계 | 커맨드 | 에이전트 | 산출물 |
|:---:|--------|----------|--------|
| ① | `/css:interview` | `superpowers:brainstorming` | `docs/superpowers/specs/YYYY-MM-DD-*.md` |
| ② | `/css:plan` | `superpowers:writing-plans` | `docs/superpowers/plans/YYYY-MM-DD-*.md` |
| ②.5 | `/css:phase` | (executor) | `phase-manifest-{slug}.json` + child Phase sessions |
| ③ | `/css:review` | `css-reviewer` (opus) + 도메인 전문가 | Rich Spec (태스크별 RED scaffold + GREEN 템플릿) |
| ④ | `/css:execute` | `css-executor` (sonnet) + fallback 전문가 | `css/{slug}` 브랜치 — TDD 구현 완료 |
| ⑤ | `/css:verify` | `css-verifier` + `css-code-reviewer` + `css-security-reviewer` | 검증 리포트 (커버리지 ≥85%) |
| ⑥ | `/css:document` | `css-documenter` (sonnet) | `docs/{slug}/README.md` 외 (Phase 세션: `docs/{epic}/p{n}/README.md`) |
| ⑦ | `/css:pr` | `css-pr-creator` (haiku) | GitHub PR (Phase 세션: `--base <base_branch>` 스택 PR) |

### 도메인 전문가 에이전트 (21개 중 11개)

review 단계에서 Rich Spec을 생성하고, execute 단계에서는 캐시 미스 시에만 fallback으로 호출됩니다 (비용 절감 ~40–50%).

| 에이전트 | 전문 영역 | 모델 |
|----------|-----------|:----:|
| `css-api-specialist` | Python / FastAPI REST·GraphQL API 설계 | sonnet |
| `css-node-backend` | Node.js / NestJS (3-layer + DI) 백엔드 | sonnet |
| `css-spring-backend` | Java·Kotlin / Spring Boot (3-layer + DI) 백엔드 | sonnet |
| `css-db-specialist` | PostgreSQL / Redis / ARQ + MongoDB + JPA·QueryDSL + TypeORM·Mongoose (polyglot 데이터) | sonnet |
| `css-ui-engineer` | Web (React/Vue/Svelte/Angular + Next.js) + Android (Compose) UI | sonnet |
| `css-infra-engineer` | Docker / Kubernetes / CI-CD / nginx + Terraform | sonnet |
| `css-async-coder` | Python asyncio 동시성 | sonnet |
| `css-langgraph-engineer` | LangChain / LangGraph / LangFuse + 벡터 DB / RAG | sonnet |
| `css-ml-engineer` | scikit-learn / PyTorch 피처·추론·평가 (테스트 가능 코드) | sonnet |
| `css-prompt-engineer` | 9-섹션 프롬프트 설계 및 리팩토링 | opus |
| `css-architect` | 아키텍처 자문 (read-only, review 단계 advisory) | opus |

### Epic / Phase 분해

대규모 아이디어는 단일 실행 세션으로 처리하기 어렵습니다. CSS는 아이디어를 **Epic**으로 계획한 후 병렬·순차 실행 가능한 **Phase**로 분해합니다.

| 계층 | 설명 |
|------|------|
| **Project** | 하나의 소프트웨어 프로젝트 (`css-claude`, `web-project` 등) |
| **Epic** | 하나의 기능 범위를 다루는 전체 계획 (slug 단위, 단일 `_active.json` 항목) |
| **Phase** | Epic을 수직 슬라이스로 분해한 독립 실행 단위 — 각자의 worktree + 브랜치 + PR 생성 |
| **Stage** | 각 Phase 내 파이프라인 단계 (plan/review/execute/verify/document/pr) |

**임계치 (D7):** `task_count > 20 OR batch_count > 4` 이면 `/css:phase`가 Epic을 2–5개 Phase로 분해합니다. 임계치 미만이면 단일 세션으로 진행 (기존 동작 유지).

**브랜치 규칙:** `phase_slug = "{epic}-p{n}"`, `phase_branch = "css/{epic}/p{n}"`. 선행 Phase가 있는 Phase는 선행 Phase 브랜치를 base로 스택 PR을 생성합니다.

상세 설계: [`docs/superpowers/specs/2026-05-29-epic-phase-pipeline-design.ko.md`](docs/superpowers/specs/2026-05-29-epic-phase-pipeline-design.ko.md)

---

## 빠른 시작

설치 후, 두 환경 모두 **동일한 파이프라인**을 사용합니다. Claude Code는 `/css:*` 커맨드를, Codex App/CLI는 설치된 `css-*` skills를 사용합니다.

### Claude Code

전체 파이프라인(승인 게이트 3개까지 자동 진행):

```
/css:ship "<아이디어>"
```

단계별로 직접 실행할 수도 있습니다:

```
/css:interview → /css:plan → /css:phase → /css:review → /css:execute → /css:verify → /css:document → /css:pr
```

### Codex App / CLI

먼저 설치: `bash scripts/install-codex.sh` (Windows: `scripts\install-codex.ps1`). 이후 App/CLI의 skill 메뉴에서 `css-ship`을 선택하거나 직접 mention합니다:

```
$css-ship "<아이디어>"
```

단계별: `$css-interview`, `$css-plan`, `$css-phase`, `$css-review`, `$css-execute`, `$css-verify`, `$css-document`, `$css-pr`.

- **병렬 전문가**(선택): `~/.codex/config.toml`의 `[features]` 아래 `multi_agent = true` 추가. 없으면 단일 에이전트가 순차 실행(결과 동일).
- **승인 게이트**: 구조화 UI 대신 평문 질문으로 제시되고 응답을 기다립니다.
- **세션 공유**: 상태가 `<project>/.claude/css/`에 저장되어, Claude Code에서 시작한 세션을 Codex에서 이어서(또는 반대로) 진행할 수 있습니다.
- 실행 동작 매핑은 `~/.codex/css/RUNTIME.md`가 규정합니다.

전체 커맨드 레퍼런스는 [`docs/usage.ko.md`](docs/usage.ko.md), Codex 설치·사용은 [`docs/installation.ko.md`](docs/installation.ko.md)의 Codex 섹션을 참고하세요.

## GitHub 추적 (기본 내장)

`/css:ship <아이디어>`를 실행하면 파이프라인이 진행 상황을 **GitHub Issues + Projects**에 그대로 비춥니다. 상주 서버 없이 `gh` CLI만 사용합니다(`lib/gh_sync.sh`).

- **이슈 + 보드**: slug마다 이슈 1개가 생성되고, 유저 단위 **GitHub Projects 칸반 보드**에 카드로 등록됩니다.
- **단계별 미러링**: 스테이지가 바뀔 때마다 라벨이 현재 상태(`css:interview` … `css:pr`, 완료 시 `css:done`)로 교체되고, 보드의 `CSS Stage` 컬럼도 함께 이동합니다. 각 스테이지 완료 시 요약 코멘트가 달리며, **interview·plan·document 단계는 산출 문서 전문**이 접이식 블록으로 첨부됩니다.
- **의사결정 기록(ADR)**: review 단계의 중요한 결정은 `ADR-N` 코멘트로 남습니다.
- **승인 게이트**: Gate 2(실행 전)·Gate 3(PR 전)에서 이슈에 `@멘션`이 달립니다. 터미널에서 바로 답하거나, "원격(이슈)에서 답변"을 선택해 **이슈 댓글로 답하면** 그 결정(자유 문장·한국어 OK)을 읽어 진행합니다 — 터미널 답변과 동일한 효과.
- **PR 연결**: 개발이 끝나면 PR이 생성되고 본문에 `Closes #<이슈>`가 들어가 이슈에 연결·머지 시 자동 종료됩니다.

**정본은 로컬입니다**: GitHub는 사람용 미러일 뿐, 파이프라인 상태의 정본은 `<project>/.claude/css/sessions/<slug>.json`입니다.

**설정 / 끄기**
- 최초 1회 `gh auth refresh -s project`로 Projects 스코프를 부여하세요(보드 생성·갱신에 필요).
- 끄려면 `~/.claude/css/config.json`의 `github.tracking_enabled`를 `false`로 두면 됩니다. GitHub 리모트가 없거나 `gh` 미인증이면 자동으로 기존 **터미널 게이트로 폴백**합니다(파이프라인 동작 불변).

## 주요 기능

- **아이디어 → PR 자동화**: 중요한 결정 시점에 명시적인 사람의 승인 게이트 포함
- **TDD 강제 적용**: execute 단계에서 테스트 커버리지 ≥85% 요구
- **캐시 우선 실행**: review 단계의 Rich Spec을 execute에서 재사용 — 전문가 재호출 최소화
- **자동 언어 감지**: JS/TS, Python, Go, Rust, Java (Maven), Java/Kotlin (Gradle, Android Compose 포함)
- **상태 저장 및 재개**: `<project>/.claude/css/sessions/{slug}.json`으로 중단 시점부터 재개 가능
- **멀티 세션 동시 실행**: 같은 프로젝트에서 터미널별로 다른 기능을 병렬 진행, 슬러그 단위 격리
- **자동 루프백 횟수 제한**: 한도 초과 시 사용자에게 에스컬레이션
- **OMC 독립**: Claude Code의 `superpowers` 플러그인과 `gh` CLI만 의존

## 설계 문서

전체 설계는 [`docs/specs/2026-05-27-css-pipeline-design.ko.md`](docs/specs/2026-05-27-css-pipeline-design.ko.md)를 참고하세요.

## 사전 조건

- Claude Code
- `superpowers` 플러그인 활성화
- `gh` CLI 인증 완료
- `git` ≥ 2.5

## 설치

플랫폼 스크립트로 설치:

- Windows: `powershell -ExecutionPolicy Bypass -File scripts\install.ps1`
- Ubuntu 22.04: `bash scripts/install.sh`
- Codex App / CLI (실험적): `bash scripts/install-codex.sh` — [`docs/installation.ko.md`](docs/installation.ko.md)의 Codex 섹션 참고

자세한 내용은 [`docs/installation.ko.md`](docs/installation.ko.md)를 참고하세요.

## 디렉토리 구조

```
css-claude/
├── README.md
├── commands/      # → ~/.claude/commands/css/
├── agents/        # → ~/.claude/agents/css/
├── lib/           # → ~/.claude/css/lib/ (gh_sync.sh — GitHub 추적)
├── config/        # 기본 설정
├── scripts/       # 설치 / 제거 스크립트 (Windows + Ubuntu)
├── docs/          # 설계 문서, 사용법, 트러블슈팅
└── tests/         # 에이전트 골든 테스트 + 토이 픽스처
```

## 라이선스

개인 사용 목적. 현 단계에서는 재배포 불가.
