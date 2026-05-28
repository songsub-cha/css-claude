# CSS Pipeline Dashboard

로컬에 설치하는 멀티 프로젝트 CSS 파이프라인 대시보드입니다. 진행 중인 모든 CSS 세션을 Kanban 보드에서 시각화하고, Gate 2 / Gate 3 승인을 카드 드래그로 처리합니다.

---

## 개요

CSS 파이프라인을 터미널에서만 운영하면 동시에 여러 프로젝트를 실행할 때 각 세션의 상태를 파악하기 어렵습니다. Pipeline Dashboard는 이를 보완하는 **선택적 로컬 웹 UI**입니다.

- 등록된 모든 프로젝트의 활성 세션을 7개 Kanban 컬럼으로 시각화합니다.
- Gate 2 (review → execute), Gate 3 (document → pr) 카드를 다음 컬럼으로 드래그하면 파이프라인이 자동으로 재개됩니다.
- 기존 터미널 `AskUserQuestion` 승인 방식과 공존하며, 같은 세션에서 Gate 2는 터미널로, Gate 3는 대시보드로 승인하는 혼합 사용이 가능합니다.
- 완료된 세션은 PostgreSQL에 아카이브되어 히스토리 뷰로 조회할 수 있습니다.

대시보드가 없어도 CSS 파이프라인 자체는 정상 동작합니다. `dashboard_enabled: false` 상태에서는 기존 터미널 2단계 승인 흐름이 그대로 유지됩니다.

---

## 핵심 기능

### 멀티 프로젝트 Kanban

7개 컬럼(interview / plan / review / execute / verify / document / pr)으로 구성된 Kanban 보드에 등록된 모든 프로젝트의 활성 세션이 카드로 표시됩니다. 상단 TopBar의 레포 칩을 클릭하면 특정 프로젝트만 필터링할 수 있습니다.

각 SessionCard는 왼쪽 3px 컬러 스트라이프로 레포를 구분하며, 세션 이름과 경과 시간을 보여줍니다. Gate 대기 중인 카드는 황색 테두리와 "드래그하여 승인" 안내 문구가 표시됩니다.

참조 테스트: `dashboard/frontend/tests/test_KanbanBoard.test.tsx` (7 컬럼 렌더링), `test_SessionCard.test.tsx`

### 단계별 진행 시각화

카드를 클릭하면 오른쪽에 상세 슬라이드 패널이 열립니다. 패널에는 다음 정보가 포함됩니다.

- 단계별 상태 타임라인 (완료 / 진행 중 / 대기 / 실패)
- 각 단계 소요 시간
- 아이디어 원문
- 아티팩트 아코디언 (spec, plan, rich-spec-Txx, exec-log, verify, docs — 클릭 시 마크다운 렌더링)

참조 테스트: `dashboard/frontend/tests/test_DetailSlideOver.test.tsx`, `test_ArtifactAccordion.test.tsx`

### 드래그&드롭 Gate 승인

Gate 승인이 가능한 드래그는 두 가지입니다.

| 드래그 방향 | Gate | 동작 |
|------------|------|------|
| review → execute | Gate 2 | `gate2_pre_execute` 승인 + 브리지를 통한 파이프라인 재개 |
| document → pr | Gate 3 | `gate3_pre_pr` 승인 + 브리지를 통한 파이프라인 재개 |

그 외 이동은 카드가 원래 컬럼으로 되돌아오고 토스트 알림("Gates 외 이동은 불가")이 표시됩니다.

참조 테스트: `dashboard/frontend/tests/test_KanbanBoard.test.tsx` (valid drag + non-gate drag rejected)

### 교차 승인 (Cross-path Approval)

터미널과 대시보드 중 어느 채널로든 Gate를 승인할 수 있으며, 같은 세션 내에서 Gate마다 채널을 달리 써도 됩니다. CSS 파이프라인은 `CSS_DASHBOARD_RESUME=1` 환경 변수로 비대화형 재실행을 감지하여 `AskUserQuestion`을 건너뜁니다.

잠금 파일(`<project>/.claude/css/locks/<id>.lock`) 기반 상호 배제로 동시 승인 충돌을 방지합니다. 터미널이 잠금을 보유 중이면 대시보드 드래그가 409 Conflict를 반환합니다.

참조 테스트: `dashboard/backend/tests/test_router_gates.py` (`test_approve_lock_held_returns_409`)

### 히스토리

완료, 실패, 취소된 세션은 PostgreSQL `sessions_history` 테이블에 자동 보관됩니다. `/history` 경로에서 다음 필터로 조회할 수 있습니다.

- 프로젝트 / 결과(completed / failed / aborted) / 날짜 범위

각 행을 클릭하면 상세 슬라이드 패널이 열립니다 (Retry 버튼 없음).

참조 테스트: `dashboard/backend/tests/test_router_history.py`, `dashboard/frontend/tests/test_HistoryView.test.tsx`

### 레포 색상 지정

Settings 모달(TopBar의 톱니 아이콘)에서 레포별 색상을 색상 선택기로 지정할 수 있습니다. 변경 즉시 SSE를 통해 모든 접속 클라이언트의 카드 색상이 동기화됩니다.

참조 테스트: `dashboard/backend/tests/test_router_projects.py`, `dashboard/frontend/tests/test_SettingsModal.test.tsx`

---

## 빠른 시작

Ubuntu 22.04에서 한 줄로 설치합니다.

```bash
bash scripts/install-dashboard.sh
```

설치 후 LAN 브라우저에서 접속합니다.

```
http://<host-ip>:7421
```

자세한 설치 방법은 [installation.md](installation.md)를, 조작 방법은 [usage.md](usage.md)를 참고하세요.

---

## 테스트 현황

| 스위트 | 결과 |
|--------|------|
| 백엔드 + 브리지 (pytest) | 45 passed |
| 프론트엔드 (vitest) | 21 passed |
| 합계 | 66 passed |
| E2E (Playwright) | 지연 — Ubuntu + Chromium 환경 필요 |

백엔드 코드 커버리지: 85% (임계값 충족)

---

## 알려진 한계 (v0.1)

이 버전은 단일 사용자 개인 서버 용도를 위한 v0.1입니다. 사용 전 아래 사항을 확인하세요.

**범위 제한**
- LAN 전용입니다. 인터넷(WAN) 노출을 위한 인증 기능은 없습니다. LAN 신뢰 모델 기반으로 운용합니다.
- 데스크탑(≥1280px) 화면 기준입니다. 모바일 최적화는 적용되지 않았습니다.
- 대시보드에서 할 수 있는 조작은 Gate 승인뿐입니다. 세션 중단, 롤백, 단계 편집은 지원하지 않습니다.

**배포 환경**
- 설치 스크립트와 전체 스택은 Ubuntu 22.04 전용입니다.
- 개발 머신(Windows)에서는 Docker 없이 진행되므로 컨테이너 빌드 및 E2E 브라우저 테스트를 검증하지 않았습니다. Ubuntu에서 별도 검증이 필요합니다.
- `watchdog`은 로컬 파일시스템(ext4/btrfs/xfs)에서만 안정적으로 동작합니다. 네트워크 마운트(SMB, NFS) 위의 세션 파일은 감지가 늦거나 누락될 수 있습니다.

**보안**
- CSRF 검사는 v0.1에서 완전한 allowlist 방식이 아닌 간이 구현입니다. 외부 노출 시 위험합니다.
- `artifact_reader.py`의 경로 순회(path traversal) 방어 로직은 테스트 커버리지 52%로 낮습니다.

**v0.2 예정 항목**
- 실제 CSRF allowlist 구현
- stale-lock 감지 및 force-unlock 기능
- `artifact_reader` / `bridge` 커버리지 보강
- E2E 브라우저 테스트 (Playwright)

---

## 아키텍처 요약

```
Ubuntu 22.04 Host
├─ docker-compose
│   ├─ dashboard (FastAPI + React static + watchdog SSE)
│   └─ postgres:16-alpine  (세션 히스토리 + 설정)
└─ css-dashboard-bridge (systemd 유저 서비스, ~80 LoC Python)
    ├─ ~/.claude/css-dashboard/queue/ 감시
    └─ claude --print '/css:ship --session X' 실행
```

자세한 내용은 [architecture.md](architecture.md)를 참고하세요.

---

## 관련 문서

- [architecture.md](architecture.md) — 컴포넌트 구조, 데이터 흐름, DB 스키마
- [installation.md](installation.md) — 설치, 업그레이드, 제거
- [usage.md](usage.md) — 대시보드 사용 방법 상세
- [../../dashboard/README.md](../../dashboard/README.md) — Docker/개발자용 빠른 참조
