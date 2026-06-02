# 도메인 전문가 확대 (Domain Expert Expansion)

CSS 파이프라인의 도메인 전문가를 **7 → 10종**으로 확대하고 3종을 대표 스택으로 강화했습니다. 각 분야는 "가장 많은 유저가 쓰는" 스택 1개 기준으로 채택했습니다.

> 설계: [`docs/superpowers/specs/2026-06-01-domain-expert-expansion-design.md`](../superpowers/specs/2026-06-01-domain-expert-expansion-design.md)

## 신설 (3종)

| 에이전트 | 분야 | 스택 |
|---|---|---|
| `css-node-backend` | 비-Python 백엔드 | **NestJS** 3-layer(controller→service→repository) + DI. Express는 미니멀 대안. Jest+supertest. |
| `css-spring-backend` | Java/Kotlin 백엔드 | **Spring Boot** 3-layer + 생성자 DI. 언어 자동 감지(Kotlin 우선, Java 동등). JUnit5 + MockMvc/WebTestClient + Testcontainers. |
| `css-ml-engineer` | ML 코드/추론 | **scikit-learn + PyTorch** + pandas + Pandera. 피처 파이프라인·데이터 검증·추론 contract·평가 임계·결정성. 비결정적 "학습"은 범위 밖. |

## 강화 (3종)

| 에이전트 | 추가 |
|---|---|
| `css-db-specialist` | **polyglot 데이터 권위**로 확장 — +MongoDB(Beanie/Motor), +JPA/QueryDSL/Flyway(Java), +TypeORM/Mongoose(Node). |
| `css-ui-engineer` | **+Next.js (App Router)** — Server/Client 경계, Server Actions, route handler(thin BFF). |
| `css-infra-engineer` | **+Terraform** — 원격 state(S3+DynamoDB lock), 모듈, AWS 기본 provider, `validate`/`plan`을 RED 게이트. |

`css-api-specialist`는 설명↔본문 드리프트를 제거하기 위해 **Python/FastAPI**로 범위를 명확화했습니다(비-Python은 node/spring로 라우팅).

## 데이터 계층 소유 모델 (대칭)

세 백엔드 모두 **데이터 계층을 `css-db-specialist`에 위임**합니다 — 백엔드는 컨트롤러/서비스/repo 주입만 소유.

| 백엔드 | 백엔드 담당 | 데이터 담당 (`css-db-specialist`) |
|---|---|---|
| Python (FastAPI) | service / endpoint | SQLAlchemy / Beanie |
| Java (Spring) | controller / service / repo 인터페이스 | JPA `@Entity` / QueryDSL / Flyway |
| Node (NestJS) | controller / service / `@InjectRepository` | TypeORM `@Entity`·migration / Mongoose `@Schema` |

엔드포인트 + 신규 엔티티가 한 태스크에 섞이면 `/css:review`가 (백엔드 태스크 + db 태스크, depends-on)로 분해합니다.

## 라우팅 (Domain Dispatch Table)

`agents/executor.md`의 10행 dispatch table이 태스크 파일/코드 패턴 → 전문가를 결정합니다(first-match-wins, 언어/생태계 우선). 핵심 경계:

- 백엔드는 언어로 분리: FastAPI→api, NestJS/Express→node, Spring→spring.
- 모든 엔티티·스키마·마이그레이션·복잡쿼리 → **db** (언어 무관).
- Mongo: Python(Beanie/Motor)·Node(Mongoose) 둘 다 db.
- `css-async-coder`는 Python 전용; Node async는 node-backend.
- langchain/langgraph(LLM 앱)는 ml보다 우선; 순수 torch/sklearn → ml.

## 정합성 가드 — `tools/agent_registry/`

신설/강화가 prose-only라 회귀에 취약하므로, **agents ↔ dispatch table ↔ README 정합성**을 강제하는 테스트를 추가했습니다.

```bash
python -m unittest discover -s tools -t tools -v
```

`check_consistency(repo_root)`가 검사하는 불변식:

1. executor `Domain_Dispatch_Table` == 도메인 전문가 집합(frontmatter `css_stages ⊇ {review, execute}`).
2. 모든 도메인 전문가가 README.md / README.en.md 전문가 표에 문서화(architect 같은 review-only advisory는 추가 허용).
3. README가 존재하지 않는 에이전트를 참조하지 않음.

→ 새 도메인 전문가를 추가하면서 dispatch나 README 갱신을 빠뜨리면 테스트가 **실패(RED)** 합니다. 이것이 향후 확장의 안전망입니다.

## 새 도메인 전문가를 추가하는 법

1. `agents/<name>.md` 작성 (`name: css-<name>`, `css_stages: [review, execute]`, 기존 specialist 구조 미러).
2. `agents/executor.md` Domain_Dispatch_Table에 행 추가.
3. `agents/reviewer.md` 도메인 감지 + 필요 시 분해 예시 추가.
4. `README.md` + `README.en.md` 전문가 표에 행 추가.
5. `python -m unittest discover -s tools -t tools` 가 GREEN인지 확인.
