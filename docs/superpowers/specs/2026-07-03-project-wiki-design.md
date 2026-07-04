# /css:wiki — 프로젝트 살아있는 문서(SoT) 큐레이션 설계

- **상태**: Draft (브레인스토밍 승인 완료, 구현 계획 대기)
- **작성일**: 2026-07-03
- **대상**: 신규 `/css:wiki` 커맨드 + 신규 `css-doc-curator` 에이전트 + `lib/gh_sync.sh` 확장
- **요지**: slug·이슈 단위로 파편화된 사건 기록을 in-repo `docs/project/`의 **현재 상태 문서**(기능 SoT · 아키텍처 · 데이터 스키마 · 운영 · ADR)로 통합 큐레이션하고, GitHub Wiki에 읽기 전용 미러를 발행한다. 트리거는 세션 독립적인 별도 커맨드다.

---

## 1. 배경 / 문제

현재 파이프라인의 문서는 전부 **사건 기록(event log)** 축으로만 쌓인다:

| 지금 있는 것 | 성격 |
|---|---|
| GitHub 이슈 + 스테이지 코멘트 | slug별 시간순 기록 |
| ADR (`GHS adr`) | **이슈 댓글에만 존재** — 발견성 최악 |
| `docs/<slug>/README.md` 등 | 머지 시점의 기능 스냅샷, 이후 갱신 없음 |
| spec / plan (`docs/superpowers/`) | 착수 시점 문서 |

빠진 것은 **현재 상태 뷰(projection)** — 기능별 SoT, 지금의 아키텍처, 지금의 스키마, 지금의 운영 방법. 기능 3개가 같은 테이블을 순차 수정했다면 현재 스키마를 알기 위해 이슈 3개 + 스냅샷 3개를 시간순으로 병합해야 한다.

추가 요구 2가지가 트리거 형태를 결정한다:

1. 파이프라인을 거치지 않은 수정(손 커밋, hotfix)도 문서에 반영되어야 한다.
2. 이미 진행 중인 기존 프로젝트에도 도입 가능해야 한다(초기 문서 일괄 생성).

→ 파이프라인 스테이지가 아니라 **독립 커맨드**여야 한다.

## 2. 결정 사항 (브레인스토밍 승인)

| # | 결정 | 선택 | 근거 |
|---|---|---|---|
| D1 | 문서 정본 위치 | **in-repo `docs/project/`** + Wiki는 읽기 전용 미러 | 에이전트가 worktree에서 문서를 컨텍스트로 재사용(문서가 파이프라인의 출력이자 입력이 되는 선순환) · 문서 변경이 PR diff에 실림 · private+Free 요금제의 Wiki 불가와 미초기화 `.wiki.git` 제약 회피 |
| D2 | 변경 반영 방식 | 페이지별 diff 요약 → 터미널 승인 → **현재 브랜치에 직접 커밋** (`git add docs/project/`로 스코프) | 자주 돌릴 수 있을 만큼 가볍고 게이트 철학 유지. 항상-PR은 빈도 저하, 무확인 자동 커밋은 정본 오염 위험으로 기각 |
| D3 | 구현 형태 | **신규 커맨드 + 전담 에이전트** | `/css:document` 확장은 `verify PASS` 세션 gating 우회 분기를 낳고, 스테이지별 dual-write는 비파이프라인 수정을 못 덮음 |
| D4 | 커맨드 이름 | `/css:wiki` | 사용자 멘탈모델 일치. Wiki가 스킵되어도 산출물 장르("프로젝트 위키")를 지칭 |

## 3. 커맨드 명세 — `/css:wiki`

```
/css:wiki [--init] [--no-publish]
```

- **세션 불요** — 어떤 git repo에서든 단독 실행. `--session` 없음(증분 수확이 파이프라인 산출물을 자동 포함). 세션 JSON은 **읽기만** 하고 쓰지 않으며, `_active.json`도 갱신하지 않는다(스테이지 커맨드가 아니므로).
- **모드 자동 판별**: `docs/project/` 부재 → bootstrap(전체 스캔), 존재 → 증분. `--init`은 전체 재생성 강제.
- `--no-publish`: Wiki 미러 생략(in-repo 커밋까지만).
- **락**: `locks/_project-wiki.lock` — 기존 규칙 동일(60분 stale → 교체+기록, 신선한 타 락 → 안내 후 중단, 모든 exit 경로에서 해제).

### 3.1 실행 플로우

```
1. preflight   : git repo·커밋 존재 확인. 비기본 브랜치/dirty tree는 경고만(중단 아님).
2. 기준점 해석  : docs/project/README.md 푸터의 <!-- css:last-synced: <sha> --> 읽기.
                 없으면 bootstrap.
3. 입력 수확    : git diff --name-status <sha>..HEAD + git log <sha>..HEAD --oneline,
                 신규/변경 docs/<slug>/, .claude/css/sessions/*.json(ADR·산출물 경로),
                 이슈 ADR 코멘트(gh 가능 시, GHS adr-list), 스키마성 파일(migrations/DDL/모델).
4. 디스패치     : css-doc-curator에 입력 번들 + 기존 docs/project/ 전달.
                 curator는 영향 페이지만 갱신하고 페이지별 변경 요약을 반환.
5. 승인 게이트  : 페이지별 diff 요약 제시 → AskUserQuestion [승인 / 페이지 제외 / 취소].
                 "페이지 제외" 선택 시 해당 파일 변경을 되돌리고 나머지만 진행.
6. 커밋        : git add docs/project/ 만 스코프 →
                 커밋 메시지 "docs(project): sync @ <shortsha>". dirty tree여도 안전.
7. Wiki 미러   : publish 활성 && Wiki 가용 시 GHS wiki-publish. 불가 시 경고 후 스킵(성공 종료).
```

핵심 성질:

- **동기화 기준점이 문서 안에 있다** — 별도 상태 파일 없이 clone·이식에도 유지되고, "언제 기준 문서인지"가 사람에게 보인다. 마커 값은 **수확 시점의 HEAD SHA**다: curator가 4단계에서 Home 푸터와 각 페이지의 `css:updated`에 이 SHA를 기록하고, 6단계 커밋에 함께 실린다(다음 증분은 이 SHA부터).
- **파이프라인 경유 여부 무관** — 수확이 git diff 기반이므로 손 커밋·hotfix도 동일하게 반영된다.

## 4. 문서 구조 — `docs/project/`

### 4.1 공통 규칙

1. **머리말 마커**: 모든 페이지 최상단에 `<!-- css:updated: <sha> <YYYY-MM-DD> -->` (Home만 푸터에 `css:last-synced`).
2. **Single-sourcing**: 한 사실은 한 페이지가 소유하고 다른 페이지는 링크한다(예: 기술 스택 상세는 `architecture.md`만, Home은 링크만).
3. **빈 섹션 금지**: 해당 없는 섹션·카테고리는 만들지 않는다. 골격은 "최대 구성"이며 curator는 근거 있는 섹션만 채운다(예: DB 없는 프로젝트에 `data/` 없음).

### 4.2 트리와 페이지 유형

페이지 유형이 갱신 계약을 결정한다 — **living**(제자리 병합, 기존 서술·손 편집 보존) / **index**(표 행 추가·수정) / **append-only**(파일 추가와 `superseded` 표기만).

```
docs/project/
├── README.md                      # Home                          [living]
├── architecture.md                # 아키텍처                       [living]
├── features/
│   ├── README.md                  # 기능 인덱스: 영역↔slug↔ADR 표   [index]
│   └── <기능영역>.md               # 기능 SoT (영역당 1페이지)       [living]
├── data/
│   ├── schema.md                  # 현재 스키마 + ERD              [living]
│   └── migrations.md              # 마이그레이션 타임라인 표         [index]
├── operations/
│   ├── runbook.md                 # 실행·빌드·배포·복구 절차        [living]
│   ├── configuration.md           # 설정 키/환경변수 레퍼런스       [living]
│   └── troubleshooting.md         # 증상→원인→조치                 [living]
└── decisions/
    ├── README.md                  # ADR 인덱스 표                  [index]
    └── ADR-NNNN-<제목>.md          # Nygard 형식                   [append-only]
```

**기능 영역 규칙**: 페이지 단위는 파이프라인 slug(변경 단위)가 아니라 **기능 영역(capability)**이다. `add-login`·`fix-login-2fa`는 같은 `features/auth.md`로 병합된다. 영역↔slug 매핑은 `features/README.md` 인덱스 표가 정본이며, curator가 새 slug의 배정을 판단하는 근거다. 신규 영역 생성은 승인 게이트 요약에 "신규 페이지"로 표시된다.

**분할 규칙**: 한 페이지가 약 300줄을 넘으면 curator가 하위 분할을 제안한다(게이트에서 표시). `data/schema.md`의 ERD는 테이블 약 15개 초과 시 도메인별로 분할한다.

**기존 산출물과의 관계**: `docs/<slug>/`(파이프라인 스냅샷)는 그대로 역사 기록으로 남는다. curator는 그 내용을 `features/` 현재판으로 승격·병합하고, 변경 이력 표에서 스냅샷으로 링크한다. 이슈 댓글의 기존 ADR은 bootstrap 시 `decisions/`로 백필한다.

### 4.3 페이지 골격 (11종)

#### 1) `README.md` — Home `[living]`

```markdown
# <프로젝트명> 프로젝트 문서

> 최종 동기화: `<short-sha>` · YYYY-MM-DD · /css:wiki가 관리

## 프로젝트 개요
(무엇을 하는 프로젝트인지 3–5문장 — 대상·핵심 가치)

## 문서 지도
| 문서 | 내용 | 이럴 때 보세요 |
|---|---|---|
| [아키텍처](architecture.md)     | 시스템 구조·모듈 경계 | 구조 파악, 설계 변경 전 |
| [기능 SoT](features/README.md)  | 기능별 현재 동작      | 기능 스펙 확인 |
| [데이터](data/schema.md)        | 스키마·ERD           | 테이블 구조 확인 |
| [운영](operations/runbook.md)   | 실행·배포·복구        | 운영 작업 시 |
| [의사결정](decisions/README.md) | ADR 목록             | "왜 이렇게 됐지?" |

## 최근 변경
(직전 동기화 1회분만 — 갱신된 페이지 · 요약 · 관련 slug/PR. 이력 아님)

<!-- css:last-synced: <sha> <date> -->
```

#### 2) `architecture.md` `[living]`

```markdown
# 아키텍처

## 1. 시스템 컨텍스트
(C4 L1 — 시스템과 외부 세계: 사용자, 외부 서비스, 연동 시스템)
(mermaid 다이어그램 + 외부 의존별 1줄: 무엇을 위해 의존하는지)

## 2. 모듈 구성
(C4 L2 — 실행/배포 단위와 주요 모듈, mermaid)
| 모듈 | 책임 (1줄) | 코드 위치 |

## 3. 주요 흐름
### 3.1 <핵심 시나리오명>   (1–3개만)
(mermaid sequenceDiagram + 단계 설명)

## 4. 기술 스택
| 계층 | 기술 | 버전 | 선정 근거 (ADR 링크 또는 "관례") |

## 5. 모듈 경계·의존 규칙
(허용/금지 의존 방향. 예: "domain은 infra를 import하지 않는다")

## 6. 횡단 관심사
(인증·로깅·에러 처리·i18n 등 — 각 1–2줄 + 담당 코드 위치)
```

#### 3) `features/README.md` — 기능 인덱스 `[index]`

```markdown
# 기능 SoT 인덱스

| 기능 영역 | 한 줄 설명 | 상태 | 관련 slug | 관련 ADR |
|---|---|---|---|---|
| [auth](auth.md) | 로그인·세션 관리 | 안정 | add-login, fix-login-2fa | ADR-0003 |

상태: 안정 · 개발중 · 폐기예정 · 폐기
```

#### 4) `features/<기능영역>.md` — 기능 SoT `[living]`

```markdown
# <기능 영역>

> 한 줄 요약 · 상태: 안정|개발중|폐기예정

## 1. 현재 동작
(호출자 관점 명세 — "지금 무엇이 되는가". 조건·규칙·엣지 케이스.
 하위 기능이 여럿이면 ### 하위 절)

## 2. 인터페이스
### API / CLI / 화면   (형태별로 해당하는 것만)
(진입점 표 + 코드 경로 인용 path:line — 상세 계약은 docs/<slug>/api.md 링크)

## 3. 내부 설계 요점
(이 기능 고유의 데이터 흐름·핵심 컴포넌트 — architecture.md와 중복 금지)

## 4. 데이터
(이 기능이 소유/사용하는 테이블·키 — data/schema.md 해당 절 링크)

## 5. 제약·알려진 한계
(의도된 제약, 미지원 케이스 — docs/<slug>/의 Future Work에서 승격)

## 6. 변경 이력                                    [행 추가만]
| 날짜 | slug | 변경 요약 | PR |
```

"변경 이력" 표가 현재 상태(§1–5)와 사건 기록(`docs/<slug>/`, 이슈)을 잇는 다리다.

#### 5) `data/schema.md` `[living]`

```markdown
# 데이터 스키마

> 저장소: <예: PostgreSQL 15 (주 저장소), Redis (캐시)> — 현재 기준, 이력은 migrations.md

## 1. ERD
(mermaid erDiagram — 테이블 ~15개 초과 시 도메인별 분할)

## 2. 테이블 상세
### 2.1 <table_name>
(용도 1줄 · 소유 기능: features/<x>.md 링크)
| 컬럼 | 타입 | 제약 | 설명 |
- 인덱스: ...
- 정의 위치: <migration/model 파일 경로>

## 3. 저장소별 특기사항
(Redis 키 스킴·TTL, 캐시 무효화 규칙, 보존 정책 — 해당 시)
```

#### 6) `data/migrations.md` `[index]`

```markdown
# 마이그레이션 이력

| 순번/파일 | 날짜 | 변경 요약 | 관련 slug/PR |
(마이그레이션 파일당 1행, "users에 2fa_secret 추가" 수준의 요약)
```

#### 7) `operations/runbook.md` `[living]`

```markdown
# 런북

## 1. 사전 요구사항
(런타임·도구·버전·접근 권한)

## 2. 로컬 실행
(설치 → 설정 → 기동, 명령은 코드 블록 — 근거: package.json/Makefile 인용)

## 3. 빌드·테스트
(빌드/테스트/커버리지 명령 — CI 워크플로 파일 인용)

## 4. 배포
### 4.1 <환경명>
(단계별 명령 + 성공 확인 방법. CI/CD 자동화면 트리거 조건 + 워크플로 링크)

## 5. 정기 작업·백업/복구
(크론, 백업/복구 절차 — 해당 시)
```

#### 8) `operations/configuration.md` `[living]`

```markdown
# 설정 레퍼런스

## 1. 환경변수
| 키 | 필수 | 기본값 | 설명 | 정의/사용 위치 |

## 2. 설정 파일
### 2.1 <path/to/config>
(포맷·로드 시점·우선순위 + 키 표는 위와 동일 컬럼)

## 3. 시크릿
(필요한 시크릿 목록과 주입 방법만 — 값 기록 절대 금지)
```

#### 9) `operations/troubleshooting.md` `[living]`

```markdown
# 트러블슈팅

## <증상 — 관찰되는 현상이 제목>
- 원인:
- 진단: (확인 명령·로그 위치)
- 조치: (해결 절차)
- 관련: (이슈 #, slug, ADR)
```

#### 10) `decisions/README.md` — ADR 인덱스 `[index]`

```markdown
# ADR 인덱스

| 번호 | 제목 | 상태 | 날짜 | 출처 |
| [ADR-0001](ADR-0001-<제목>.md) | ... | accepted | 2026-07-01 | 이슈 #12 |

상태: proposed · accepted · superseded by ADR-NNNN
```

#### 11) `decisions/ADR-NNNN-<제목>.md` `[append-only]`

Nygard 표준. 기존 `GHS adr`의 4필드(title/context/decision/consequences)와 1:1이라 이슈 댓글 백필이 무손실이다.

```markdown
# ADR-NNNN: <제목>

- 상태: accepted (| superseded by ADR-MMMM)
- 날짜: YYYY-MM-DD
- 출처: 이슈 #N의 ADR-k 코멘트 · 세션 <slug> · 수동

## 배경 (Context)
(어떤 문제·제약이 작용했나)

## 결정 (Decision)
(무엇을 하기로 했나 — 단정문)

## 결과 (Consequences)
(좋아지는 것 / 감수하는 것)
```

요약: **11종 = living 7 + index 3 + append-only 1**. 갱신 규칙이 페이지 유형에 붙어 curator 계약이 단순해진다.

## 5. Wiki 미러

`docs/project/` → GitHub Wiki 단방향 발행. Wiki 페이지는 flat 네임스페이스이므로 접두어로 변환한다.

| in-repo | Wiki 페이지 |
|---|---|
| `README.md` | `Home` |
| `architecture.md` | `Architecture` |
| `features/README.md` | `Features` |
| `features/<x>.md` | `Features-<x>` |
| `data/schema.md` / `data/migrations.md` | `Data-Schema` / `Data-Migrations` |
| `operations/runbook.md` 등 | `Ops-Runbook` · `Ops-Configuration` · `Ops-Troubleshooting` |
| `decisions/README.md` | `ADR-Index` |
| `decisions/ADR-NNNN-<x>.md` | `ADR-NNNN-<x>` |

- `_Sidebar.md`: 카테고리 트리 자동 생성. `_Footer.md`: `mirrored from docs/project @ <sha>`.
- 각 페이지 상단에 배너: `> DO NOT EDIT — docs/project/에서 미러됨. 수정은 repo에서.`
- 상호 링크는 발행 시 Wiki 페이지명으로 재작성한다.

## 6. 에이전트 — `css-doc-curator` (sonnet)

기존 에이전트와 동일한 `<Agent_Prompt>` 9-섹션 형식. frontmatter: `model: sonnet`, `memory: project`, `css_stages: [wiki]`.

- **임무**: `docs/project/`를 "현재 상태의 정본"으로 유지. 입력 번들(diff 파일 목록·커밋 로그·신규 `docs/<slug>/`·세션 ADR·스키마 파일 경로)과 기존 `docs/project/`를 읽고 **영향받은 페이지만** 갱신.
- **핵심 규칙**:
  - 페이지 유형별 갱신 계약 준수(living 병합 / index 행 / append-only 추가). 기존 서술·손 편집 보존 — bootstrap 외 전체 재작성 금지.
  - 근거 없는 서술 금지 — 코드·설정·테스트·세션 산출물 인용(`path:line`)으로 뒷받침, 확인 불가한 운영 사실은 "미확인" 명시.
  - bootstrap은 카테고리별 순차 생성(대형 repo 컨텍스트 폭주 방지).
  - 산문 한국어, 다이어그램 mermaid, 시크릿 값 기록 금지.
- **Output contract**: 변경 페이지 목록 + 페이지별 1줄 요약, 마지막 줄 `ARTIFACT=docs/project/`. **커밋은 하지 않는다** — 승인 전 diff를 보여줘야 하므로 커맨드가 게이트 후 수행(에이전트가 커밋하는 documenter와 다른, 의도된 차이).

## 7. `lib/gh_sync.sh` 확장

함수 2개 추가. 기존 폴백 철학(gh 불가 시 파이프라인 불변) 유지.

```
wiki-publish --sha <sha>    # gh api repos/{owner}/{repo} --jq .has_wiki + clone 시도로 가용성 판단
                            # → <repo>.wiki.git clone(스크래치 디렉토리)
                            # → docs/project/ 변환·복사(§5 매핑, _Sidebar/_Footer/배너, 링크 재작성)
                            # → commit·push. 불가 시 경고 1줄 + exit 0.
adr-list --session <slug>   # session.github.adrs[]의 코멘트를 gh api로 회수해 전문 출력
                            # (bootstrap 백필용). gh 불가 시 빈 출력 + exit 0.
```

## 8. 에러 처리

| 상황 | 동작 |
|---|---|
| git repo 아님 / 커밋 0개 | 안내 후 중단 |
| dirty tree / 비기본 브랜치 | 경고만 — 커밋이 `docs/project/`로 스코프되므로 안전 |
| gh 미인증 · 리모트 없음 | ADR 수확은 세션 JSON만으로, Wiki 스킵 |
| Wiki 불가(private+Free, 미초기화 `.wiki.git`) | 경고 + 스킵, 커맨드는 성공 종료 |
| curator 실패 / 사용자 취소 | 커밋 없음, 락 해제 |
| 증분 diff 과대(수백 파일) | 카테고리별 분할 처리, 초과 시 `--init` 권고 후 중단 |
| 타 실행의 신선한 락 | 안내 후 중단 (기존 규칙) |

## 9. 테스트 계획

기존 체계(에이전트 골든 테스트 + `tests/fixtures/toy-typescript`)를 따른다.

1. **골든 테스트**: `css-doc-curator` 프롬프트가 9-섹션 계약·출력 계약(ARTIFACT 라인, 커밋 금지)을 지키는지.
2. **fixture 시나리오**: toy 프로젝트 bootstrap → 기대 카테고리만 생성되는지(예: DB 없음 → `data/` 없음) → 작은 변경 커밋 후 증분 실행 → 영향 페이지만 갱신 + `css:last-synced` 전진 확인.
3. **wiki-publish 단위 테스트**: 로컬 bare repo를 가짜 `.wiki.git` 리모트로 사용(네트워크 불요) — 이름 매핑·사이드바·배너·링크 재작성 검증.

## 10. 문서화

- `README.md` / `README.en.md`: 파이프라인 표·주요 기능에 `/css:wiki` 추가 (`/css:clean` 문서화와 동일한 방식).
- `docs/usage.ko.md` / `docs/usage.md`: 커맨드 레퍼런스 절 추가.
- Codex 대응(`$css-wiki` skill)은 기존 커맨드→skill 변환 규칙을 따른다.

## 11. 범위 외 (future work)

- `/css:clean` 완료 시 `/css:wiki` 실행 제안 훅 (머지 직후가 최적 타이밍).
- review 스테이지의 ADR 파일 dual-write (`GHS adr`가 `decisions/`에도 기록) — 현재는 수확으로 충분.
- 다중 repo 통합 wiki.
- `glossary.md` 등 추가 카테고리.

## 12. 참조

- `commands/document.md`, `agents/documenter.md` — 기존 문서화 스테이지(스냅샷 생성자)
- `lib/gh_sync.sh` — GitHub 연동 헬퍼(확장 대상)
- `docs/session-schema.md` — 세션 스키마(이 커맨드는 세션을 읽기만 함)
- `docs/superpowers/specs/2026-06-15-github-pipeline-tracking-design.md` — gh_sync 설계 원형
