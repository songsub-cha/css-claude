# Pipeline Dashboard — 사용 방법

## 대시보드 접속

설치 후 LAN 브라우저에서 아래 주소로 접속합니다.

```
http://<host-ip>:7421
```

인증 없이 바로 접속됩니다. LAN 신뢰 모델 기반이므로 인터넷에 노출하지 않도록 주의하세요.

---

## 화면 구성

### TopBar

화면 상단에 위치합니다.

- **타이틀** — "CSS Pipeline Dashboard · N active" (활성 세션 수 표시)
- **레포 칩** — 등록된 레포 목록. 클릭하면 해당 레포의 세션만 보이도록 필터링됩니다.
- **History** — 완료된 세션 히스토리 뷰로 이동
- **설정 아이콘** — 레포별 색상 설정 모달 열기
- **연결 상태 점** — DB / watcher / bridge 세 가지 상태 표시 (초록=정상, 빨강=이상)

### Kanban 보드

7개 컬럼이 CSS 파이프라인 단계를 나타냅니다.

```
interview  →  plan  →  review  →  execute  →  verify  →  document  →  pr
                              ↑                                       ↑
                           Gate 2                                  Gate 3
                        (드래그 승인)                           (드래그 승인)
```

Gate 승인 대기 중인 컬럼은 황색 점선 테두리와 "⚠" 아이콘으로 표시됩니다.

### SessionCard

각 세션 카드에는 다음 정보가 표시됩니다.

- 왼쪽 3px 컬러 스트라이프 — 레포 구분 색상
- 세션 이름 (굵게)
- 레포 이름 + 경과 시간 (예: `css-claude · 14m`)
- Gate 대기 중: 황색 테두리 + "드래그하여 승인" 안내
- 재개 실패: 우상단 빨간 점 + 흔들림 애니메이션
- 선택됨: 파란 테두리 (상세 패널이 열린 카드)

---

## 세션 카드 상세 패널

카드를 클릭하면 오른쪽에서 상세 슬라이드 패널이 열립니다.

### 타임라인

단계별 상태와 소요 시간을 보여줍니다.

```
✓ interview   2m 34s
✓ plan        4m 12s
✓ review      18m 05s
▶ execute     진행 중 ...
  verify      대기
  document    대기
  pr          대기
```

### 아이디어 원문

세션 시작 시 입력한 아이디어 텍스트가 표시됩니다.

### 아티팩트 아코디언

기본적으로 모두 접혀 있습니다. 항목을 클릭하면 마크다운으로 렌더링됩니다.

| 아티팩트 이름 | 내용 |
|-------------|------|
| `spec` | interview 단계 spec 문서 |
| `plan` | plan 단계 구현 계획 |
| `rich-spec-T01` 등 | review 단계 태스크별 Rich Spec |
| `exec-log` | execute 단계 실행 로그 |
| `verify` | verify 단계 검증 리포트 |
| `docs` | document 단계 README.md |

참조 테스트: `dashboard/frontend/tests/test_ArtifactAccordion.test.tsx`

### 실행 실패 시 액션

파이프라인 재개가 실패하면 패널 하단에 **Retry** 버튼이 나타납니다. 클릭하면 브리지 큐에 재시도 이벤트를 추가합니다.

---

## Gate 드래그 승인

### Gate 2 — review → execute

review 컬럼에서 Gate 2 대기 중인 카드를 execute 컬럼으로 드래그합니다.

1. 카드가 이동하면서 스피너 오버레이가 표시됩니다 (낙관적 UI).
2. 서버가 `gate2_pre_execute`를 `"approved"`로 기록하고 브리지 큐 파일을 생성합니다.
3. SSE `resume_started` 이벤트가 수신되면 스피너가 사라집니다.
4. 파이프라인이 execute 단계부터 재개됩니다. 세션 JSON이 갱신될 때마다 카드 위치가 업데이트됩니다.
5. 성공하면 카드가 현재 단계 컬럼으로 이동합니다.

참조 테스트: `dashboard/frontend/tests/test_KanbanBoard.test.tsx` — "valid gate2 drag triggers approve"

### Gate 3 — document → pr

document 컬럼에서 Gate 3 대기 중인 카드를 pr 컬럼으로 드래그합니다. 동작은 Gate 2와 동일합니다.

### 잘못된 드래그

Gate 2/3 외의 컬럼 이동을 시도하면 카드가 원래 위치로 돌아오고 토스트 알림("Gates 외 이동은 불가")이 표시됩니다.

참조 테스트: `dashboard/frontend/tests/test_KanbanBoard.test.tsx` — "non-gate drag rejected with toast"

### 키보드 접근성

마우스를 사용하기 어려운 경우:

1. Tab 키로 카드에 포커스
2. Enter 키로 상세 패널 열기
3. Gate 대기 중인 카드에 포커스 후 Space 키 → "Approve Gate" 버튼 클릭

---

## 교차 승인 (Cross-path Approval)

터미널과 대시보드를 Gate마다 자유롭게 혼합할 수 있습니다.

**예시 시나리오**: Gate 2는 터미널로, Gate 3는 대시보드로 승인

1. `/css:ship --session my-feature` 실행
2. Gate 2 도달 시 터미널에 3선택지가 나타납니다:
   - "Yes (여기서 승인)" — 즉시 터미널에서 승인
   - "Wait for dashboard (대시보드에서 드래그)" — 대시보드로 위임
   - "Cancel"
3. "Yes"를 선택하면 execute 단계가 진행됩니다.
4. Gate 3 도달 시 파이프라인이 일시 중지됩니다. 대시보드의 document 컬럼 카드를 pr 컬럼으로 드래그하면 파이프라인이 재개됩니다.

**반대 시나리오**: Gate 2는 대시보드로, Gate 3는 터미널로 승인

1. `/css:ship --session my-feature` 실행
2. Gate 2 도달 시 "Wait for dashboard"를 선택하거나 터미널을 닫습니다.
3. 대시보드에서 카드를 execute 컬럼으로 드래그합니다.
4. 브리지가 파이프라인을 재개하여 Gate 3까지 진행합니다.
5. 브리지가 재개한 프로세스는 비대화형이므로 Gate 3에서 자동으로 `state=pending`을 기록하고 종료됩니다.
6. 이 시점에 터미널을 열고 `/css:ship --session my-feature`를 실행하면 Gate 3 프롬프트가 나타납니다.

**잠금 충돌**: 터미널에서 Gate 대화 중(`AskUserQuestion` 응답 대기)에 대시보드에서 드래그하면 409 Conflict가 반환됩니다. 터미널에서 먼저 응답하거나 취소한 뒤 대시보드를 사용하세요.

---

## 레포별 색상 설정

1. TopBar의 톱니 아이콘을 클릭하여 Settings 모달을 엽니다.
2. 레포 목록에서 색상 피커를 클릭하여 색상을 선택합니다.
3. 확인 즉시 SSE를 통해 모든 클라이언트의 카드 색상이 업데이트됩니다.
4. "Auto-assign colors" 버튼을 클릭하면 기본 팔레트 7색이 자동 배정됩니다.

기본 팔레트: `#22c55e`, `#a855f7`, `#3b82f6`, `#f59e0b`, `#ef4444`, `#06b6d4`, `#ec4899`

참조 테스트: `dashboard/frontend/tests/test_SettingsModal.test.tsx`

---

## 히스토리 뷰 (`/history`)

완료, 실패, 취소된 세션의 아카이브를 조회합니다.

TopBar의 "History" 링크를 클릭하거나 직접 `http://<host-ip>:7421/history`로 접속합니다.

**테이블 컬럼**: 완료 시각 / 레포 (색상 칩) / 세션 이름 / 결과 / 총 소요 시간 / PR URL

**필터**: 프로젝트 선택 / 결과 선택 / 날짜 범위

각 행을 클릭하면 상세 슬라이드 패널이 열립니다. 히스토리 뷰의 패널에는 Retry 버튼이 없습니다.

참조 테스트: `dashboard/backend/tests/test_router_history.py`, `dashboard/frontend/tests/test_HistoryView.test.tsx`

---

## 연결 상태 표시기

TopBar 우측의 세 점은 각각 다음 컴포넌트 상태를 나타냅니다.

| 점 | 의미 |
|----|------|
| DB | PostgreSQL 연결 상태 |
| watcher | 파일 감시 데몬 상태 |
| bridge | 브리지 데몬 마지막 응답 |

PostgreSQL 장애 시 활성 세션 Kanban은 파일 기반으로 계속 동작하지만 히스토리와 색상 설정은 비활성화됩니다. 상단에 "DB unreachable" 배너가 표시됩니다.

LAN 연결이 끊기면 SSE가 1s/2s/4s/8s 간격으로 재연결을 시도하며 "재연결 중..." 배너가 표시됩니다.

---

## 주요 한계 (v0.1 재확인)

- **LAN 전용** — WAN 접근을 위한 인증 기능 없음. 외부 인터넷에 절대 노출하지 마세요.
- **Gate 승인 외 조작 불가** — 세션 중단, 롤백, 단계 강제 이동은 지원하지 않습니다.
- **데스크탑 전용** — 1280px 미만 화면에서는 레이아웃이 깨질 수 있습니다.
- **Ubuntu 22.04 전용** — Windows/macOS에서는 설치 스크립트가 동작하지 않습니다.
- **stale-lock 자동 해제 없음** — CSS 프로세스가 비정상 종료하여 잠금 파일이 남아 있어도 자동으로 해제되지 않습니다 (v0.2 예정). 수동으로 `<project>/.claude/css/locks/<session-id>.lock` 파일을 삭제하세요.
- **E2E 테스트 미검증** — Playwright 브라우저 테스트는 Ubuntu + Chromium 환경에서 별도 확인이 필요합니다.
