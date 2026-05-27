# css-claude

**CSS — Claude Super System**: [Claude Code](https://claude.com/claude-code)를 위한 개인용 글로벌 소프트웨어 개발 자동화 파이프라인.

상태: **v0.1.0**. 개인 사용 파이프라인. 설치 방법은 [`docs/installation.md`](docs/installation.md)를 참고하세요.

---

## 개요

아이디어를 입력하면 spec 작성 → 계획 → 검토 → TDD 구현 → 검증 → 문서화 → PR까지 자동으로 진행됩니다. 총 18개의 전문 에이전트가 단계별로 투입되며, 고비용 결정 시점에는 사람의 승인 게이트가 개입합니다.

```
/css:interview  →  /css:plan  →  /css:review  →  /css:execute  →  /css:verify  →  /css:document  →  /css:pr
                                                                                                        ↑
                                                /css:ship  ──── 3개 승인 게이트로 전체 실행 ────────────┘
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

    subgraph S3["③ review"]
        R1["css-reviewer · css-architect"]
        R2["도메인 전문가 dispatch\napi · db · ui · infra · async · llm · prompt"]
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

    START --> S1 --> S2 --> S3 --> GATE2 --> S4 --> S5 --> S6 --> GATE3 --> S7 --> END
```

### 단계별 상세

| 단계 | 커맨드 | 에이전트 | 산출물 |
|:---:|--------|----------|--------|
| ① | `/css:interview` | `superpowers:brainstorming` | `docs/superpowers/specs/YYYY-MM-DD-*.md` |
| ② | `/css:plan` | `superpowers:writing-plans` | `docs/superpowers/plans/YYYY-MM-DD-*.md` |
| ③ | `/css:review` | `css-reviewer` (opus) + 도메인 전문가 | Rich Spec (태스크별 RED scaffold + GREEN 템플릿) |
| ④ | `/css:execute` | `css-executor` (sonnet) + fallback 전문가 | `css/{slug}` 브랜치 — TDD 구현 완료 |
| ⑤ | `/css:verify` | `css-verifier` + `css-code-reviewer` + `css-security-reviewer` | 검증 리포트 (커버리지 ≥85%) |
| ⑥ | `/css:document` | `css-documenter` (sonnet) | `docs/{slug}/README.md` 외 |
| ⑦ | `/css:pr` | `css-pr-creator` (haiku) | GitHub PR |

### 도메인 전문가 에이전트 (18개 중 8개)

review 단계에서 Rich Spec을 생성하고, execute 단계에서는 캐시 미스 시에만 fallback으로 호출됩니다 (비용 절감 ~40–50%).

| 에이전트 | 전문 영역 | 모델 |
|----------|-----------|:----:|
| `css-api-specialist` | REST / GraphQL / gRPC / tRPC API 설계 | sonnet |
| `css-db-specialist` | PostgreSQL / Redis / ARQ 스키마·쿼리·마이그레이션 | sonnet |
| `css-ui-engineer` | Web + Android (Material 3, Jetpack Compose) UI | sonnet |
| `css-infra-engineer` | Docker / Kubernetes / CI-CD / nginx | sonnet |
| `css-async-coder` | Python asyncio 동시성 | sonnet |
| `css-langgraph-engineer` | LangChain / LangGraph / LangFuse + 벡터 DB / RAG | sonnet |
| `css-prompt-engineer` | 9-섹션 프롬프트 설계 및 리팩토링 | opus |
| `css-architect` | 아키텍처 자문 (read-only, review 단계 advisory) | opus |

---

## 빠른 시작

설치 후:

```
/css:ship "<아이디어>"
```

전체 커맨드 레퍼런스는 [`docs/usage.md`](docs/usage.md)를 참고하세요.

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

전체 설계는 [`docs/specs/2026-05-27-css-pipeline-design.md`](docs/specs/2026-05-27-css-pipeline-design.md)를 참고하세요.

## 사전 조건

- Claude Code
- `superpowers` 플러그인 활성화
- `gh` CLI 인증 완료
- `git` ≥ 2.5

## 설치

플랫폼 스크립트로 설치:

- Windows: `powershell -ExecutionPolicy Bypass -File scripts\install.ps1`
- Ubuntu 22.04: `bash scripts/install.sh`

자세한 내용은 [`docs/installation.md`](docs/installation.md)를 참고하세요.

## 디렉토리 구조

```
css-claude/
├── README.md
├── commands/      # → ~/.claude/commands/css/
├── agents/        # → ~/.claude/agents/css/
├── config/        # 기본 설정
├── scripts/       # 설치 / 제거 스크립트 (Windows + Ubuntu)
├── docs/          # 설계 문서, 사용법, 트러블슈팅
└── tests/         # 에이전트 골든 테스트 + 토이 픽스처
```

## 라이선스

개인 사용 목적. 현 단계에서는 재배포 불가.
