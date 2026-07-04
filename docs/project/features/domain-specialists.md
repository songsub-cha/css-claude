<!-- css:updated: 079b623 2026-07-04 -->

# 도메인 전문가

## 1. 현재 동작

CSS는 review 단계에서 Rich Spec을 생성하고 execute 단계에서는 캐시 미스일 때만 fallback으로 호출되는 11종 도메인 전문가를 보유합니다(비용 절감 목적, `README.md:104`). 각 전문가는 `agents/*.md` frontmatter에 `css_stages: [review, execute]`를 선언하며, 이 구조적 표식이 "도메인 전문가"의 정의입니다 — `css-architect`는 `css_stages: [review]`만 가져 advisory로 별도 취급됩니다 (`tools/agent_registry/registry.py:6-9`).

| 에이전트 | 전문 영역 | 모델 |
|---|---|---|
| `css-api-specialist` | Python/FastAPI REST·GraphQL, 3-layer(endpoint→service→crud) | sonnet |
| `css-node-backend` | Node.js/NestJS 3-layer(controller→service→repository)+DI | sonnet |
| `css-spring-backend` | Java/Kotlin Spring Boot 3-layer+생성자 DI | sonnet |
| `css-db-specialist` | PostgreSQL/Redis/ARQ + MongoDB + JPA/QueryDSL/Flyway + TypeORM/Mongoose (polyglot 데이터 권위) | sonnet |
| `css-ui-engineer` | Web(React/Vue/Svelte/Angular/Next.js)+Android(Compose) UI | sonnet |
| `css-infra-engineer` | Docker/K8s/CI-CD/nginx/Terraform | sonnet |
| `css-async-coder` | Python asyncio 동시성 (Python 전용) | sonnet |
| `css-langgraph-engineer` | LangChain/LangGraph/LangFuse + 벡터DB/RAG | sonnet |
| `css-ml-engineer` | scikit-learn/PyTorch 피처·추론·평가(테스트 가능한 코드만, 비결정적 "학습"은 범위 밖) | sonnet |
| `css-prompt-engineer` | 9-섹션 프롬프트 설계·리팩토링 | opus |
| `css-architect` | 아키텍처 자문 — review 전용 advisory, `disallowedTools:[Write,Edit]` | opus |

(출처: 각 `agents/<name>.md` frontmatter, `README.md:106-118`.)

## 2. 인터페이스

도메인 전문가는 사용자가 직접 호출하지 않고 `/css:review`(Rich Spec 저작)와 `/css:execute`(캐시 미스 fallback)가 dispatch합니다. 라우팅은 `agents/executor.md`의 `Domain_Dispatch_Table`(10행, `css-architect` 제외)이 결정합니다 (`agents/executor.md:24-37`):

| 패턴 | 전문가 |
|---|---|
| FastAPI endpoint/service/CRUD, Pydantic | `css-api-specialist` |
| NestJS/Express controller/service/DTO | `css-node-backend` |
| Spring controller/service/config/security | `css-spring-backend` |
| Web/Android UI 컴포넌트, Next.js page | `css-ui-engineer` |
| Entity/schema/migration/복잡쿼리/Redis/queue | `css-db-specialist` |
| Docker/compose/K8s/CI/nginx/Terraform | `css-infra-engineer` |
| Python asyncio/TaskGroup/동시성 헬퍼 | `css-async-coder` |
| LangChain/LangGraph/RAG/임베딩/벡터스토어 | `css-langgraph-engineer` |
| torch/sklearn/pandas/Pandera | `css-ml-engineer` |
| LLM 시스템 프롬프트 저작 | `css-prompt-engineer` |

first-match-wins, 언어/생태계 우선 (`docs/domain-expert-expansion/README.md:37-46`).

## 3. 내부 설계 요점

- **데이터 계층 소유 대칭 모델**: 세 백엔드(api/node/spring)는 컨트롤러/서비스/repo 주입만 소유하고, 엔티티·스키마·마이그레이션·복잡 쿼리는 전부 `css-db-specialist`에 위임한다 (`agents/db-specialist.md:11-12`, `docs/domain-expert-expansion/README.md:25-35`).
- **엔드포인트+엔티티 혼재 태스크 분해**: 백엔드 태스크와 db 태스크가 한 태스크에 섞이면 `/css:review`가 (백엔드, db, depends-on) 형태로 분해한다 (`docs/domain-expert-expansion/README.md:35`).
- **정합성 가드**: `tools/agent_registry/registry.py`가 (1) executor dispatch table == 도메인 전문가 집합, (2) 모든 도메인 전문가가 README 표에 문서화됨, (3) README가 존재하지 않는 에이전트를 참조하지 않음을 검사한다 — 위반 시 `python -m unittest discover -s tools -t tools`가 RED (`docs/domain-expert-expansion/README.md:55-61`).
- 신규 도메인 전문가 추가 절차 5단계(agent 파일 작성 → dispatch table 추가 → reviewer 도메인 감지 추가 → 양쪽 README 표 추가 → 테스트 GREEN 확인)는 `docs/domain-expert-expansion/README.md:63-70`.

## 4. 데이터

이 영역은 별도의 영속 데이터를 소유하지 않는다 — 전문가가 설계/구현하는 스키마는 **대상 프로젝트**의 스키마이지 CSS 자신의 스키마가 아니다.

## 5. 제약·알려진 한계

- `css-async-coder`는 Python 전용이며 Node의 비동기 코드는 `css-node-backend`가 자체 소유한다 (`docs/domain-expert-expansion/README.md:44`, D9).
- `css-ml-engineer`는 결정적 추론/평가 코드에 한정되고 비결정적 모델 학습은 범위 밖이다 (`docs/domain-expert-expansion/README.md:13`, D2).
- LangChain/LangGraph가 섞인 LLM 앱은 순수 torch/sklearn보다 `css-langgraph-engineer`가 우선한다 (`docs/domain-expert-expansion/README.md:45`).

## 6. 변경 이력

| 날짜 | slug | 요약 | PR |
|---|---|---|---|
| 2026-06-01 | `domain-expert-expansion` | 도메인 전문가 7→10종 확대(node/spring/ml 신설) + db/ui/infra 강화, 정합성 가드 추가 | 미확인 |
| 2026-07-04 | (bootstrap) | `docs/project/` 최초 생성 — 이 페이지 신설 | — |
