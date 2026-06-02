# Domain Expert Expansion — 설계 문서

- **날짜:** 2026-06-01
- **세션 slug:** `domain-expert-expansion`
- **상태:** 승인 대기 (브레인스토밍 게이트 — 사용자 검토 중, 2차 개정)
- **유형:** CSS 파이프라인 자체 개선 (도메인 전문가 에이전트 확대·강화)

---

## 1. 배경 & 문제

CSS 파이프라인은 `/css:review`에서 **도메인 전문가(specialist) 에이전트**가 rich-spec을 생산하고, `/css:execute`에서 executor가 그 스펙의 RED scaffold / GREEN template를 적용한다. 현재 도메인 전문가는 7종이며, executor의 `Domain_Dispatch_Table`과 reviewer의 도메인 감지 로직이 라우팅을 담당한다.

현재 7종의 기술 커버리지와 락인:

| 전문가 | 분야 | 현재 커버 | 공백 |
|---|---|---|---|
| `css-api-specialist` | 백엔드 API | FastAPI(Python). 설명엔 REST/GraphQL/gRPC/tRPC라 적혀 있으나 본문·예시는 FastAPI 전용 | **Python 전용**, 설명↔본문 계약 불일치 |
| `css-ui-engineer` | 프론트/모바일 | Web(React/Vue/Svelte/Angular) + Android 네이티브(Compose) | 메타프레임워크·크로스플랫폼 없음 |
| `css-db-specialist` | 데이터 계층 | PostgreSQL + Redis + ARQ (SQLAlchemy/Alembic) | **NoSQL 없음, Java(JPA) 없음**, Python ORM 전용 |
| `css-infra-engineer` | 인프라 | Docker/K8s/nginx/CI | **IaC(Terraform) 없음** |
| `css-async-coder` | 동시성 | Python asyncio | Python 전용 |
| `css-langgraph-engineer` | LLM/RAG | LangChain/LangGraph/LangFuse + 벡터DB 6종 | (이번 범위 밖) |
| `css-prompt-engineer` | 프롬프트 | 9-section 템플릿 | (메타, 언어 무관) |

**핵심 문제:** 서버사이드(백엔드 API + 동시성)가 Python에 완전히 묶여 있어, 비-Python 프로젝트는 도메인 전문가의 혜택을 전혀 못 받는다. 특히 **Android 앱의 백엔드는 Spring Boot(Kotlin/Java)를 광범위하게 사용**하는데 이를 위한 백엔드·데이터 전문가가 없다. 또한 NoSQL·IaC·메타프레임워크·ML 같은 대중적 분야가 미커버다.

---

## 2. 목표 & 원칙

- 도메인 전문가를 **7 → 10종**으로 확대하고(신설 3종), **3종을 대표 스택으로 강화**한다(db는 polyglot 데이터 권위로 강화).
- **분야별 "가장 많은 유저가 쓰는" 1개 스택만** 채택한다 (모든 스택 망라 금지).
- 신설 전문가가 실제로 dispatch되도록 **라우팅(executor/reviewer)과 문서(README)를 동시에 동기화**한다.
- prose-only 변경을 회귀로부터 보호하기 위해 **정합성 테스트**(agents ↔ dispatch table ↔ README)를 추가한다.

---

## 3. 범위

### 3.1 In scope

**신설 (3종):**
1. `css-node-backend` — NestJS 기반 비-Python 백엔드.
2. `css-spring-backend` — Java/Kotlin Spring Boot 백엔드 (Android 백엔드 대응).
3. `css-ml-engineer` — scikit-learn/PyTorch 기반 ML 코드/추론.

**강화 (3종):**
4. `css-db-specialist` → **polyglot 데이터 권위**: + **MongoDB**(Beanie/Motor) + **JPA/QueryDSL/Flyway**(Java) + **TypeORM/Mongoose**(Node TS).
5. `css-ui-engineer` + Next.js (App Router).
6. `css-infra-engineer` + Terraform (AWS provider 예시).

**경계 정리 (1종):**
7. `css-api-specialist` 설명을 Python/FastAPI로 축소 (계약 드리프트 제거).

**라우팅·문서·정합성:**
8. `executor.md` Domain_Dispatch_Table 갱신.
9. `reviewer.md` 도메인 감지 + Single-Specialist 분해 예시 갱신.
10. `README.md` / `README.en.md` 전문가 표 갱신.
11. `tools/agent_registry/` 정합성 검사 도구 + unittest 신설.

### 3.2 Out of scope (이번 제외)

크로스플랫폼 모바일(Flutter/RN), `langgraph` + LlamaIndex, Go/.NET 백엔드, Rust, iOS 네이티브, MySQL, Prisma(→ TypeORM 채택), 데이터 엔지니어링(dbt/Airflow). 예제 프로젝트 생성도 제외 — 에이전트 프롬프트만 다룬다.

---

## 4. 확정된 결정 (브레인스토밍 게이트)

| # | 결정 | 선택 | 근거 |
|---|---|---|---|
| D1 | Node 프레임워크 | **NestJS** (primary) | 3-layer+DI 내장으로 기존 FastAPI api-specialist 규율을 TS로 이식 |
| D2 | ML 전문가 초점 | **테스트 가능한 ML 코드/추론** | 피처·검증·추론·평가에 한정. 비결정적 "학습" 제외 → TDD 적합 |
| D3 | Node 데이터 계층 소유 | **db-specialist가 소유** (TypeORM/Mongoose); node-backend는 위임 | 데이터 계층을 단일 권위로 통일 — Python/Java와 대칭 |
| D4 | api-specialist 경계 | **Python/FastAPI로 축소** | node-backend/spring-backend가 타 언어 담당 → 불일치 제거 |
| D5 | NestJS ORM | TypeORM (Prisma 아님) | NestJS 1st-party, DI 통합 repository |
| D6 | Python MongoDB | Beanie(+Motor) | async ODM, Pydantic Document — FastAPI 정합 |
| D7 | Next.js | App Router + Server/Client 경계 | 현행 권장 기본값 |
| D8 | Terraform provider 예시 | AWS | 최다 유저 클라우드 |
| D9 | Node 동시성 | node-backend 자체 소유 | 신규 async 에이전트 불필요 |
| **D10** | **Spring 백엔드 신설** | **css-spring-backend (Java+Kotlin)** | **Android 백엔드가 Spring Boot 광범위 사용. 언어는 프로젝트 감지(.kt/build.gradle.kts→Kotlin, .java/pom.xml→Java). Android-인접 맥락상 예시는 Kotlin 우선, Java 동등 지원** |
| **D11** | **Java 데이터 계층 소유** | **db-specialist가 JPA/QueryDSL 소유** | **사용자 요청. spring-backend는 db-specialist에 위임(Python api↔db 분리 패턴과 동일)** |
| **D12** | **Spring 빌드/마이그레이션** | **Gradle(Kotlin DSL) 기본·Maven 대안 / Flyway 기본·Liquibase 대안** | **각 분야 최다 유저** |

### 4.1 데이터 계층 소유 모델 (중요 — db-specialist 단일 권위)

| 백엔드 | 백엔드 담당 | 데이터 계층 담당 | 패턴 |
|---|---|---|---|
| Python (FastAPI) | `api-specialist` (service/endpoint) | `db-specialist` (SQLAlchemy/Beanie) | **분리** |
| Java (Spring) | `spring-backend` (controller/service, Spring Data repo 인터페이스 선언) | `db-specialist` (JPA @Entity·QueryDSL·Flyway) | **분리** |
| Node (NestJS) | `node-backend` (controller/service, `@InjectRepository` 와이어링) | `db-specialist` (TypeORM @Entity·migration, Mongoose schema) | **분리** |

→ 세 백엔드 모두 **데이터 계층을 db-specialist에 위임**(대칭). db-specialist가 Python(SQLAlchemy/Beanie)·Java(JPA/QueryDSL)·Node(TypeORM/Mongoose) + Postgres/Redis/ARQ/Mongo를 아우르는 **polyglot 데이터 권위**. 백엔드는 service/controller/repo 주입·인터페이스 선언만 소유.

---

## 5. 상세 설계

### 5.1 신설 — `agents/node-backend.md` (`css-node-backend`)

Frontmatter: `name: css-node-backend`, `model: sonnet`, `css_stages: [review, execute]`.

- **Role** — NestJS 3-layer. controller(HTTP만)→service(비즈니스)→repository(데이터 접근 와이어링). **데이터 계층(TypeORM @Entity·migration, Mongoose schema)은 db-specialist에 위임**(§4.1). *Python은 api-specialist, Java는 spring-backend, 인프라는 infra-engineer*.
- **Used_By_CSS** — review에서 rich-spec(`node-spec-{slug}-{ts}.md`), execute fallback (기존 cache-first 계약).
- **Why_This_Matters** — 계층 혼재(컨트롤러에 비즈니스 로직, 서비스에 Request 누수)가 가장 흔한 실패. NestJS DI 경계가 예방.
- **Success_Criteria** — controller는 라우팅/검증/직렬화만; service에 모든 비즈니스; repository는 주입된 TypeORM/Mongoose 사용만; DTO는 class-validator 검증; 전역 exception filter; 구조화 로깅(correlation id); `any` 금지(strict TS); 모든 I/O async; 외부 HTTP timeout 명시.
- **Per-Task Implementation Guide** — `## Task {id}` (Files / RED = Jest+supertest e2e·unit / GREEN = module+controller+service+DTO + 주입된 repository 사용 / Edge cases / **Depends-on: db-spec의 TypeORM @Entity·Mongoose schema 섹션**).
- **Idiom reminders** — "controller에 비즈니스 로직 금지", "service는 Request/Response 미수신", "DTO ValidationPipe 필수", "엔티티/스키마는 db-spec 참조", "Promise.all은 bounded(p-limit)".
- **Stack** — NestJS / `@InjectRepository`로 주입된 TypeORM repository·Mongoose model **사용**(엔티티·스키마 정의는 db-specialist) / class-validator+class-transformer / @nestjs/config / @nestjs/axios(또는 fetch) / Jest+supertest / npm(기본). Express는 미니멀 대안.
- **데이터 위임** — 엔티티/스키마/마이그레이션은 직접 정의하지 않고 db-spec의 `## Task` 섹션을 depends-on으로 참조. service는 주입된 repository를 통해 접근. 공용 데이터 원칙(시간 UTC, 돈 decimal, FK 인덱스)도 db-spec 소유.

### 5.2 신설 — `agents/spring-backend.md` (`css-spring-backend`)

Frontmatter: `name: css-spring-backend`, `model: sonnet`, `css_stages: [review, execute]`.

- **Role** — Java/Kotlin Spring Boot 3-layer. `@RestController`(HTTP만)→`@Service`(비즈니스)→Spring Data repository(데이터 접근). **엔티티 매핑·복잡 쿼리(QueryDSL)·마이그레이션(Flyway)은 db-specialist에 위임**(§4.1). *Python은 api-specialist, Node는 node-backend, 인프라는 infra-engineer*.
- **Used_By_CSS** — review에서 rich-spec(`spring-spec-{slug}-{ts}.md`), execute fallback.
- **Why_This_Matters** — 컨트롤러에 비즈니스 로직 누수, 필드 주입, 엔티티를 API 응답으로 직접 노출, 블로킹 I/O가 흔한 실패. Spring DI 경계 + 계층 규율이 예방.
- **Success_Criteria** — controller는 HTTP/검증/직렬화만; service에 비즈니스 + `@Transactional` 경계; repository는 Spring Data 인터페이스; **DTO ≠ Entity**(엔티티 직접 직렬화 금지); Bean Validation(Jakarta `@Valid`); 전역 `@RestControllerAdvice` 예외 처리; 생성자 주입(필드 `@Autowired` 금지); 구조화 로깅; N+1 회피(fetch join/EntityGraph — 쿼리 설계는 db-specialist 협업).
- **Per-Task Implementation Guide** — `## Task {id}` (Files / RED = JUnit5 + `@WebMvcTest`(MockMvc) / `@SpringBootTest`+`WebTestClient` + Testcontainers(통합) / GREEN = controller+service+repository 인터페이스+DTO+검증 / Edge cases = 검증 실패→400, 미존재→404, 충돌→409, 트랜잭션 롤백 / Depends-on = db-spec의 @Entity·QueryDSL 섹션).
- **Idiom reminders** — "생성자 주입", "DTO/Entity 분리(record/data class)", "@Transactional은 service 계층", "controller에서 repository 직접 호출 금지", "Kotlin은 nullable 명시·data class DTO".
- **Stack** — Spring Boot(Spring Web; 리액티브 필요 시 WebFlux 옵션) / Spring Data JPA / Spring Security / Bean Validation. **언어: 프로젝트 감지**(`build.gradle.kts`+`.kt`→Kotlin, `pom.xml`/`.java`→Java); 예시는 Kotlin 우선(Android-인접), Java 동등. **빌드: Gradle(Kotlin DSL) 기본 / Maven 대안. 테스트: JUnit5 + Spring Boot Test + MockMvc/WebTestClient + Testcontainers.**
- **Boundary note** — spring-backend는 **단순 파생 쿼리용 Spring Data repository 인터페이스 선언** + service/controller/보안 소유. **`@Entity` 매핑, QueryDSL 복잡·동적 쿼리, Flyway 마이그레이션은 db-specialist**(§5.4). Python·Node와 동일하게 데이터 계층은 db-specialist에 위임(§4.1, 대칭).

### 5.3 신설 — `agents/ml-engineer.md` (`css-ml-engineer`)

Frontmatter: `name: css-ml-engineer`, `model: sonnet`, `css_stages: [review, execute]`.

- **Role** — scikit-learn/PyTorch 기반 ML 코드. 피처 엔지니어링, 데이터 검증, 추론 서비스, 평가 하니스. *추론 HTTP 노출은 api-specialist, 모델 호스팅 인프라는 infra-engineer*.
- **Used_By_CSS** — review rich-spec(`ml-spec-{slug}-{ts}.md`), execute fallback.
- **Why_This_Matters** — 데이터 누수(test에 fit), 비결정성(시드 미고정), train/inference 코드 혼재가 조용한 실패를 만든다.
- **Success_Criteria** — `fit`은 train split에만; 시드 고정으로 결정적; 피처 변환은 sklearn Pipeline/ColumnTransformer로 캡슐화; 데이터프레임은 **Pandera** 스키마 검증; 추론은 입력/출력 contract·shape 테스트; 평가는 명시적 임계값 테스트; 모델 아티팩트 버전화; train/inference 분리.
- **Per-Task Implementation Guide** — `## Task {id}` (Files / RED = pytest: 피처 변환·Pandera·추론 shape·결정성·평가 임계 / GREEN = Pipeline·검증 스키마·추론 래퍼·평가 함수 / Edge cases = 결측·dtype 불일치·빈 입력·shape mismatch / Depends-on = 추론 엔드포인트는 api-spec).
- **Idiom reminders** — "test 데이터로 fit 금지", "시드 고정", "원시 학습 루프보다 Pipeline", "추론은 순수 함수".
- **Stack** — scikit-learn / PyTorch / pandas / Pandera / pytest / uv. MLflow는 실험 추적 옵션.
- **Boundary note** — LLM/RAG(`langchain` 등)는 langgraph-engineer. langchain 미사용 순수 ML만 담당.

### 5.4 강화 — `css-db-specialist` (+ MongoDB, + JPA/QueryDSL)

기존 PostgreSQL/Redis/ARQ 섹션 유지. 두 블록 추가:

**(a) MongoDB (Python):**
- **Stack** — Beanie(async ODM, Pydantic `Document`) + Motor. PyMongo는 동기 스크립트용으로만.
- **Success_Criteria** — 모든 쿼리 인덱스 근거; 복합·TTL 인덱스 명시; 컬렉션 스키마 검증(`$jsonSchema`/Beanie); aggregation 페이지네이션; unbounded find 금지(projection·limit); datetime UTC 저장.
- **Reference** — Beanie Document + 인덱스 + aggregation 예시.

**(b) Java 데이터 계층 — JPA + QueryDSL (D11):**
- **Stack** — JPA(Hibernate): `@Entity`/`@Table`/`@Column`/관계 매핑, `@Index`, 페치 전략(LAZY 기본 + 명시적 fetch join/EntityGraph로 N+1 회피). QueryDSL: `Q`-type 기반 type-safe 동적 쿼리, `JPAQueryFactory`, 프로젝션. 마이그레이션: **Flyway**(기본, `V{ver}__{desc}.sql`) / Liquibase 대안.
- **Success_Criteria** — money=`BigDecimal`(절대 double 아님); 시간=`Instant`/`OffsetDateTime`(UTC); 모든 FK 인덱스; 동적 쿼리는 문자열 JPQL 대신 QueryDSL; Flyway 마이그레이션은 immutable(적용분 수정 금지, 새 버전 추가); 엔티티는 DTO와 분리.
- **Reference** — `@Entity`(Kotlin/Java) + QueryDSL 동적 쿼리 + Flyway 마이그레이션 예시.

**(c) Node 데이터 계층 — TypeORM + Mongoose (TypeScript) [D3]:**
- **Stack** — TypeORM: `@Entity`/`@Column`/관계, `@Index`, 마이그레이션(`typeorm migration:generate/run`), 복잡 쿼리는 QueryBuilder. Mongoose: `@Schema`/`SchemaFactory`, 인덱스, 검증.
- **Success_Criteria** — money=`decimal`(string 모드)·시간 UTC; 모든 FK/참조 인덱스; 동적 쿼리는 QueryBuilder; 마이그레이션 immutable; 엔티티 ≠ DTO. NestJS DI 호환(repository 주입 가능 형태).
- **Reference** — TypeORM `@Entity` + migration + QueryBuilder, Mongoose schema + 인덱스 예시.

**Boundary note** — **모든 데이터 계층(Python SQLAlchemy/Beanie · Java JPA/QueryDSL/Flyway · Node TypeORM/Mongoose)은 db-specialist 소유.** 백엔드(api/spring/node)는 service·controller·repository 주입/사용/인터페이스 선언만 소유하고, 엔티티·스키마·마이그레이션은 db-spec을 depends-on으로 참조. db-specialist는 언어 무관 데이터 권위.

**공용 "데이터 설계 원칙" 섹션** — node-backend/spring-backend가 인용하도록 언어 무관 원칙(시간 UTC, 돈 decimal, FK 인덱스, 마이그레이션 안전, 캐시 키 스킴, 멱등 잡)을 명시적 섹션으로 분리.

### 5.5 강화 — `css-ui-engineer` + Next.js

- **Platform_Detection 확장** — `package.json`에 `next` → Next.js(App Router) 모드.
- **Stack** — App Router(`app/` 라우팅), Server vs Client Component(`'use client'`) 경계, Server Actions, route handler(`route.ts`), `loading.tsx`/`error.tsx`, `metadata`.
- **Success_Criteria 추가** — Server/Client 경계 명시(기본 Server, 상호작용만 Client); 데이터 페치는 Server Component; 캐시/`revalidate` 전략 명시; route handler는 얇은 BFF(무거운 백엔드는 node-backend/spring-backend/api-specialist).
- **Per-Task Guide** — RED에 React Testing Library + 서버 컴포넌트 렌더 스모크.

### 5.6 강화 — `css-infra-engineer` + Terraform

- **Stack** — HCL, 모듈, provider(예시 AWS: VPC/ECS·EKS/RDS/S3), 원격 state(S3 + DynamoDB lock), `plan`/`apply`/`validate`/`fmt`, 버전 핀.
- **Success_Criteria 추가** — 원격 state + 잠금; 하드코딩 시크릿 금지(변수·SSM); provider 버전 핀; 모듈화; `terraform validate`+`plan`+`fmt -check`를 RED/lint 단계로.
- **Per-Task Guide** — RED = `terraform validate`/`plan` 실패 출력; GREEN = `.tf`(provider+resource+variables+outputs) + 백엔드 설정.

### 5.7 경계 정리 — `css-api-specialist`

- Frontmatter `description`·Role을 **"Python/FastAPI REST/GraphQL(Strawberry/Ariadne) API"**로 축소. gRPC/tRPC/언어무관 문구 제거(또는 "Node→node-backend, Java→spring-backend" 위임 명시).
- 본문(FastAPI 전용)은 유지 — 이제 설명과 일치.

### 5.8 라우팅 동기화 — `executor.md` Domain_Dispatch_Table

**최종 행 순서 (top-to-bottom, first-match-wins). 언어/생태계 우선 → 도메인 순. 10 specialist 행.**

| # | 패턴 | Specialist | spec 아티팩트 |
|---|---|---|---|
| 1 | FastAPI endpoint/service/CRUD, Pydantic schema, Python REST/GraphQL(Strawberry/Ariadne) | `css-api-specialist` | `api-spec-{slug}-*.md` |
| 2 | NestJS module/controller/provider/service, Express router, `*.controller.ts`/`*.service.ts`/`*.module.ts`, `@InjectRepository` 와이어링, class-validator DTO | `css-node-backend` | `node-spec-{slug}-*.md` |
| 3 | Spring `@RestController`/`@Service`/`@Configuration`/`@SpringBootApplication`, Spring Security, Bean Validation DTO, Spring Data `JpaRepository` 인터페이스 선언, `*.java`/`*.kt` Spring + `build.gradle(.kts)`/`pom.xml` Spring deps | `css-spring-backend` | `spring-spec-{slug}-*.md` |
| 4 | UI component/composable/Activity/Fragment/React·Vue·Svelte·Angular view/Compose `@Composable`, Next.js `app/**/page.tsx`·`route.ts`·`'use client'`·Server Action | `css-ui-engineer` | `ui-spec-{slug}-*.md` |
| 5 | Alembic/SQLAlchemy/raw SQL(Python), Redis(redis-py), ARQ worker, Beanie/Motor/pymongo(Python Mongo), **JPA `@Entity`/`@Table`/관계, QueryDSL `Q`-type/`JPAQueryFactory`, Flyway/Liquibase, TypeORM `@Entity`/migration/QueryBuilder, Mongoose `@Schema`/`SchemaFactory`** (모든 엔티티·스키마·마이그레이션) | `css-db-specialist` | `db-spec-{slug}-*.md` |
| 6 | Dockerfile, docker-compose, k8s manifest, GitHub/GitLab CI, nginx, Terraform `*.tf`/HCL/모듈 | `css-infra-engineer` | `infra-spec-{slug}-*.md` |
| 7 | `async def`/`await`/`asyncio.*`/`TaskGroup`/async generator **(Python only)** | `css-async-coder` | `async-spec-{slug}-*.md` |
| 8 | `langchain`/`langgraph`/`langfuse`/벡터스토어 SDK; StateGraph/`@tool`; RAG/임베딩/청킹 | `css-langgraph-engineer` | `llm-app-spec-{slug}-*.md` |
| 9 | `import torch`/`sklearn`/`pandas`, Pandera schema, `.fit(`/`.predict(`/`.transform(`, mlflow, 피처 파이프라인, 추론 래퍼 (langchain 미사용) | `css-ml-engineer` | `ml-spec-{slug}-*.md` |
| 10 | LLM system-prompt 파일(9-section) | `css-prompt-engineer` | `prompt-spec-{slug}-*.md` |

**순서·경계 근거:**
- 백엔드 3종은 언어로 분리: Python(행1)·TS(행2)·Java/Kotlin(행3). 파일 시그니처가 달라 충돌 없음.
- **백엔드↔데이터 경계(전 언어 공통):** 컨트롤러/서비스/repo 주입·인터페이스 선언 → 백엔드 행(1·2·3). 엔티티 매핑·복잡 쿼리·마이그레이션 → 행5(db). 보통 별도 파일(`*.entity.ts`/`*Entity.kt`/`*.schema.ts`/`models.py` vs `*.controller.*`/`*.service.*`)이라 분리되며, 혼재 task는 reviewer가 분해(§5.9).
- **데이터 계층 일원화:** 모든 ORM/ODM 엔티티·스키마·마이그레이션(SQLAlchemy/JPA/QueryDSL/TypeORM/Mongoose/Beanie/Flyway/Alembic) → 행5(db). 언어 무관 단일 권위.
- langgraph(행8)가 ml(행9)보다 먼저라 LLM 앱은 langgraph로, 순수 torch/sklearn은 ml로. async-coder(행7)는 "Python only"(Node async는 행2).

### 5.9 라우팅 동기화 — `reviewer.md`

- **Investigation_Protocol step 4** 도메인 감지 확장: "Python HTTP(FastAPI)→api; Node HTTP(NestJS/Express)→node-backend; **Java/Kotlin HTTP(Spring `@RestController`)→spring-backend**; **모든 엔티티·스키마·마이그레이션·복잡쿼리(SQLAlchemy/Alembic/JPA/QueryDSL/Flyway/TypeORM/Mongoose/Beanie)→db**; component/Next.js→ui; Docker/CI/Terraform→infra; `async def`→async; langchain→llm-app; torch/sklearn/Pandera→ml; system-prompt→prompt".
- **Single_Specialist_Task_Rule 분해 예시 추가:**
  - **PyTorch 추론 엔드포인트** → `api-specialist`(endpoint) + `ml-engineer`(모델 로드/추론), depends-on.
  - **Next.js 페이지 + 엔드포인트** → `ui-engineer`(page/component) + (`api-specialist`|`node-backend`|`spring-backend`)(endpoint) + executor-direct 와이어링.
  - **Spring 엔드포인트 + 신규 엔티티/QueryDSL 쿼리** → `spring-backend`(controller/service/repo 인터페이스/DTO) + `db-specialist`(`@Entity` 매핑·QueryDSL 구현·Flyway 마이그레이션), depends-on.
  - **NestJS endpoint + Mongo/TypeORM** → `node-backend`(controller/service/DTO + repository 주입) + `db-specialist`(Mongoose `@Schema`/TypeORM `@Entity`·migration·인덱스), depends-on.
  - *세 백엔드(Python·Java·Node) 모두 데이터 계층을 db-specialist로 분해(대칭). 백엔드 task가 엔티티/스키마/마이그레이션을 직접 포함하면 분해 필요.*

### 5.10 문서 동기화 — `README.md` / `README.en.md`

전문가 표(7행 → 10행):
- 추가 `css-node-backend` | NestJS (controller/service/DI; 데이터는 db-specialist 위임) | sonnet
- 추가 `css-spring-backend` | Java/Kotlin Spring Boot (3-layer + DI) / Spring Data JPA · Security | sonnet
- 추가 `css-ml-engineer` | scikit-learn / PyTorch / 피처·추론·평가 (테스트 가능 코드) | sonnet
- 수정 `css-api-specialist` | **Python/FastAPI** REST / GraphQL API 설계 | sonnet
- 수정 `css-db-specialist` | (polyglot 데이터) PostgreSQL/Redis/ARQ **+ MongoDB + JPA/QueryDSL + TypeORM/Mongoose** | sonnet
- 수정 `css-ui-engineer` | Web (React/Vue/Svelte/Angular **+ Next.js**) + Android (Compose) | sonnet
- 수정 `css-infra-engineer` | Docker / K8s / CI-CD / nginx **+ Terraform** | sonnet

### 5.11 정합성 강제 — `tools/agent_registry/`

prose-only 변경을 회귀로부터 보호하고, execute 단계에 TDD 대상(RED→GREEN)을 제공.

**모듈:**
- `tools/agent_registry/__init__.py`
- `tools/agent_registry/registry.py`:
  - `parse_agent_files(agents_dir) -> dict[name -> {model, css_stages, path}]` — `agents/*.md` frontmatter 파싱.
  - `parse_dispatch_specialists(executor_md_path) -> set[str]` — Domain_Dispatch_Table 행에서 `css-*` 추출.
  - `parse_readme_specialists(readme_md_path) -> set[str]` — 전문가 표에서 `css-*` 추출.
  - `check_consistency(repo_root) -> list[str]` — 위반 목록:
    1. dispatch table의 모든 specialist는 동일 `name`의 agent 파일 존재.
    2. dispatch table의 모든 specialist는 README(ko/en) 표에 존재.
    3. README 표의 모든 specialist는 agent 파일 존재.
    4. (역방향) `css_stages`에 review+execute를 가진 agent 중 dispatch 미등재 시 경고. process agent 화이트리스트 제외: executor/reviewer/architect/code-reviewer/code-simplifier/debugger/test-engineer/documenter/verifier/security-reviewer/pr-creator.
- `tools/agent_registry/test_registry.py` — `unittest`로 `check_consistency(repo_root)`가 빈 리스트 반환 단언. dispatch table이 진실의 원천.

**TDD 흐름:** test 먼저(RED: 신설 specialist가 dispatch엔 있으나 agent 파일/README 미존재로 실패) → agent 파일·dispatch 행·README 행 추가(GREEN).

---

## 6. 수용 기준 (테스트 가능)

1. `agents/node-backend.md` 존재: `name: css-node-backend`, `css_stages: [review, execute]`, Role/Used_By_CSS/Success_Criteria/Per-Task Guide/Idiom 섹션 + 데이터 계층 db-specialist 위임 경계 명시.
2. `agents/spring-backend.md` 존재: `name: css-spring-backend`, 동일 구조 + 언어 감지(Java/Kotlin) + db-specialist 위임 경계 명시.
3. `agents/ml-engineer.md` 존재: `name: css-ml-engineer`, 동일 구조.
4. `db-specialist`에 MongoDB(Python) + JPA/QueryDSL/Flyway(Java) + TypeORM/Mongoose(Node TS) 블록 + 공용 데이터 원칙 섹션 추가; `ui-engineer` Next.js; `infra-engineer` Terraform.
5. `api-specialist` 설명이 Python/FastAPI로 축소.
6. `executor.md` Domain_Dispatch_Table이 §5.8 순서·패턴과 일치(10 specialist 행).
7. `reviewer.md` 도메인 감지 + 분해 예시(§5.9): 세 백엔드(Python·Java·Node) 모두 데이터 계층을 db-specialist로 분해(대칭).
8. `README.md` + `README.en.md` 전문가 표가 10행, 설명 §5.10과 일치.
9. `tools/agent_registry/test_registry.py` 통과(agents ↔ dispatch ↔ README 정합).
10. 기존 `tools/css_schema` 테스트 전부 통과(회귀 없음).

---

## 7. 검증 방법

- `python -m unittest discover -s tools -t tools -v` — agent_registry + css_schema 단위 테스트.
- 행동 체크리스트(수동): 신설 3종이 기존 specialist의 rich-spec 구조(High-level decisions + Per-Task RED/GREEN + Idiom)를 충실히 미러링하는지, dispatch table 패턴이 실제 파일 시그니처와 매칭되는지, Spring↔db 위임 경계가 명확한지.
- 커버리지 임계 85%는 `tools/agent_registry` Python 코드에 적용. 마크다운 프롬프트는 정합성 테스트 + 체크리스트로 검증.

---

## 8. 리스크 & 완화

| 리스크 | 완화 |
|---|---|
| Dispatch 순서 모호성(언어 교차 패턴) | §5.8 언어 한정자 명시 + 정합성 테스트(존재성). 라우팅 *정확성*은 reviewer 분해 예시로 보강 |
| 백엔드↔db 경계 혼동(엔티티/쿼리 누가?) | §4.1 + §5.4 boundary note + §5.9 분해 예시(3 백엔드 대칭) |
| db-specialist가 3언어(Py/Java/TS) 데이터 계층 — 비대해짐 | 언어별 명확한 하위 섹션(SQLAlchemy/JPA/QueryDSL/TypeORM/Mongoose/Mongo) + 공용 원칙 분리. 백엔드는 depends-on만 |
| 에이전트 prose 품질 단위테스트 불가 | 행동 체크리스트 + 기존 구조 미러링 |
| agent_registry 파서가 마크다운 표 포맷에 취약 | 관대한 정규식 + 실패 시 명확한 메시지, fixtures 테스트 |

---

## 9. 작업 단위 (plan 단계에서 task로 분해)

1. `tools/agent_registry/` 파서 + consistency 검사 + unittest (RED 먼저 — 회귀 가드).
2. `agents/node-backend.md` 신설.
3. `agents/spring-backend.md` 신설.
4. `agents/ml-engineer.md` 신설.
5. `db-specialist` 강화(MongoDB + JPA/QueryDSL + 공용 원칙 섹션) / `ui-engineer`(Next.js) / `infra-engineer`(Terraform) 편집.
6. `api-specialist` 경계 축소.
7. `executor.md` Domain_Dispatch_Table 갱신(10행).
8. `reviewer.md` 감지 + 분해 예시 갱신.
9. `README.md` + `README.en.md` 표 갱신(10행).
10. 정합성·기존 테스트 그린 확인.

> 작업 1이 나머지의 회귀 가드. 2~9는 1의 테스트를 GREEN으로 만드는 변경.
