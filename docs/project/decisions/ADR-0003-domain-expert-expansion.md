<!-- css:updated: 079b623 2026-07-04 -->

# ADR-0003: 도메인 전문가 확장과 데이터 계층 위임

- **상태**: accepted
- **날짜**: 2026-06-01
- **출처**: `docs/superpowers/specs/2026-06-01-domain-expert-expansion-design.md:68-93` (확정된 결정 D1–D12)

## 배경 (Context)

기존 7종 도메인 전문가는 Python/FastAPI(웹), 범용 async, DB, UI, 인프라만 커버해 Node.js·Java/Kotlin·ML 스택 프로젝트에서 커버리지 공백이 있었다. 또한 `css-api-specialist`의 설명과 실제 범위(Python 한정 vs 범용) 사이에 드리프트가 있었다.

## 결정 (Decision)

- Node 백엔드 신설: **NestJS**(3-layer+DI)를 primary로 채택(D1).
- ML 전문가는 **테스트 가능한 ML 코드/추론**에 한정 — 비결정적 "학습"은 범위 밖(D2).
- Node 데이터 계층은 `db-specialist`가 소유(TypeORM/Mongoose), node-backend는 위임(D3) — Python/Java와 대칭.
- `api-specialist`는 **Python/FastAPI로 범위 축소**(D4).
- NestJS ORM은 TypeORM(Prisma 아님, D5); Python MongoDB는 Beanie+Motor(D6); Next.js는 App Router(D7); Terraform 예시는 AWS(D8); Node 동시성은 node-backend 자체 소유(D9).
- Spring 백엔드 신설: **css-spring-backend**(Java+Kotlin, 언어는 프로젝트 감지)(D10).
- Java 데이터 계층은 `db-specialist`가 JPA/QueryDSL 소유, spring-backend는 위임(D11).
- Spring 빌드/마이그레이션 기본값은 Gradle(Kotlin DSL)/Flyway, Maven/Liquibase는 대안(D12).
- 모든 백엔드(Python/Java/Node)는 데이터 계층을 `db-specialist` 단일 권위에 위임하는 대칭 모델을 확정.

## 결과 (Consequences)

- 도메인 전문가가 7→10종(신설 3, architect 포함 11 표기 관례)으로 늘었고, `db-specialist`가 polyglot 데이터 권위(Postgres/Redis/ARQ/Mongo + JPA/QueryDSL/Flyway + TypeORM/Mongoose)가 되었다.
- prose-only 확장은 회귀에 취약하므로 `tools/agent_registry/`가 agents↔dispatch table↔README 정합성을 테스트로 강제하게 되었다(`docs/domain-expert-expansion/README.md:47-61`).
- 엔드포인트+엔티티가 한 태스크에 섞이면 `/css:review`가 (백엔드, db, depends-on)로 분해해야 하는 추가 복잡도가 생겼다.
- 신규 도메인 전문가 추가 시 5단계 절차(agent 파일→dispatch table→reviewer 감지→양쪽 README→테스트 GREEN)를 반드시 따라야 한다.
