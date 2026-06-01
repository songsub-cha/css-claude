> [English](2026-05-27-css-pipeline-design.md) · **한국어**

# CSS 파이프라인 설계 — Claude Super System

## 메타데이터

- **생성일**: 2026-05-27
- **소유자**: sub1904@gmail.com
- **상태**: 설계 — 구현 대기
- **네임스페이스**: `/css:*` (글로벌 Claude Code 커맨드)
- **설치 대상**: `~/.claude/commands/css/`, `~/.claude/agents/css/`
- **향후 저장소**: 비공개 GitHub repo (예: `css-claude`)
- **Brainstorming 세션**: `superpowers:brainstorming` 주도

## 개요

CSS(Claude Super System)는 Claude Code를 위한 개인용 글로벌 소프트웨어 개발 자동화 파이프라인입니다. `/css:` 네임스페이스 아래 8개 슬래시 커맨드를 노출하며, 기능을 아이디어부터 병합된 PR까지 7개 단계로 진행시키고, 3개 승인 게이트로 전체 파이프라인을 실행하는 마스터 커맨드를 추가로 제공합니다.

### 목표

1. 고위험 결정 시점에 명시적인 사람 체크포인트를 둔 **아이디어-투-PR 자동화**.
2. **구성에 의한 품질(Quality by construction)**: 커버리지 ≥85%를 강제하는 TDD, 구현 전 구조화된 계획, 자동 루프백을 경계 내로 제한한 다중 패스 review/verify.
3. **크로스 프로젝트 재사용성**: `~/.claude/`에 한 번 설치하면 사용자 머신의 모든 프로젝트에서 동작.
4. **OMC 독립성**: `/css:*`는 oh-my-claudecode(OMC)에 의존하지 않음. Claude Code 표준 플러그인(특히 `superpowers`)과 `gh` CLI에만 의존.
5. **도메인 인식 위임**: 18개 전문 서브 에이전트가 plan review, code-quality review, API, DB, UI(web + Android), infra, security, testing, debugging, refactoring, async, LLM 앱, 프롬프트 작성을 커버.

### 비목표 (v1)

- PR 자동 병합.
- 패키지별 감지를 넘어선 크로스 언어 모노레포 오케스트레이션(기본 모노레포 처리만).
- Claude Code 플러그인 패키지로의 배포(3단계 배포로 보류).

### 범위 내 (v1)

- **같은 프로젝트 내 멀티 세션 동시성**: 여러 터미널이 서로 다른 기능에 대해 동시에 `/css:ship`(또는 임의의 `/css:*`)을 실행. 세션은 slug로 격리됨 — 별도 세션 파일, 별도 워크트리, 별도 브랜치. 동일 slug 충돌은 명시적으로 거부됨.

## 결정 요약

| 주제 | 결정 |
|-------|----------|
| 설치 위치 | `~/.claude/commands/css/` (글로벌 커맨드, `/css:command` 네임스페이스) |
| OMC 의존성 | 없음 — 완전 독립 |
| 마스터 커맨드(`/css:ship`) 게이트 | 3개 사용자 승인: interview 이후(interview spec 수락), execute 전, PR 전 |
| 언어 감지 | 자동: JS/TS, Python, Go, Rust, Java(Maven), Java/Kotlin(Gradle, Android 포함) |
| 산출물 저장 | `<project>/.claude/css/` (ephemeral한 곳만 gitignore) |
| 루프백 제어 | AI 자동 판단, review는 최대 2회, verify는 최대 3회, 이후 사용자 에스컬레이션 |
| Interview 방식 | `superpowers:brainstorming`을 통한 한 번에 한 질문(소크라테스식, 모호성 점수화) |
| Plan 방식 | `superpowers:writing-plans` 경유 |
| `css` 의미 | Claude Super System / Studio — 범용 소프트웨어 개발 파이프라인 |
| 아키텍처 | 모듈식: 커맨드 = 얇은 오케스트레이터, 에이전트 = 워커 |
| 에이전트 시스템 프롬프트 | 영어(정책 정밀도); 사용자 대면 메시지와 출력은 한국어 |
| 배포 범위 | 2단계: 수동 + 스크립트 설치(Windows PowerShell + Ubuntu 22.04 Bash)를 갖춘 비공개 GitHub repo |

## 아키텍처

### 3계층 구조

```
┌─────────────────────────────────────────────────────────┐
│  Commands Layer  (~/.claude/commands/css/)              │
│  /css:interview /css:plan /css:review /css:execute      │
│  /css:verify    /css:document /css:pr /css:ship         │
│                                                          │
│  Role: thin entrypoints. Gate via AskUserQuestion,      │
│        dispatch agents, persist artifacts.              │
└──────────────────────┬──────────────────────────────────┘
                       │ Task() invocations
┌──────────────────────▼──────────────────────────────────┐
│  Agents Layer  (~/.claude/agents/css/)                  │
│  reviewer / executor / verifier / documenter /          │
│  pr-creator / code-reviewer / api-specialist /          │
│  ui-engineer / architect / db-specialist /              │
│  infra-engineer / security-reviewer / test-engineer /   │
│  debugger / code-simplifier / async-coder /             │
│  langgraph-engineer / prompt-engineer                   │
│                                                          │
│  Role: stage- and domain-specific workers with policy   │
│        encoded in system prompts.                       │
└──────────────────────┬──────────────────────────────────┘
                       │ read/write
┌──────────────────────▼──────────────────────────────────┐
│  State Layer  (<project>/.claude/css/)                  │
│  sessions/{slug}.json   (one file per active session)   │
│  sessions/_active.json  (pointer to most-recent session)│
│  specs/         (interview output via brainstorming)    │
│  plans/         (writing-plans output + spec extensions)│
│  reviews/       (review verdicts + findings)            │
│  executions/    (TDD logs + worktree info)              │
│  verifies/      (test/coverage/criteria reports)        │
│  documents/     (staging before docs/<slug>/)           │
└─────────────────────────────────────────────────────────┘
```

### 핵심 원칙

- **독립 실행**: 각 `/css:*` 커맨드는 단독 호출 가능. 누락된 선행 산출물은 크래시가 아니라 사용자 친화적 안내로 표면화.
- **단일 진실의 원천**: 단계별 산출물은 `<project>/.claude/css/` 아래에 존재. slug별 세션 파일(`sessions/{slug}.json`)이 이를 가리킴.
- **`/css:ship`에는 3개 승인 게이트만**: interview 이후, execute 전, PR 전.
- **영어 정책 + 한국어 응답**: 에이전트 시스템 프롬프트는 영어 사용(정밀도); 사용자에게 보이는 출력 텍스트는 한국어.
- **도메인 위임(캐시 우선)**: API, DB, UI, infra, async, LLM 앱, 프롬프트 엔지니어링 작업은 각각 `/css:review`에서 매칭되는 전문가에게 한 번 dispatch되어 태스크별 RED scaffold + GREEN 템플릿을 담은 rich spec을 생성. `/css:execute`에서는 executor가 spec을 읽고 템플릿을 직접 적용 — 통상 경로에서 전문가 재호출 없음. 전문가는 `css-debugger` self-heal이 소진됐을 때만 경계 내 fallback으로 재호출. naive한 이중 호출 설계 대비 ~40–50% LLM 비용 절감 기대.

## 디렉토리 구조

### 글로벌 설치 (`~/.claude/`)

```
~/.claude/
├── commands/
│   └── css/
│       ├── interview.md       # /css:interview
│       ├── plan.md            # /css:plan
│       ├── review.md          # /css:review
│       ├── execute.md         # /css:execute
│       ├── verify.md          # /css:verify
│       ├── document.md        # /css:document
│       ├── pr.md              # /css:pr
│       └── ship.md            # /css:ship (master)
├── agents/
│   └── css/
│       ├── reviewer.md             # plan reviewer (used by /css:review)
│       ├── executor.md
│       ├── verifier.md
│       ├── documenter.md
│       ├── pr-creator.md
│       ├── code-reviewer.md        # code-quality reviewer (used by /css:verify)
│       ├── api-specialist.md
│       ├── ui-engineer.md
│       ├── architect.md
│       ├── db-specialist.md
│       ├── infra-engineer.md
│       ├── security-reviewer.md
│       ├── test-engineer.md
│       ├── debugger.md
│       ├── code-simplifier.md
│       ├── async-coder.md
│       ├── langgraph-engineer.md
│       └── prompt-engineer.md
└── css/
    └── config.json            # global defaults (optional)
```

### 프로젝트별 산출물 (`<project>/.claude/css/`)

```
<project>/.claude/css/
├── sessions/
│   ├── {slug}.json                       # one per active or completed session
│   └── _active.json                      # {"latest_slug": "user-auth-jwt"} — pointer for standalone commands
├── specs/
│   └── interview-{slug}-{ts}.md          # from superpowers:brainstorming
├── plans/
│   ├── plan-{slug}-{ts}.md               # from superpowers:writing-plans
│   ├── api-spec-{slug}-{ts}.md           # from css-api-specialist (if applicable)
│   ├── db-spec-{slug}-{ts}.md
│   ├── ui-spec-{slug}-{ts}.md
│   ├── infra-spec-{slug}-{ts}.md
│   ├── arch-review-{slug}-{ts}.md
│   ├── async-spec-{slug}-{ts}.md
│   ├── llm-app-spec-{slug}-{ts}.md
│   └── prompt-spec-{slug}-{ts}.md
├── reviews/
│   └── review-{slug}-{ts}.md
├── executions/
│   ├── exec-log-{slug}-{ts}.md
│   └── worktree-{slug}/                  # metadata only; the actual worktree lives at ../{repo}-css-{slug}
├── verifies/
│   ├── verify-{slug}-{ts}.md
│   ├── code-review-{slug}-{ts}.md
│   └── security-review-{slug}-{ts}.md
└── documents/
    └── doc-staging-{slug}.md
```

### 최종 문서 (`<project>/docs/{slug}/`)

```
<project>/docs/{slug}/
├── README.md         # always
├── api.md            # if public API surface added
└── changelog.md      # if behavior change or migration
```

### 네이밍 규칙

- `{slug}`: interview 중 도출된 kebab-case 식별자(예: `user-auth-jwt`).
- `{ts}`: 안전한 구분자를 가진 ISO-8601 타임스탬프(예: `2026-05-27T14-30`).
- **모든 산출물 파일명은 예외 없이 `-{ts}`를 포함**(interview spec, plan, 도메인 spec, review, exec log, verify, document staging).
- 같은 slug로 단계를 재실행하면 새 타임스탬프 산출물이 생성됨(히스토리 보존). 세션 파일은 최신을 가리킴.
- 최종 사용자 대면 문서(`<project>/docs/{slug}/*.md`)는 파일명에 타임스탬프를 **사용하지 않음** — 이들은 병합된 산출물의 정본 문서.

## 커맨드 명세

8개 커맨드 모두 동일한 골격을 따릅니다:

```
1. Parse arguments and flags (including `--slug`).
2. Resolve target session via `--slug`, idea-derived new slug (for `/css:ship`), or `_active.json` pointer.
3. Load `sessions/{slug}.json` (or initialize for new ship).
4. Acquire per-slug phase lock.
5. Detect language profile if missing.
6. Gate (AskUserQuestion) when required.
7. Dispatch to skill or sub-agent.
8. Persist artifact path, update `sessions/{slug}.json`, refresh `_active.json.latest_slug`.
9. Release lock.
10. Announce next step (and, for `/css:ship`, auto-advance).
```

### `/css:interview <idea>`

- **Skill**: `superpowers:brainstorming`
- **동작**:
  1. 생성된 slug(brainstorming의 설계 파일명에서 추출)로 `sessions/{slug}.json` 초기화; `_active.json.latest_slug` 갱신.
  2. `Skill("superpowers:brainstorming")`이 전체 소크라테스식 흐름 실행(컨텍스트 발견 → 명확화 질문 → 2-3개 접근 → 섹션별 설계 → spec 작성 → spec 자체 검토 → 사용자 검토).
  3. **오버라이드**: brainstorming의 종단 `writing-plans` 호출은 건너뜀. CSS는 `/css:plan`을 별도 호출하여 각 커맨드가 독립 실행 가능하게 유지.
  4. 세션 파일에 `phases.interview.artifact`(brainstorming의 spec 파일 경로) 기록.
- **출력**: `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md` (brainstorming 기본 위치, 단일 진실의 원천으로 유지).
- **게이트**(마스터 흐름 내): brainstorming 내부의 사용자 검토 단계가 Gate 1 역할.

### `/css:plan [--from <spec-path>]`

- **Skill**: `superpowers:writing-plans`
- **동작**:
  1. spec 경로 해석(인자 > 해석된 세션 파일 > 사용자에게 질문).
  2. `Skill("superpowers:writing-plans")`이 구조화된 plan 생성.
  3. 세션 파일에 plan 경로 보존.
- **출력**: writing-plans 기본 위치(예: `docs/superpowers/plans/...`). CSS는 경로만 기록.

### `/css:review [--plan <plan-path>]`

- **Agent**: `css-reviewer` (도메인 전문가로의 서브 dispatch 포함)
- **동작**:
  1. Reviewer가 plan + spec 로드, 커버리지 매트릭스 감사 수행.
  2. Reviewer가 도메인을 식별하고 전문가에게 병렬 dispatch:
     - REST/GraphQL/gRPC/tRPC 패턴 → `css-api-specialist`
     - SQL 스키마, 마이그레이션, Redis, ARQ → `css-db-specialist`
     - Components/Composables/Activity/Fragment → `css-ui-engineer`
     - Dockerfile/compose/K8s/CI → `css-infra-engineer`
     - 아키텍처에 영향을 주는 변경 → `css-architect`
     - `async`/`await`/`asyncio` 패턴 → `css-async-coder`
     - LangChain/LangGraph/LangFuse → `css-langgraph-engineer`
     - LLM 프롬프트 작성 → `css-prompt-engineer`
  3. 전문가 출력은 plan이 참조하는 `*-spec-{slug}.md` 산출물이 됨.
  4. Reviewer가 평결 발행: `PASS | LOOPBACK_TO_PLAN | LOOPBACK_TO_INTERVIEW`.
  5. 최대 2회 자동 루프백. 그 이상은 사용자 에스컬레이션.
- **출력**: `.claude/css/reviews/review-{slug}-{ts}.md` + 도메인 spec 파일.

### `/css:execute [--plan <plan-path>]`

- **Agent**: `css-executor` (`/css:review`에서 생성된 rich-spec 산출물을 GREEN 단계 캐시로 사용; 전문가는 fallback으로만 호출)
- **동작**:
  1. `git worktree add ../{repo}-css-{slug} -b css/{slug}` 생성.
  2. **rich-spec 산출물 인덱싱**: `/css:review` 중 생성된 모든 `*-spec-{slug}-*.md` 산출물(api-spec, ui-spec, db-spec, infra-spec, async-spec, llm-app-spec, prompt-spec)을 찾아 그 `## Task {id}` 앵커를 lookup 맵으로 파싱.
  3. plan 태스크를 의존성 그래프로 배치 묶음. 각 태스크에 대해 그 `Files:`와 코드를 **Domain Dispatch Table**과 대조하여 어느 spec 산출물이 RED scaffold + GREEN 템플릿을 공급할지 미리 해석(매칭 없으면 "executor-direct").
  4. **배치 체크포인트**: 각 배치 전에 의도(각 태스크가 어느 spec 산출물에서 끌어오는지 포함)를 알리고 사용자 확인 요청. 이 배치별 마이크로 체크포인트는 3개 마스터 `/css:ship` 게이트(interview 후, execute 전, PR 전)와 **별개이며 추가적**.
  5. 각 태스크에 대해 rich spec을 캐시로 사용하여 TDD 강제:
     - **RED**(executor 소유, spec 주도): spec의 매칭되는 `## Task {id}` 섹션에서 `RED scaffold:` 블록을 워크트리에 복사; 실행; 반드시 실패해야 함. exit 0이면 → 중단 및 에스컬레이션.
     - **GREEN**(executor 소유, spec 주도, 경계 내 fallback 포함):
       - 같은 `## Task {id}` 섹션에서 `GREEN template:` 블록을 워크트리에 복사. **기본적으로 전문가 재호출 안 함.**
       - spec 매칭 없음 → executor가 plan 태스크에 따라 직접 구현.
       - 테스트 실행. 실패 시:
         1. `css-debugger` 시도 1 → 패치 → 재실행.
         2. `css-debugger` 시도 2 → 패치 → 재실행.
         3. 여전히 실패 AND 전문가가 매칭됐으면: 전체 실패 트레일과 함께 전문가를 **execute 단계 fallback**(최대 1회 호출)으로 호출.
         4. 여전히 실패 → 중단 및 에스컬레이션.
     - **REFACTOR**(executor 소유): `css-code-simplifier` 호출; 테스트는 green을 유지해야 함.
  6. css 브랜치에 태스크별 커밋(executor 소유). 트레일러: `CSS-Slug`, `CSS-Task`, `CSS-Specialist-Spec`(GREEN이 spec에서 끌어왔을 때), `CSS-Specialist-Fallback`(fallback이 트리거됐을 때만 — 캐시 미스 빈도 감사에 사용).
  7. 배치별 커버리지 측정. <85%이면 `css-test-engineer`를 최대 2회 추가 테스트 작성 사이클 호출.
- **출력**: `../{repo}-css-{slug}` 워크트리의 `css/{slug}` 브랜치 + `.claude/css/executions/exec-log-{slug}-{ts}.md`(slug별 `cache_miss_count` 포함).
- **비용 모델**: 통상 실행 = `/css:review`의 N개 전문가 호출 + execute의 ~0–0.2N개 fallback 호출. naive(캐시 없음)는 2N. ~40–50% LLM 비용 절감 기대.

#### Domain Dispatch Table (GREEN에서 사용)

| 태스크 파일/코드의 패턴 | 전문가 | Spec 산출물 |
|------------------------------|------------|----------------|
| HTTP route, OpenAPI, GraphQL schema, .proto, tRPC router, FastAPI endpoint/service/CRUD | `css-api-specialist` | `api-spec-{slug}-*.md` |
| UI component, composable, Activity, Fragment, React/Vue/Svelte/Angular view, Compose `@Composable` | `css-ui-engineer` | `ui-spec-{slug}-*.md` |
| Alembic migration, SQLAlchemy model, raw SQL, Redis client, ARQ worker | `css-db-specialist` | `db-spec-{slug}-*.md` |
| Dockerfile, docker-compose*.yml, k8s manifest, GitHub/GitLab CI workflow, nginx config | `css-infra-engineer` | `infra-spec-{slug}-*.md` |
| `async def` / `await` / `asyncio.*` / `TaskGroup` / async generator (Python) | `css-async-coder` | `async-spec-{slug}-*.md` |
| `langchain`, `langgraph`, `langfuse`, 또는 벡터 스토어 SDK(`chromadb`, `pinecone`, `weaviate-client`, `qdrant-client`, `faiss`, `langchain_postgres.PGVector`) import; StateGraph/`@tool` 사용; RAG / 임베딩 / 청킹 워크플로 | `css-langgraph-engineer` | `llm-app-spec-{slug}-*.md` |
| LLM 시스템 프롬프트 파일 작성(9-섹션 템플릿 대상) | `css-prompt-engineer` | `prompt-spec-{slug}-*.md` |

첫 매칭 우선(위→아래). 태스크가 여러 행에 매칭되면 지배적 산출물의 전문가가 사용되고, 다른 spec은 보조 컨텍스트로 전달됨.

#### 위임 경계

`css-executor`는 RED scaffold 적용, GREEN 템플릿 적용(캐시된 spec에서의 복사 작업이지 위임이 아님), REFACTOR 오케스트레이션, `git commit`, 워크트리 경계 강제, 커버리지 측정, self-heal 회계, VERDICT 발행, 세션 갱신을 **항상** 소유. execute 단계에서 구현 전문가는 (`css-debugger`가 2회 예산을 소진한 후) 타깃 패치를 만들기 위한 경계 내 fallback(태스크당 최대 1회)으로만 호출됨. 읽기 전용/자문 에이전트(`css-architect`, `css-security-reviewer`, `css-code-reviewer`, `css-code-simplifier`)는 GREEN에서 구현 코드를 절대 작성하지 않음.

#### Rich Spec 출력 형식 (`/css:review`에서 모든 구현 전문가가 생성)

각 `*-spec-{slug}-*.md` 산출물은 executor가 디스크에서 GREEN을 실행할 수 있도록 세 섹션을 반드시 포함:

1. **High-level decisions** — 도메인 수준 패턴, idiom, 라이브러리 선택, 아키텍처 규칙.
2. **Per-Task Implementation Guide** — Dispatch Table이 이 전문가로 라우팅하는 plan 태스크마다 하나의 `## Task {plan-task-id}` 블록, 내용:
   - `Files:` plan 태스크와 일치하는 정확한 경로.
   - `RED scaffold:` executor가 그대로 사용하는 완전·실행 가능한 테스트 코드.
   - `GREEN template:` 완전·실행 가능한 구현 코드.
   - `Edge cases:` 기대 동작과 함께 열거.
   - `Depends-on:` 다른 spec 참조(예: `db-spec-{slug}-*.md#Task N-a`).
3. **Idiom reminders** — GREEN 중 executor가 되뇔 간결한 규칙(예: "TIMESTAMPTZ never naive", "no business logic in endpoints").

전문가의 rich spec에 Dispatch Table이 라우팅한 태스크의 태스크별 블록이 없으면, `css-reviewer`가 이를 finding으로 표시하고 `LOOPBACK_TO_PLAN`을 트리거 — executor가 hit할 캐시 없이 실행되게 절대 두지 않음.

### `/css:verify [--exec-log <log-path>]`

- **Agent**: `css-verifier` (필수 `css-code-reviewer`, `css-security-reviewer` 포함)
- **동작**:
  1. 감지된 커맨드로 워크트리에서 전체 테스트 스위트 실행.
  2. 커버리지 도구 실행, ≥85% 보장.
  3. spec의 각 인수 기준을 구체적 코드/테스트 증거에 매핑.
  4. 항상 병렬 호출:
     - `css-code-reviewer`(코드 품질: 가독성, 네이밍, idiom, 죽은 코드, 잠재 버그, 성능 냄새)
     - `css-security-reviewer`(OWASP, 시크릿 스캔, 의존성 감사)
  5. finding을 단일 평결로 집계: `PASS | LOOPBACK_TO_EXECUTE | ESCALATE`.
     - 어느 reviewer든 CRITICAL 또는 HIGH 보고, 또는 테스트 실패, 또는 커버리지 <85%, 또는 인수 기준 미매핑이면 LOOPBACK_TO_EXECUTE.
     - MEDIUM/LOW 코드 품질 finding은 기록하되 차단하지 않음.
  6. 최대 3회 자동 루프백. 이후 사용자 에스컬레이션.
- **출력**:
  - `.claude/css/verifies/verify-{slug}-{ts}.md` (집계 리포트)
  - `.claude/css/verifies/code-review-{slug}-{ts}.md` (코드 품질 finding)
  - `.claude/css/verifies/security-review-{slug}-{ts}.md` (보안 finding)

### `/css:document [--from-worktree]`

- **Agent**: `css-documenter`
- **동작**:
  1. spec, plan, verify 리포트, 워크트리의 실제 코드 읽기.
  2. `<project>/docs/{slug}/README.md` 생성(개요, 빠른 시작, 사용법, 아키텍처, 테스트, 향후 작업).
  3. 조건부로 `api.md`, `changelog.md` 생성.
  4. 검증된 테스트에서 사용 예제 추출.
  5. 도움이 될 때 다이어그램에 Mermaid 사용.
  6. 워크트리에 `docs(css): add docs for {slug}` 커밋.
- **출력**: `<project>/docs/{slug}/*.md`.

### `/css:pr [--draft]`

- **Agent**: `css-pr-creator`
- **동작**:
  1. `gh` CLI 사용 가능 확인; 아니면 안내와 함께 중단.
  2. `git symbolic-ref refs/remotes/origin/HEAD`로 base 브랜치 감지.
  3. push 전 명시적 사용자 확인 요청(force push 불허).
  4. `git push -u origin css/{slug}`.
  5. PR 본문 조립(Summary / Spec link / Plan link / Test plan / Coverage / Checklist).
  6. `gh pr create`(요청 시 `--draft`).
  7. PR URL 출력.
- **출력**: GitHub PR URL.

### `/css:ship <idea>` (마스터)

- `/css:interview` → `/css:plan` → `/css:review`(자동 루프백) → **Gate 2** → `/css:execute` → `/css:verify`(자동 루프백) → `/css:document` → **Gate 3** → `/css:pr` 오케스트레이션.
- Gate 1은 암묵적(brainstorming 사용자 검토 단계).
- 재개 가능: Ctrl+C 시 `sessions/{slug}.json` 보존; 같은 slug로 재실행하면 resume / restart 질문.

## 에이전트 명세

### 단계 에이전트 (6개)

| 에이전트 | 모델 | 출처 | 핵심 정책 |
|-------|-------|--------|-----------|
| `css-reviewer` | opus | OMC `code-reviewer` + CSS 적응 | Plan review: 커버리지 매트릭스 감사, 전문가 dispatch, plan 평결 |
| `css-executor` | sonnet (복잡 태스크는 opus fallback) | CSS-native | TDD 강제, 워크트리 격리 |
| `css-verifier` | sonnet (opus fallback) | CSS-native | 테스트/커버리지/기준 매핑, 집계 루프백 결정 |
| `css-code-reviewer` | opus (읽기 전용) | OMC `code-reviewer` + CSS 적응(코드 품질 초점) | verify에서의 코드 품질 review: 가독성, 네이밍, idiom, 죽은 코드, 잠재 버그, 성능 냄새 |
| `css-documenter` | sonnet | OMC `document-specialist` + CSS 적응 | docs/{slug}/ 구조, 예제 추출 |
| `css-pr-creator` | haiku | OMC `git-master` + CSS 적응 | gh CLI 워크플로, PR 본문 템플릿, force push 없음 |

**두 reviewer에 대한 노트**: `css-reviewer`(plan reviewer, `/css:review`에서 실행)와 `css-code-reviewer`(코드 품질 reviewer, `/css:verify`에서 실행)는 같은 OMC 출처(`code-reviewer.md`)를 공유하지만 그 방법론을 서로 다른 산출물에 적용. plan reviewer는 plan을 spec과 대조 감사하고 도메인 전문가를 dispatch. code reviewer는 워크트리의 구현 코드를 품질 이슈 측면에서 감사.

### 도메인 전문가 (12개, CSS 헤더와 함께 OMC에서 복사)

전문가는 동작에 따라 두 그룹으로 나뉨:

- **구현 전문가**(`[review, execute]`): `/css:review`에서 spec 산출물을 생성하고, `/css:execute`에서 매칭 태스크의 GREEN 단계를 구현하기 위해 다시 dispatch됨.
- **읽기 전용 / 자문 전문가**: finding 또는 리팩토링 제안만 생성. GREEN에서 프로덕션 코드를 절대 작성하지 않음.

| 에이전트 | 모델 | 도메인 | 단계 | dispatch 출처 |
|-------|-------|--------|--------|-----------------|
| `css-api-specialist` | sonnet | REST/GraphQL/gRPC/tRPC 계약 설계 + 구현 | review, execute | css-reviewer(review, rich spec 생성), css-executor(execute fallback만 — debugger self-heal 소진 후) |
| `css-ui-engineer` | sonnet | Web + Android UI/UX(Material 3, Compose, web 프레임워크) + 구현 | review, execute | css-reviewer(review, rich spec 생성), css-executor(execute fallback만) |
| `css-db-specialist` | sonnet | PostgreSQL, Redis, ARQ, 마이그레이션 + 구현 | review, execute | css-reviewer(review, rich spec 생성), css-executor(execute fallback만) |
| `css-infra-engineer` | sonnet | Docker, K8s, CI/CD, nginx + 구현 | review, execute | css-reviewer(review, rich spec 생성), css-executor(execute fallback만) |
| `css-async-coder` | sonnet | Python asyncio 동시성 + 구현 | review, execute | css-reviewer(review, rich spec 생성), css-executor(execute fallback만) |
| `css-langgraph-engineer` | sonnet | LangChain/LangGraph/LangFuse + 벡터 DB / RAG(Chroma, Pinecone, Weaviate, Qdrant, FAISS, LangChain 경유 pgvector) + 구현 | review, execute | css-reviewer(review, rich spec 생성), css-executor(execute fallback만) |
| `css-prompt-engineer` | opus | 9-섹션 프롬프트 설계 + 작성 | review, execute | css-reviewer(review, rich spec 생성), css-executor(execute fallback만) |
| `css-architect` | opus (읽기 전용) | 시스템 아키텍처, 모듈 경계 | review | css-reviewer(자문) |
| `css-security-reviewer` | opus (읽기 전용) | OWASP, 시크릿, 의존성 감사 | verify, review | css-verifier(항상), css-reviewer(필요 시) |
| `css-test-engineer` | sonnet | 테스트 설계, 커버리지 갭 보완 | execute | css-executor(커버리지 <85% 시) |
| `css-debugger` | sonnet | 근본 원인 분석 | execute | css-executor(GREEN self-heal, 태스크당 최대 2회) |
| `css-code-simplifier` | opus (읽기 전용) | 명료성을 위한 리팩토링 | execute | css-executor(REFACTOR, 제안만) |

### 공통 Frontmatter

```yaml
---
name: css-{role}
description: {one-line role + (CSS pipeline, model)}
model: opus | sonnet | haiku
disallowedTools: [Write, Edit]      # for read-only agents
css_stages: [review]                 # array — an agent may be called from multiple stages
                                     # e.g. security-reviewer: [verify, review]
adapted_from: oh-my-claudecode/agents/{source}.md   # for OMC-derived agents (omit for CSS-native)
---
```

### UI Engineer 플랫폼 전환

`css-ui-engineer`는 플랫폼을 자동 감지:

- `package.json`에 `react`, `vue`, `svelte`, `@angular/core` 등이 있으면 **Web**.
- `build.gradle(.kts)`가 `com.android.application` 또는 `androidx.compose.*` 의존성을 선언하면 **Android**.
- 모노레포에 둘 다 있으면 **둘 다**.

Android의 경우 구체적으로: Material 3, Jetpack Compose 선호(Kotlin), 48dp 터치 타깃, 다크 테마 + 다이내믹 컬러, TalkBack 라벨, 폰트 스케일링, RTL 지원, Compose 부재 시 ConstraintLayout/XML 폴백.

## 데이터 흐름과 상태 관리

### 세션 파일 스키마 (`sessions/{slug}.json`)

```json
{
  "schema_version": "1.0.0",
  "session_id": "uuid-v4",
  "slug": "user-auth-jwt",
  "created_at": "2026-05-27T14:30:00Z",
  "updated_at": "2026-05-27T15:42:11Z",
  "current_phase": "execute",
  "master_flow": true,
  "phases": {
    "interview": { "status": "completed", "artifact": "...", "ambiguity": 0.18, "rounds": 12 },
    "plan":      { "status": "completed", "artifact": "...", "task_count": 9 },
    "review":    { "status": "completed", "artifact": "...", "verdict": "PASS", "attempts": 1 },
    "execute":   { "status": "in_progress", "artifact": "...", "worktree": "...", "branch": "css/user-auth-jwt", "current_batch": 2, "total_batches": 3 },
    "verify":    { "status": "pending" },
    "document":  { "status": "pending" },
    "pr":        { "status": "pending" }
  },
  "retry_counters": { "review": 0, "verify": 0, "execute_tdd_self_heal": { "task_3": 0 } },
  "gates": { "interview_approval": "approved", "execute_approval": "approved", "pr_approval": "pending" },
  "lock": { "phase": "execute", "pid": null, "started_at": "2026-05-27T15:20:00Z" },
  "language_profile": {
    "primary": "kotlin-android",
    "build_tool": "gradle",
    "test_command": "./gradlew testDebugUnitTest",
    "coverage_command": "./gradlew jacocoTestReport",
    "coverage_report_path": "app/build/reports/jacoco/jacocoTestReport/html/index.html",
    "platform": "android",
    "ui_framework": "compose",
    "detected_from": ["build.gradle.kts", "settings.gradle.kts"]
  },
  "last_error": null
}
```

### 세션 해석 (커맨드가 어느 세션에 작용하는가?)

| 호출 | 해석 |
|------------|-----------|
| `/css:ship "<idea>"` | 새 slug 생성; 새 `sessions/{slug}.json` 생성; `_active.json.latest_slug` 갱신. |
| 기존 slug 인자 또는 매칭 idea가 있는 `/css:ship` | 매칭되는 `sessions/{slug}.json`이 존재하고 사용자가 확인하면 재개. |
| `--slug <name>`을 가진 임의의 단독 `/css:*` | `sessions/<name>.json`에 작용(없으면 에러). |
| `--slug` 없는 임의의 단독 `/css:*` | `_active.json.latest_slug` 읽음; 있으면 그 세션에 작용하고 응답 상단에 slug 표시. `_active.json` 없으면 안내와 함께 에러. |

### 재개 시나리오

| 시나리오 | 동작 |
|----------|----------|
| `/css:ship` 중단됨 | `sessions/{slug}.json` 보존; 같은 slug로 재실행 시 resume / restart 질문 |
| 세션 없는 `/css:execute` 단독 | `--plan <path>` 또는 `--slug <name>` 필요 |
| 같은 slug 재실행 | `sessions/{slug}.json.bak.{ts}`로 백업 후 새로 시작; 산출물 파일은 누적(각자 자기 `-{ts}` 보유) |
| slug에 워크트리가 이미 존재 | 질문: reuse / recreate / cancel |

### 동시성 모델

동시성은 프로젝트별이 아니라 **slug별**. 여러 `/css:*` 호출이 서로 다른 slug에 대해 병렬 실행 가능.

- 각 `sessions/{slug}.json`은 자기 `lock` 필드(`{phase, started_at}`)를 가짐.
- **동일 slug 충돌**(예: 두 터미널이 동시에 `/css:execute --slug user-auth-jwt` 시도):
  - 같은 phase + <30분 → 두 번째 거부.
  - 다른 phase + <30분 → 사용자 경고(한 세션이 동시에 두 phase에 있어선 안 되므로 사용자 오류일 가능성).
  - 오래됨(>30분) → 경고와 함께 강제 해제.
- **다른 slug** 호출: 상호작용 없음. 둘 다 진행. 각자 자기 워크트리(`../{repo}-css-{slug}`)와 브랜치(`css/{slug}`) 생성.
- slug 간 유일한 공유 상태는 `~/.claude/css/config.json`(읽기 전용)과 `.git/objects/`(git은 별도 워크트리의 동시 읽기/쓰기에 스레드 안전).

#### 실행 예 — 같은 프로젝트의 두 동시 `/css:ship` 호출

```
Terminal 1:                              Terminal 2:
$ /css:ship "JWT auth middleware"        $ /css:ship "PDF export module"
  → slug = jwt-auth-middleware             → slug = pdf-export-module
  → sessions/jwt-auth-middleware.json      → sessions/pdf-export-module.json
  → worktree ../proj-css-jwt-auth-mw       → worktree ../proj-css-pdf-export-mod
  → branch css/jwt-auth-middleware         → branch css/pdf-export-module
  → independently progresses               → independently progresses
  → independent gates / loopbacks          → independent gates / loopbacks
  → independent PR                         → independent PR
```

두 세션은 서로의 파일을 절대 건드리지 않음. 메인 작업 트리는 둘 모두에 의해 변경되지 않음.

### 언어 감지 로직

```
1. package.json present                 → JS/TS
   - vitest in deps                      → vitest run --coverage
   - jest in deps                        → jest --coverage
   - pnpm/yarn lockfile                  → package manager picked

2. pyproject.toml | setup.py | requirements.txt → Python
   - pytest in deps                      → pytest --cov
   - poetry.lock / uv.lock               → poetry / uv; else pip

3. go.mod                               → Go
   - test: go test -cover ./...

4. Cargo.toml                           → Rust
   - test: cargo test
   - coverage: cargo tarpaulin

5. pom.xml                              → Java + Maven
   - test: mvn test
   - coverage: mvn jacoco:report

6. build.gradle | build.gradle.kts |
   settings.gradle(.kts)                → Java/Kotlin + Gradle
   - test: ./gradlew test
   - coverage: ./gradlew jacocoTestReport (fallback koverHtmlReport)
   - If com.android.application or androidx.compose detected:
       platform=android, ui_framework=compose,
       test: ./gradlew testDebugUnitTest,
       optional: connectedAndroidTest (if emulator)

7. Multiple manifests (monorepo)        → array of language_profiles
   - Each task's Files path resolves which profile

8. None detected                        → ask user in interview, save to session
```

## 에러 처리와 루프백 로직

### 루프백 결정 매트릭스

| 단계 | finding | 결과 |
|-------|---------|--------|
| review | plan의 인수 기준이 spec에 없음(또는 그 반대) | LOOPBACK_TO_INTERVIEW |
| review | plan이 인수 기준을 놓침 | LOOPBACK_TO_PLAN |
| review | 의존성 사이클 / 잘못된 파일 경로 | LOOPBACK_TO_PLAN |
| review | 불완전한 코드 스니펫(TODO/`...`) | LOOPBACK_TO_PLAN |
| review | API/UI 전문가 산출물 누락 | LOOPBACK_TO_PLAN |
| verify | 테스트 실패 | LOOPBACK_TO_EXECUTE |
| verify | 커버리지 <85% | LOOPBACK_TO_EXECUTE |
| verify | 인수 기준 미매핑 | LOOPBACK_TO_EXECUTE |
| verify | api-spec으로부터의 인터페이스 드리프트 | LOOPBACK_TO_EXECUTE |
| verify | UI 접근성 위반(Android <48dp 등) | LOOPBACK_TO_EXECUTE |
| verify | css-code-reviewer가 CRITICAL 또는 HIGH 보고(잠재 버그, 깨진 계약, 심각한 성능 회귀) | LOOPBACK_TO_EXECUTE |
| verify | css-code-reviewer가 MEDIUM/LOW만 보고 | 기록, 차단 안 함 |
| verify | css-security-reviewer가 CRITICAL 또는 HIGH 보고 | LOOPBACK_TO_EXECUTE |

### 카운터

- review 시도 ≤ 2
- verify 시도 ≤ 3
- 태스크별 TDD self-heal ≤ 2

초과 시 → `AskUserQuestion`을 통한 사용자 에스컬레이션, 옵션: 한 번 재시도 / 현재 상태 수락 / 중단 및 보존.

### TDD Self-Heal (executor 내부)

```
RED:
  write tests → run
  if exit 0: abort task ("RED failed: tests did not fail")
  else: continue

GREEN:
  for attempt in 0..2:
    write/patch implementation → run tests
    if exit 0: break
    diagnose with css-debugger → patch hint
  else: abort task, escalate

REFACTOR:
  invoke css-code-simplifier → patch → run tests
  if regression: revert refactor, log warning, proceed
```

### 에러 클래스

| 클래스 | 예 | 처리 |
|-------|---------|----------|
| Validation | 손상된 세션 파일(`sessions/{slug}.json`) | 사전 점검 중단 + 복구 안내 |
| Tool | gh 누락, 워크트리 생성 실패 | 보고 + 대안 제안 |
| Agent | 서브 에이전트 Task 실패 | phase failed 표시, 세션 보존 |
| Policy violation | RED가 실패하지 않음, 워크트리 밖 쓰기 | 즉시 중단, 절대 조용히 처리 안 함 |
| Loopback (정상) | 카운터 내 review/verify | 자동 재시도 |

**원칙**: 조용한 실패 없음. 모든 비정상 종료는 세션 파일에 `last_error`를 기록하고 사용자에게 표면화.

## 마스터 흐름 (`/css:ship`)

```
USER: /css:ship "<idea>"

[ship.md]
1. Resolve session.
   `--slug` provided + sessions/{slug}.json exists → AskUserQuestion: resume / restart / cancel.
   `--slug` provided + no file                       → init that slug.
   No --slug                                          → generate slug from idea (kebab-case),
                                                        ensure no collision with existing
                                                        sessions, init sessions/{slug}.json,
                                                        acquire per-slug lock,
                                                        update _active.json.latest_slug.

2. /css:interview <idea>
   → superpowers:brainstorming runs
   → spec written
   → brainstorming's "user reviews spec" step IS Gate 1

3. /css:plan
   → superpowers:writing-plans runs
   → plan written

4. /css:review (auto-loop)
   loop:
     css-reviewer runs (dispatches domain specialists in parallel)
     verdict == PASS → break
     verdict == LOOPBACK_TO_PLAN → /css:plan (attempts++)
     verdict == LOOPBACK_TO_INTERVIEW → user confirm → /css:interview
     attempts >= 2 → escalate

5. [Gate 2] AskUserQuestion:
   "Plan validated. Worktree '../{repo}-css-{slug}', N batches, M tasks. Start execute?"

6. /css:execute
   → worktree create
   → batch-by-batch TDD with checkpoints
   → all tasks complete

7. /css:verify (auto-loop)
   loop:
     css-verifier runs the test suite + coverage + criteria mapping
     css-code-reviewer + css-security-reviewer run in parallel
     verifier aggregates verdict
     verdict == PASS → break
     verdict == LOOPBACK_TO_EXECUTE → /css:execute --resume (failed tasks only)
     attempts >= 3 → escalate

8. /css:document
   → css-documenter runs
   → docs/{slug}/ written + committed in worktree

9. [Gate 3] AskUserQuestion:
   "Implementation + docs complete. Push 'css/{slug}' and create PR? (draft / normal / cancel)"

10. /css:pr
    → push → gh pr create → print URL

11. Finalize: mark all phases completed, release lock.
```

### 단독 커맨드 동작

`/css:ship` 밖에서 단일 `/css:*`이 호출될 때:

- 게이트 프롬프트가 추가되지 않음 — 사용자가 원하는 바를 안다고 전제.
- 세션 해석은 [세션 해석](#세션-해석-커맨드가-어느-세션에-작용하는가) 규칙을 따름.
- 커맨드는 출력 상단에 작용하는 slug를 표시(예: `[css:plan @ slug=user-auth-jwt]`)하여 사용자가 어느 세션이 갱신되는지 모호하지 않게 함.
- 누락된 선행 산출물은 친절한 안내로 표면화("먼저 `/css:plan --slug <name>`을 실행하거나 `--plan <path>`를 전달하세요").
- 세션 파일은 진행을 계속 추적하여 이후 `/css:ship --slug <name>`으로 전환 시 재개 가능.

## Skill 의존성

### 하드 의존성

- `superpowers:brainstorming` — `/css:interview`
- `superpowers:writing-plans` — `/css:plan`

CSS 커맨드는 진입 시 `~/.claude/settings.json`의 `enabledPlugins["superpowers@claude-plugins-official"]`을 확인. 비활성화되어 있으면 활성화하라는 명확한 지침과 함께 중단.

### 소프트 의존성

| CSS 단계 | Skill | 동작 |
|-----------|-------|----------|
| execute - worktree | `superpowers:using-git-worktrees` | 가능하면 사용; 직접 `git worktree`로 폴백 |
| execute - TDD | `superpowers:test-driven-development` | 가능하면 RED-GREEN-REFACTOR 강제에 사용 |
| execute - debug | `superpowers:systematic-debugging` | self-heal 중 사용 |
| verify | `superpowers:verification-before-completion` | 가드레일로 사용 |

### 외부 도구

- `gh` CLI — `/css:pr`에 필요.
- `git` ≥ 2.5 — 워크트리에 필요.
- 언어별 테스트/커버리지 도구 — 자동 감지; 누락 도구는 사용자에게 질문(interview 단계).

## 테스트 전략

### 1. 에이전트 단위 (수동 + 골든 파일)

```
tests/css/agents/
├── reviewer/
│   ├── input-plan-missing-criteria.md
│   └── expected-verdict.txt
├── api-specialist/
│   ├── input-rest-spec.md
│   └── golden-output-shape.md
└── ...
```

검증: 출력 구조, 평결 형식, 정책 준수(예: reviewer가 절대 동시에 두 질문을 하지 않음).

### 2. 커맨드 통합 (토이 프로젝트)

```
tests/css/fixtures/
├── toy-typescript/
├── toy-python/
├── toy-android/
└── toy-go/
```

픽스처별 시나리오: A(interview happy path), B(spec으로부터 plan), C(TDD 로그와 함께 1 태스크 execute), D(주입된 실패를 verify가 포착).

### 3. 엔드투엔드 (`/css:ship` 주간)

가장 작은 실제 기능, 모든 게이트와 루프백 관찰. PR 생성 확인.

### 4. 커맨드 내 Self-Check 블록

각 커맨드 `.md`는 다음으로 끝남:

```markdown
<self_check>
- [ ] Artifact written to correct path
- [ ] session file (`sessions/{slug}.json`) phase status updated
- [ ] Last line contains VERDICT=... or NEXT=...
- [ ] No policy violations
</self_check>
```

### 5. 회귀 추적

- `.claude/css/`의 산출물은 git 추적됨 → 실행 간 diff가 드리프트를 표면화.
- 같은 시나리오를 두 번 재실행; 산출물의 큰 발산은 불안정한 시스템 프롬프트를 시사.

### 6. 메트릭 (시간에 걸쳐 수집, v1에서 게이팅 임계치 없음)

| 메트릭 | 목표 |
|--------|------|
| interview 평균 라운드 | 8–15 |
| review 루프백률 | <30% |
| verify 루프백률 | <40% |
| TDD self-heal 성공 | >60% |
| /css:ship 엔드투엔드 시간 | 기록만 |

## 보안 가드레일

### 워크트리 격리

- 모든 코드 변경은 `../{repo}-css-{slug}`에서 발생.
- css-executor는 진입 시 `cwd` 검증; 메인 작업 트리에 있으면 중단.
- 워크트리 내부 금지 사항:
  - 직접 `.git/` 수정
  - 메인 작업 트리 경로 접근
  - 워크트리 루트 상위로의 `..` 순회

### 시크릿

- 모든 에이전트 프롬프트에 규칙 포함: API 키 / 비밀번호 / 토큰 / `.env` 값을 직접 작성하지 말 것. 환경 변수나 시크릿 매니저 참조.
- 기존 코드에서 감지된 시크릿 → 산출물에서 마스킹(`***REDACTED***`)하고 사용자에게 보고.
- 권장 `.gitignore` 추가: `.claude/css/state/`(락, ephemeral), `.claude/css/archive/`.

### 에이전트 도구 허용 목록

- 읽기 전용 에이전트: `disallowedTools: [Write, Edit]`(architect, security-reviewer, reviewer, verifier 기본).
- 쓰기 가능 에이전트: 명시적 허용(executor, documenter, pr-creator).
- `Bash` 차단 패턴(사용자 확인 필요): `rm -rf`, `git push --force`, `git reset --hard origin/*`, `chmod 777`.

### 커맨드 진입 가드

- 락 체크(동시성).
- cwd는 git repo(또는 그 워크트리) 내부여야 함.
- 필요 도구 존재(`gh`는 `/css:pr`에서만).
- 실패 시 명확하고 복구 가능한 에러.

### 명시적 사용자 승인

- 워크트리 생성
- 브랜치 push
- PR 생성(draft 또는 normal)
- 오래되지 않은 락의 강제 해제
- 기존 세션 덮어쓰기

## 설치와 배포

### 1단계 — 개인 (현재 목표)

- 파일을 `~/.claude/commands/css/`와 `~/.claude/agents/css/`로 복사.
- dotfiles 또는 설치 스크립트를 통한 머신 간 동기화.

### 2단계 — 비공개 GitHub 저장소 (현재 목표)

저장소 레이아웃:

```
css-claude/                       # private GitHub repo (e.g. github.com/songsub-cha/css-claude)
├── README.md
├── LICENSE                       # personal use license
├── commands/                     # source of truth for ~/.claude/commands/css/
│   └── *.md
├── agents/                       # source of truth for ~/.claude/agents/css/
│   └── *.md
├── config/
│   └── default-config.json       # global defaults
├── scripts/
│   ├── install.ps1               # Windows PowerShell installer
│   ├── install.sh                # Ubuntu 22.04 Bash installer
│   ├── uninstall.ps1
│   └── uninstall.sh
├── docs/
│   ├── specs/                    # design docs (this file)
│   ├── usage.md
│   ├── architecture.md
│   ├── installation.md
│   └── troubleshooting.md
└── tests/
    ├── agents/                   # golden files
    └── fixtures/                 # toy projects
```

#### 배포 시퀀스 (구현 완료 후)

1. 파이프라인 구현이 로컬에 안착하고 통합 테스트 통과.
2. 비공개 GitHub repo 생성(수동: `gh repo create <user>/css-claude --private`).
3. 모든 소스, 스크립트, 문서와 함께 초기 커밋.
4. `v0.1.0` 태그.
5. README에 사전 조건 + 설치 단계 문서화.

#### 사전 조건 (README에 문서화)

- Claude Code 설치.
- `~/.claude/settings.json`에 `superpowers` 플러그인 활성화.
- `gh` CLI 설치 및 인증.
- `git` ≥ 2.5.
- 선택이지만 권장되는 언어별 테스트/커버리지 도구.

### 3단계 — 플러그인 패키징 (보류)

v0.1.0 안정화 후, `/plugin install css`가 가능하도록 Claude Code 플러그인으로 재패키징 고려. v1 범위 아님.

## 설치 스크립트

### Windows PowerShell (`scripts/install.ps1`)

설계(최종 코드는 구현 단계에서):

```powershell
# install.ps1 — Windows installer for CSS
# Usage: irm https://raw.githubusercontent.com/songsub-cha/css-claude/main/scripts/install.ps1 | iex
#    or: .\scripts\install.ps1 -SourcePath .

param(
  [string]$SourcePath = $PSScriptRoot + "\..",
  [switch]$Force
)

# 1. Verify prerequisites
#    - Claude Code config dir: $env:USERPROFILE\.claude
#    - gh.exe in PATH
#    - git in PATH (version ≥ 2.5)
#    - superpowers enabled in ~/.claude/settings.json

# 2. Create directories
#    - ~/.claude/commands/css
#    - ~/.claude/agents/css
#    - ~/.claude/css

# 3. Copy files
#    - commands/*.md → ~/.claude/commands/css/
#    - agents/*.md   → ~/.claude/agents/css/
#    - config/default-config.json → ~/.claude/css/config.json (only if absent or -Force)

# 4. Verify superpowers in settings.json; warn if disabled.

# 5. Print summary: file counts, prerequisite status, next steps.
```

### Ubuntu 22.04 Bash (`scripts/install.sh`)

설계(최종 코드는 구현 단계에서):

```bash
#!/usr/bin/env bash
# install.sh — Ubuntu 22.04 installer for CSS
# Usage: curl -fsSL https://raw.githubusercontent.com/songsub-cha/css-claude/main/scripts/install.sh | bash
#    or: bash scripts/install.sh

set -euo pipefail

SOURCE_PATH="${SOURCE_PATH:-$(dirname "$0")/..}"
CLAUDE_HOME="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
FORCE="${FORCE:-0}"

# 1. Verify prerequisites
#    - $CLAUDE_HOME exists
#    - command -v gh
#    - command -v git; git version ≥ 2.5
#    - jq for settings.json parsing
#    - superpowers enabled in $CLAUDE_HOME/settings.json

# 2. mkdir -p $CLAUDE_HOME/{commands/css,agents/css,css}

# 3. cp -r commands/*.md $CLAUDE_HOME/commands/css/
#    cp -r agents/*.md   $CLAUDE_HOME/agents/css/
#    Only copy default-config.json if absent or FORCE=1.

# 4. Warn if superpowers disabled.

# 5. Summary printout.
```

### 제거기 동작 (양 플랫폼)

- `~/.claude/commands/css/`와 `~/.claude/agents/css/` 제거.
- `~/.claude/css/config.json`과 프로젝트별 `.claude/css/` 산출물 유지(사용자가 명시적으로 제거해야 함).
- 실수 제거를 위한 복원 커맨드 출력.

### 머신별 설정 흐름

1. repo 로컬 클론(또는 릴리스 아카이브 다운로드).
2. 플랫폼에 맞는 설치기 실행.
3. (선택) 개인 기본값을 위해 `~/.claude/css/config.json` 편집.
4. 샘플 프로젝트에서 `/css:ship "<small idea>"` 실행하여 검증.

## 마이그레이션과 제거

### 업데이트

- 비공개 repo에서 pull 또는 설치 스크립트 재실행.
- 진행 중 세션은 영향받지 않음; 산출물은 파일 기반.
- 임의 세션 파일의 스키마 버전 불일치는 마이그레이션 안내를 트리거.

### 제거

- `~/.claude/commands/css/`와 `~/.claude/agents/css/` 삭제.
- 프로젝트 `.claude/css/` 산출물은 보존(사용자 관리).
- 워크트리와 브랜치는 사용자 관리(작업 손실 방지를 위해 자동 삭제 없음).

### 임시 비활성화

- `~/.claude/commands/css/` 이름 변경(예: `_css.bak`로).

## 미해결 질문 / 향후 작업

- **3단계 플러그인 패키징**: 커맨드 + 에이전트를 단일 설치 가능한 Claude Code 플러그인으로 번들.
- **텔레메트리**: 시간에 걸친 프롬프트 드리프트 평가를 위한 opt-in 메트릭 내보내기.
- **Ralph 스타일 지속 루프**: 주변적 자기 교정을 위한 `/css:ship`과의 통합(보류).
- 패키지별 감지를 넘어선 **크로스 언어 모노레포 오케스트레이션**.
- **세션 파일의 클라우드 동기화**: 머신 간 세션 재개를 위한 선택적 GitHub 기반 동기화.

## 리스크와 완화책

| 리스크 | 완화책 |
|------|-----------|
| 긴 프롬프트가 컨텍스트를 넘침 | 단계별 산출물이 파일 기반; 에이전트는 필요한 것만 읽음. brainstorming/writing-plans가 이미 컨텍스트 관리. |
| 취약한 TDD 강제(거짓 RED 통과) | executor가 exit code를 명시적으로 확인. RED가 예상외로 통과하면 계속하지 않고 중단·에스컬레이션. |
| 루프백 무한 루프 | 하드 카운터(review=2, verify=3, self-heal=2). |
| OMC 드리프트가 적응된 에이전트를 깨뜨림 | adapted-from frontmatter가 OMC 경로 인용. 주기적 수동 diff. CSS 특화 오버라이드를 각 에이전트 내부에 문서화. |
| 커버리지 도구 감지 실패 | 폴백: interview에서 사용자에게 질문, language_profile에 저장. |
| 사용자가 실수로 시크릿 커밋 | 에이전트 프롬프트가 금지; verify에서 시크릿 패턴 grep; .gitignore 추가 제안. |
| `/css:ship`이 execute 중 취소될 때 워크트리 오염 | 워크트리는 의도적으로 보존; 정리는 별도의 명시적 커맨드. |

## 용어집

- **CSS**: Claude Super System(이 파이프라인). 웹 CSS와 혼동 금지.
- **Slug**: interview 중 생성된 기능의 kebab-case 식별자.
- **Worktree**: `/css:execute` 중 사용되는 `git worktree`로 격리된 체크아웃.
- **Gate**: `/css:ship`의 사용자 승인 지점. 세 개 존재: interview 후(암묵적), execute 전, PR 전.
- **Loopback**: review 또는 verify의 평결에 기반한 이전 단계로의 자동 재진입.
- **Specialist**: review 단계에서 `css-reviewer`가 호출하는 도메인별 서브 에이전트(api/db/ui/etc.).
- **Master command**: 전체 파이프라인을 실행하는 `/css:ship`.
