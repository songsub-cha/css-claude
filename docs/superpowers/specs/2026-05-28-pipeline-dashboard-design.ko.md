> [English](2026-05-28-pipeline-dashboard-design.md) · **한국어**

# CSS 파이프라인 대시보드 — 설계 Spec

## 메타데이터

- **생성일**: 2026-05-28
- **소유자**: sub1904@gmail.com
- **상태**: 설계 — plan + 구현 대기
- **Slug (세션 id)**: `pipeline-dashboard`
- **Brainstorming 세션**: `/css:ship`을 통한 `superpowers:brainstorming` 주도
- **대상**:
  - 신규: `dashboard/` (FastAPI 백엔드 + React 프론트엔드 + 브리지 데몬 + docker-compose)
  - 수정: `commands/{interview,ship,execute,pr}.md` 및 8개 커맨드 전체 (CLI 플래그 이름 변경)
  - 신규: `scripts/install-dashboard.sh`, `scripts/uninstall-dashboard.sh`

## 개요

CSS 파이프라인 진행 상황을 시각화하고, 사용자가 **세션 카드를 한 Kanban 컬럼에서 다음 컬럼으로 드래그**하여 각 파이프라인 Gate를 승인할 수 있게 하는 **로컬 호스팅 멀티 프로젝트 대시보드**입니다. 대시보드는 파일 watcher로 기존 CSS 세션 JSON 파일을 관측하고, 완료된 세션 히스토리 + 사용자 설정을 PostgreSQL에 보존하며, 사용자를 대신해 `claude` CLI를 호출하는 작은 호스트 측 브리지 데몬을 통해 파이프라인 재개를 트리거합니다.

대시보드는 기존 터미널 흐름을 **대체하지 않습니다** — 터미널 `AskUserQuestion` 승인과 대시보드 드래그&드롭 승인이 모두 지원되며, 단일 세션 내에서 혼용도 가능합니다(터미널에서 Gate 2, 대시보드에서 Gate 3, 혹은 그 반대). 상호 배제는 기존 세션별 락 파일로 강제됩니다.

### 주 사용자 (단일 사용자, 개인용 도구)

Ubuntu 22.04 홈 서버에서 CSS 파이프라인을 실행하고, Windows 11 워크스테이션에서 LAN으로 접속하는 저장소 소유자. 멀티 테넌트 요구사항 없음.

### 목표

1. **가시성**: 등록된 모든 프로젝트의 모든 활성 CSS 세션을, 단계별 진행률·경과 시간·배치/태스크 상세·산출물 아코디언과 함께 한눈에 봄.
2. **드래그&드롭 Gate 승인**: Gate 2(실행 전)와 Gate 3(pr 전)의 터미널 `AskUserQuestion`을 한 컬럼에서 다음 컬럼으로의 Kanban 카드 드래그로 대체. 승인은 자동 파이프라인 재개를 트리거.
3. **히스토리 + 설정**: 회고를 위해 완료된 세션을 아카이브; 시각적 그룹화를 위해 사용자가 저장소별 고정 색상을 지정.
4. **교차 경로 승인**: 두 승인 채널(터미널 또는 대시보드) 중 어느 쪽이든 Gate별·호출별로 사용 가능. 전역 모드 전환 없음.
5. **CSS 파이프라인 영향 최소화**: 8개 중 4개 커맨드만 변경. 수정은 가산적(대시보드 비활성화 시 레거시 AskUserQuestion 경로 유지).

### 비목표 (v0.1)

- 멀티 사용자, RBAC, 원격(WAN) 접속. LAN 전용, 인증 없음.
- gate 승인을 넘어선 대시보드에서의 파이프라인 상태 편집(중단·롤백·편집 없음). v0.1은 *관측자 + gate 승인자*.
- 모바일 최적화 레이아웃. 데스크톱(≥1280px) 우선; 태블릿은 best-effort.
- CSS 파이프라인 오케스트레이션 대체. 대시보드는 파이프라인 로직을 소유하지 않음; CSS 커맨드가 권위를 유지.
- 버전 간 CSS 커맨드 수정의 핫 리로드(단일 CSS 버전 설치 가정).

## 결정 요약

| 주제 | 결정 |
|---|---|
| 프로젝트 범위 | 멀티 프로젝트. 대시보드는 호스트의 등록된 모든 저장소에서 세션을 읽음. |
| 백엔드 스택 | Python 3.12 + FastAPI + uvicorn + asyncpg + SQLAlchemy 2.x + watchdog |
| 프론트엔드 스택 | React 19 + Vite + TypeScript + TailwindCSS v4 + dnd-kit + zustand + react-markdown |
| 영속화 | PostgreSQL 16 (히스토리 + 설정). 활성 세션은 진실의 원천으로서 파일 기반 유지. |
| 실시간 | FastAPI → React로의 Server-Sent Events (SSE) |
| 네트워크 | 0.0.0.0:7421 바인드 (LAN). 인증 없음 (LAN 신뢰). |
| 레이아웃 | A. 좌측 스트라이프 저장소 색상 + 우측 슬라이드아웃 상세 패널을 가진 Kanban 7컬럼 (GitHub Issues 스타일) |
| 드래그 규칙 | Gate 2(review→execute)와 Gate 3(document→pr)만. 다른 컬럼 이동은 거부. |
| Gate 승인 교차 경로 | Gate별·호출별. TTY 체크 + 락 파일 상호 배제. |
| 데몬-CSS 결합 | 파일 기반(세션 JSON + 큐 디렉토리). Hook 기반 대체는 검토 후 기각(Hook은 라이브 CC 세션 내부에서만 발화). |
| 브리지 위치 | 호스트에서 systemd 유저 서비스로 실행(컨테이너 아님). 컨테이너 내 `claude` 인증 + 워크트리-부모 볼륨 문제 회피. |
| 프로젝트 자동 발견 | 프로젝트의 첫 `/css:*` 호출이 `~/.claude/css-dashboard/projects.json`에 추가(flock 직렬화). |
| 재개 실패 | 카드 에러 아이콘 + 재시도 버튼. 감사 로깅. v0.1에서 자동 재시도 없음. |
| 산출물 렌더링 | 아코디언(기본 접힘) + 펼침 시 지연 fetch. 세션별 화이트리스트 산출물 이름. |
| 배포 | docker-compose (대시보드 + postgres). 설치 스크립트가 DB·systemd 유닛·설정 부트스트랩. |
| CLI 플래그 이름 변경 | 8개 커맨드 전반에서 `--slug <name>` → `--session <name>`. 내부 JSON 필드 `slug`는 보존. |
| Hook (선택) | 즉각 SSE 푸시를 위한 `PostToolUse`(세션 JSON에 Write 시), `SessionStart` 배너. 부하 분담(load-bearing) 아님. |

## 아키텍처

```
┌────────────────────────────── Ubuntu 22.04 host ──────────────────────────────┐
│                                                                                │
│  ┌──────────────────┐                                                          │
│  │ Claude Code (TUI) │  user runs /css:ship --session X "idea" in a project   │
│  │                   │  writes: <project>/.claude/css/sessions/X.json          │
│  │                   │  writes: ~/.claude/css-dashboard/projects.json (auto)   │
│  └──────────────────┘                                                          │
│           ▲                                                                    │
│           │ re-spawned via `claude --print "/css:ship --session X"`           │
│           │                                                                    │
│  ┌────────┴──────────────────────────────── docker-compose stack ───────────┐ │
│  │                                                                          │ │
│  │  ┌─────────────────────────┐    ┌─────────────────────────┐             │ │
│  │  │ dashboard (FastAPI)     │    │ PostgreSQL 16            │             │ │
│  │  │  - watchdog file watcher│◄──►│  - projects              │             │ │
│  │  │  - REST + SSE           │    │  - sessions_history       │             │ │
│  │  │  - React static build   │    │  - gate_audit_log         │             │ │
│  │  └─────┬───────────────────┘    │  - daemon_runs            │             │ │
│  │        │                        └─────────────────────────┘             │ │
│  └────────┼───────────────────────────────────────────────────────────────────┘ │
│           │ writes approval events to queue dir                                │
│  ┌────────▼─────────┐  ← runs on host as systemd user service                  │
│  │ daemon-bridge    │ watches ~/.claude/css-dashboard/queue/*.json             │
│  │ (~80 LoC Python) │ on event: spawns `claude --print '/css:ship --session X'│
│  │                  │ POSTs run results back to dashboard                      │
│  └──────────────────┘                                                          │
│                                                                                │
│  ~/.claude/                                                                    │
│   ├── css/sessions/<session-id>.json   ← state of truth                        │
│   ├── css-dashboard/                                                           │
│   │     ├── config.json    ← {dashboard_enabled, claude_cli, ...}              │
│   │     ├── projects.json  ← auto-registered project paths + repo metadata    │
│   │     ├── queue/<evt-id>.json ← approval signal files (consumed by bridge)  │
│   │     ├── queue/processed/, queue/failed/                                    │
│   │     ├── runs/<run-id>.log                                                  │
│   │     └── server-info    ← daemon URL                                        │
│   └── ...                                                                       │
└────────────────────────────────────────────────────────────────────────────────┘
                                  ▲
                                  │ http://<host-ip>:7421 (LAN, no auth)
                                  │ React drag&drop → POST /api/...
                                  │ Server → React via /api/sse (SSE)
                                ┌─┴───────┐
                                │ Browser  │
                                │ (Windows)│
                                └──────────┘
```

### 왜 브리지가 컨테이너가 아닌 호스트에 있는가

대시보드 컨테이너 안에서 `claude`를 실행하려면 다음이 필요합니다:
- 호스트 OAuth 토큰 / `~/.claude/.credentials` 마운트
- `git worktree add ../<repo>-css-<session>`이 해석되도록 등록된 모든 프로젝트의 부모 디렉토리 마운트
- 네트워크 접근(컨테이너 → Anthropic API), 호스트와 다를 수 있는 DNS/프록시 포함
- 사용자가 `claude auth login`으로 재인증할 경우의 중복 인증

작은 호스트 측 브리지가 이 모든 것을 우회합니다. 컨테이너는 UI + 상태 + DB로 축소됩니다. 브리지는 ~80 LoC, 멱등, 재시작 안전합니다.

### 왜 Hook이 데몬을 대체할 수 없는가

Claude Code Hook(`PreToolUse`, `PostToolUse` 등)은 CC 프로세스가 활발히 실행 중일 때만 발화합니다. 다음을 할 수 없습니다:
- CC가 실행 중이 아닐 때 파일 시스템 감시
- 새 `claude` 프로세스 생성
- 대시보드의 자동 재개 구동

Hook은 *유용한 선택적 최적화*로 남습니다(세션 JSON 기록 시 PostToolUse가 파일 watcher 디바운스보다 SSE를 더 빨리 푸시) — 하지만 대시보드에 부하 분담 요소는 아닙니다.

## 진실의 원천 & 파일 레이아웃

| 데이터 | 위치 | 소유자 |
|---|---|---|
| 활성 세션 상태 | `<project>/.claude/css/sessions/<id>.json` | CSS 커맨드가 기록; watcher가 읽음 |
| Phase 락 | `<project>/.claude/css/locks/<id>.lock` | CSS 커맨드. 브리지는 재개 전 확인; 대시보드는 드래그 승인 전 확인. |
| Plan / spec / rich-spec / exec-log / verify | `<project>/.claude/css/{plans,executions,verifies}/` 및 `<project>/docs/` | CSS 파이프라인 출력; 대시보드가 산출물 아코디언 펼침 시 읽음 |
| 등록된 프로젝트 | `~/.claude/css-dashboard/projects.json` | CSS 커맨드가 첫 실행 시 추가(flock); 대시보드가 읽고 색상 자동 할당 |
| 승인 큐 | `~/.claude/css-dashboard/queue/*.json` | 대시보드가 기록; 브리지가 소비 |
| 실행 로그 | `~/.claude/css-dashboard/runs/<run-id>.log` | 브리지가 기록; 대시보드가 필요 시 읽음 |
| 대시보드 설정 | `~/.claude/css-dashboard/config.json` | 설치 스크립트가 기록; CSS 커맨드 + 대시보드가 읽음 |
| 완료 세션 아카이브 | PostgreSQL `sessions_history` | watcher가 파이프라인 완료 시 삽입 |
| 사용자 설정(저장소 색상 등) | PostgreSQL `projects`, `settings` | 대시보드 UI가 REST로 편집 |

세션이 종료되면(성공 또는 실패), watcher가 `phases.pr.status`의 `completed` 전환(또는 임의 phase의 `failed`)을 감지하고, `sessions_history`에 아카이브 행을 삽입하며, **JSON 파일을 보존**합니다(삭제하지 않음 — 포렌식 재독해를 위해 단일 진실의 원천 유지).

## 데이터 모델 (PostgreSQL)

```sql
CREATE TABLE projects (
  id            SERIAL PRIMARY KEY,
  repo_root     TEXT UNIQUE NOT NULL,
  repo_name     TEXT NOT NULL,
  color         TEXT NOT NULL DEFAULT '#3b82f6',
  registered_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_seen_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE sessions_history (
  id              SERIAL PRIMARY KEY,
  project_id      INT REFERENCES projects(id) ON DELETE CASCADE,
  session_id      TEXT NOT NULL,
  idea            TEXT NOT NULL,
  started_at      TIMESTAMPTZ NOT NULL,
  finished_at     TIMESTAMPTZ,
  final_phase     TEXT NOT NULL,
  outcome         TEXT NOT NULL CHECK (outcome IN ('completed', 'failed', 'aborted')),
  pr_url          TEXT,
  phase_durations JSONB NOT NULL,
  snapshot        JSONB NOT NULL,
  archived_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (project_id, session_id, archived_at)
);

CREATE TABLE gate_audit_log (
  id              SERIAL PRIMARY KEY,
  project_id      INT REFERENCES projects(id),
  session_id      TEXT NOT NULL,
  gate            TEXT NOT NULL CHECK (gate IN ('gate2_pre_execute', 'gate3_pre_pr')),
  reached_at      TIMESTAMPTZ NOT NULL,
  approved_at     TIMESTAMPTZ,
  approval_source TEXT CHECK (approval_source IN ('dashboard_drag', 'terminal_ask')),
  resume_status   TEXT CHECK (resume_status IN ('success', 'failed', 'retrying')),
  retry_count     INT NOT NULL DEFAULT 0,
  error_message   TEXT
);

CREATE TABLE daemon_runs (
  id           SERIAL PRIMARY KEY,
  session_id   TEXT NOT NULL,
  command      TEXT NOT NULL,
  started_at   TIMESTAMPTZ NOT NULL,
  finished_at  TIMESTAMPTZ,
  exit_code    INT,
  stdout_tail  TEXT,
  stderr_tail  TEXT
);

CREATE INDEX idx_history_project_finished ON sessions_history(project_id, finished_at DESC);
CREATE INDEX idx_audit_session ON gate_audit_log(session_id, reached_at DESC);
CREATE INDEX idx_runs_session ON daemon_runs(session_id, started_at DESC);
```

## 세션 JSON 스키마 변경

```json
{
  "slug": "pipeline-dashboard",
  "idea": "...",
  "master_flow": true,
  "repo_root": "/home/user/proj/css-claude",
  "repo_name": "css-claude",
  "current_phase": "review",
  "phases": { /* unchanged */ },
  "gates": {
    "gate2_pre_execute": {
      "state": "pending",
      "source": null,
      "reached_at": "2026-05-28T05:14:23Z",
      "approved_at": null,
      "approved_by": null
    },
    "gate3_pre_pr": { /* same shape */ }
  },
  "retry_counters": { "review": 0, "execute": 0, "verify": 0 }
}
```

- JSON 필드 `slug`는 보존됩니다(파일 자체에서 이름 변경 없음). DB 컬럼 `sessions_history.session_id`는 동일 값을 저장 — 용어 브리지: 사용자에게 보이는 라벨은 "session", JSON 저장 필드는 `slug`, DB 컬럼은 `session_id`.
- `repo_root` / `repo_name`은 `/css:interview`가 첫 세션 저장 시 채움.
- `gates.<name>`은 객체(이전엔 `null`). 이 형태가 없는 레거시 세션: 대시보드는 누락 필드를 `state: null`로 취급.

## CSS 파이프라인 커맨드 수정

### 공통: CLI 플래그 이름 변경 — `--slug` → `--session`

범위: 8개 커맨드 파일 전체(`interview`, `plan`, `review`, `execute`, `verify`, `document`, `pr`, `ship`).

- `argument-hint` 갱신
- 인자 파싱 갱신
- 도움말 / 에러 / 배너 텍스트를 "slug" 대신 "session"으로 갱신
- 내부 `session.slug` 필드 참조는 보존
- 파일 경로 템플릿(예: `sessions/{slug}.json`)은 그대로 보존(kebab id는 여전히 slug)

### `/css:interview` — 저장소 메타데이터 캡처 + 프로젝트 자동 등록 (+15줄)

`<project>/.claude/css/sessions/<id>.json` 생성 후:

```
repo_root = git -C <project> rev-parse --show-toplevel
repo_name = basename(repo_root)
session.repo_root = repo_root
session.repo_name = repo_name
save_session()

if config.dashboard_enabled:
    flock(projects.json):
        if repo_root not in projects.entries:
            projects.entries.append({
                "repo_root": repo_root,
                "repo_name": repo_name,
                "registered_at": now_iso(),
                "color": null
            })
            write_atomic(projects.json)
```

### `/css:ship` — 교차 경로 지원 Gate 처리 (+40줄)

step 7(Gate 2)과 step 11(Gate 3)을 **교차 경로 분기 로직**으로 교체:

**재개 모드 감지**: 브리지는 환경 변수 `CSS_DASHBOARD_RESUME=1`과 함께 `claude --print`를 생성합니다. 슬래시 커맨드는 이 env var를 Bash로 확인(`[ "$CSS_DASHBOARD_RESUME" = "1" ]`)하여 브리지 주도의 비대화형 재개와 사용자 주도의 대화형 호출을 구분합니다. (`tty -s` 폴백은 Claude Code의 Bash 도구 내부에서 신뢰할 수 없으며, 도구 자체가 비-TTY입니다.)

```
# at Gate N
state = session.gates.gateN.state

if state == "approved":
    proceed
    return

is_interactive = $CSS_DASHBOARD_RESUME != "1"

if is_interactive and config.dashboard_enabled:
    answer = AskUserQuestion(
      "Gate N reached" + (" (currently pending dashboard approval — you can also approve here)" if state == "pending" else ""),
      options=[
        "Yes (approve here)",
        "Wait for dashboard",
        "Cancel"
      ]
    )
    if answer == "Yes":
        session.gates.gateN = {state: "approved", source: "terminal_ask", approved_at: now()}
        save_session()
        proceed

    elif answer == "Wait for dashboard":
        if state != "pending":
            session.gates.gateN = {state: "pending", reached_at: now()}
            save_session()
        release_lock()
        exit 0  # graceful

    else:  # Cancel
        release_lock()
        exit 0  # state preserved

elif is_interactive and not config.dashboard_enabled:
    # legacy 2-option AskUserQuestion (unchanged)
    answer = AskUserQuestion(banner, options=["Yes", "Cancel"])
    ...

else:  # non-interactive — spawned via `claude --print` by bridge with CSS_DASHBOARD_RESUME=1
    if state != "approved":
        session.gates.gateN = {state: "pending", reached_at: now()}
        save_session()
    release_lock()
    exit 0
```


### `/css:execute` 및 `/css:pr` (각 +10줄)

`master_flow=true`일 때 Gate 2 / Gate 3을 다시 묻지 않음(이미 `/css:ship`에서 처리됨). `dashboard_enabled=true`로 단독 호출되어 Gate를 만나면 동일한 교차 경로 분기 로직을 따름.

### 대시보드 설정 파일

`~/.claude/css-dashboard/config.json`은 `install-dashboard.sh`가 생성하고 모든 CSS 커맨드가 읽습니다:

```json
{
  "dashboard_enabled": true,
  "dashboard_url": "http://localhost:7421",
  "database_url": "postgresql+asyncpg://css:****@localhost:5432/css_dashboard",
  "claude_cli": "claude",
  "queue_dir": "~/.claude/css-dashboard/queue",
  "default_palette": ["#22c55e", "#a855f7", "#3b82f6", "#f59e0b", "#ef4444", "#06b6d4", "#ec4899"]
}
```

파일이 없으면 CSS 커맨드는 레거시 모드로 동작(대시보드 상호작용 없음).

## 승인 시퀀스 (엔드투엔드)

```
User drags card from review column to execute column in browser
  │
  ▼
[Browser]  POST /api/sessions/{id}/gates/gate2_pre_execute/approve
  │
  ▼
[FastAPI]  ① Check <project>/.claude/css/locks/<id>.lock — if exists → 409 Conflict
           ② Update <project>/.claude/css/sessions/<id>.json (atomic write):
                gates.gate2_pre_execute.state = "approved"
                gates.gate2_pre_execute.source = "dashboard_drag"
                gates.gate2_pre_execute.approved_at = now()
           ③ Write ~/.claude/css-dashboard/queue/<evt-id>.json:
                { slug, project_root, command: ["claude", "--print", "/css:ship --session X"],
                  callback_url, ... }
           ④ INSERT INTO gate_audit_log (...)
           ⑤ SSE broadcast: gate_approved
  │
  ▼
[bridge]   watchdog on QUEUE_DIR detects new file
           subprocess.run(command, cwd=project_root, timeout=3600)
           POST /api/internal/run-result { event: "started" }
  │
  ▼
[FastAPI]  SSE broadcast: resume_started
  │
  ▼
[claude]   Non-interactive `/css:ship --session X` re-runs:
              session.gates.gate2_pre_execute.state == "approved" → AskUserQuestion skipped
              proceed to execute → TDD → verify → document → Gate 3 → ...
           session JSON updates throughout
  │
  ▼
[watcher]  detects JSON changes → SSE broadcast: session_updated (multiple)
  │
  ▼
[bridge]   `claude --print` exits (code 0)
           POST /api/internal/run-result { event: "finished", exit_code: 0 }
           Move queue file to queue/processed/
  │
  ▼
[FastAPI]  Update daemon_runs row. If next gate now pending → no further action.
           If pipeline finished (pr.status=completed) → trigger archive to sessions_history.
```

**실패 경로**: 브리지가 stderr 꼬리와 함께 `event: "failed"`를 POST. FastAPI가 `gate_audit_log.resume_status = "failed"`를 갱신하고 `resume_failed`를 브로드캐스트. UI는 상세 패널에 빨간 표시기 + 재시도 버튼을 표시. 재시도는 `gate.state`를 바꾸지 않고(여전히 "approved") 새 큐 파일을 큐잉하는 `/api/sessions/{id}/gates/{gate}/retry`를 POST.

## REST API

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/api/sessions` | 등록된 프로젝트 전반의 모든 활성 세션 나열 |
| GET | `/api/sessions/{id}` | 전체 세션 상세 |
| GET | `/api/sessions/{id}/artifacts` | 사용 가능한 산출물 나열(이름, mtime, 크기) |
| GET | `/api/sessions/{id}/artifacts/{name}` | 명명된 산출물의 Markdown 본문(화이트리스트 강제) |
| POST | `/api/sessions/{id}/gates/{gate}/approve` | 드래그로 gate 승인 |
| POST | `/api/sessions/{id}/gates/{gate}/retry` | 실패 후 재개 재큐잉 |
| GET | `/api/projects` | 색상이 포함된 등록 프로젝트 |
| PATCH | `/api/projects/{id}` | 색상 또는 기타 설정 갱신 |
| GET | `/api/history` | 페이지네이션된 세션 아카이브(필터: project_id, outcome, 날짜 범위) |
| GET | `/api/sse` | Server-Sent Events 스트림 |
| POST | `/api/internal/run-result` | 브리지 콜백(started / finished / failed) |

### 산출물 화이트리스트

세션별로 API가 서빙할 산출물:
- `spec` → `session.phases.interview.artifact`
- `plan` → `session.phases.plan.artifact`
- `rich-spec-{task-id}` → `<project>/.claude/css/plans/T{id}-spec-{session-id}-*.md` 에서
- `exec-log` → 가장 최신 `<project>/.claude/css/executions/exec-log-{session-id}-*.md`
- `verify` → 가장 최신 `<project>/.claude/css/verifies/verify-{session-id}-*.md`
- `code-review`, `security-review` → verify 리포트에서 링크됨
- `docs` → `<project>/docs/{session-id}/README.md` (`/css:document` 완료 후)

경로 해석: 각 이름은 `session.repo_root` 내에서 해석되는 파일로 매핑. `Path(file).resolve()`의 결과는 `repo_root.resolve()`로 시작해야 함. 아니면 → 403.

### SSE 이벤트 타입

```
event: session_updated     data: { session_id, phase, gates, mtime }
event: gate_reached        data: { session_id, gate, reached_at }
event: gate_approved       data: { session_id, gate, source }
event: resume_started      data: { session_id, run_id, command }
event: resume_failed       data: { session_id, gate, error, retry_count }
event: session_completed   data: { session_id, pr_url, outcome, durations }
event: project_registered  data: { project_id, repo_name, color }
event: connection_health   data: { db, watcher, bridge }   (every 30s heartbeat)
```

## 프론트엔드 컴포넌트

```
<App>
 ├─ <TopBar>
 │   ├─ <Title>            "CSS Pipeline Dashboard · N active"
 │   ├─ <RepoLegend>       (chips, click to filter)
 │   ├─ <HistoryLink>      → /history
 │   └─ <SettingsButton>   → opens <SettingsModal>
 ├─ <KanbanBoard>          (7 columns)
 │   └─ <Column stage gateAfter?> ← dashed border + ⚠ label when gate pending
 │       └─ <SessionCard× n>
 ├─ <DetailSlideOver>      (right slide-in 320px, GitHub Issues style)
 │   ├─ <SessionHeader>    (color block + id + close)
 │   ├─ <StatusChips>      (repo, phase, gate state)
 │   ├─ <IdeaSection>
 │   ├─ <Timeline>         (per-phase status + duration)
 │   ├─ <ArtifactAccordion>← lazy fetch on expand
 │   └─ <ActionRow>        (Retry / Open in editor)
 ├─ <SettingsModal>        (per-project color picker)
 ├─ <HistoryView route="/history">
 ├─ <ToastContainer>
 └─ <SSEConnection />      (headless; updates Zustand store)
```

### SessionCard 비주얼

- 좌측 3px 스트라이프, `project.color`
- 제목: `session_id` 굵게
- 부제: `repo_name` 흐리게 + 경과 시간(`14m`)
- 상태:
  - `pending-gate`: 2px 호박색 외곽선 + 작은 "⚠ drag right to approve" 힌트
  - `resume-failed`: 우상단 빨간 점 + 1초 흔들림 애니메이션
  - `selected`: 2px primary 외곽선(이 카드에 상세 패널이 열렸을 때)

### 드래그 규칙 (dnd-kit)

| From 컬럼 | To 컬럼 | 동작 |
|---|---|---|
| `review` | `execute` | gate2_pre_execute 승인 POST(카드의 gate2가 pending일 때만) |
| `document` | `pr` | gate3_pre_pr 승인 POST(카드의 gate3가 pending일 때만) |
| 그 외 쌍 | — | 드롭 거부, 스냅백, 토스트 "Gates 외 이동은 불가" |

낙관적 UI: 드롭 시 카드 이동, SSE `resume_started` 도착까지 스피너 오버레이. 다음 phase를 보여주는 `session_updated`에서 배지 해제. `resume_failed`에서 카드는 빨간 표시기와 함께 원래 컬럼으로 복귀.

### 산출물 아코디언

- 각 산출물은 상세 패널의 접힌 행
- 클릭 → `GET /api/sessions/{id}/artifacts/{name}` fetch → `react-markdown` + `rehype-highlight`(코드) + `rehype-sanitize`(XSS 방어)로 렌더링
- `(session_id, name, mtime)` 키로 Zustand 캐시; SSE 브로드캐스트의 mtime 변경 시 재fetch

### 히스토리 뷰 (`/history`)

- 페이지네이션 테이블: finished_at / repo(색상 칩) / session_id / outcome / 총 소요시간 / PR URL
- 필터: 프로젝트, outcome, 날짜 범위
- 행 클릭 → DetailSlideOver 열림(동일 컴포넌트 재사용), `source="history"`(Retry 액션 없음)

### 설정 모달

- `projects` 테이블: repo_name | repo_root | 현재 색상(색상 선택기) | registered_at
- 색상 변경 → `/api/projects/{id}` PATCH → SSE 브로드캐스트 → 모든 클라이언트 팔레트 갱신
- "Auto-assign colors" 버튼(`config.default_palette` 사용)

### 접근성 / 키보드

- Tab으로 카드 포커스; Enter로 상세 열기; Esc로 닫기
- 드래그 대안: 포커스된 pending-gate 카드 + Space → "Approve Gate" 인라인 버튼
- 모든 인터랙티브 요소에 `aria-label`

## 브리지 데몬

`~/.claude/css-dashboard/bin/bridge.py` (~80 LoC). 호스트에서 systemd 유저 서비스로 실행.

```python
# pseudocode
import json, subprocess, requests, time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

HOME = Path.home()
QUEUE = HOME / ".claude/css-dashboard/queue"
PROCESSED = QUEUE / "processed"
FAILED = QUEUE / "failed"
RUNS = HOME / ".claude/css-dashboard/runs"

def process_event(path: Path):
    evt = json.loads(path.read_text())
    sid = evt["session_id"]
    pr  = evt["project_root"]
    cmd = evt["command"]                  # list of str — server-constructed, validated
    log = RUNS / f"{evt['id']}.log"

    requests.post(evt["callback_url"], json={"id": evt["id"], "session_id": sid, "event": "started"})

    try:
        env = {**os.environ, "CSS_DASHBOARD_RESUME": "1"}
        with open(log, "w") as f:
            proc = subprocess.run(cmd, cwd=pr, timeout=3600, env=env, stdout=f, stderr=subprocess.STDOUT)
        result = {"id": evt["id"], "session_id": sid, "event": "finished",
                  "exit_code": proc.returncode, "log_path": str(log)}
        requests.post(evt["callback_url"], json=result)
        path.rename(PROCESSED / path.name)
    except Exception as e:
        requests.post(evt["callback_url"], json={
            "id": evt["id"], "session_id": sid, "event": "failed", "error": str(e)
        })
        path.rename(FAILED / path.name)

class Handler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith(".json"): return
        process_event(Path(event.src_path))

def main():
    for d in (QUEUE, PROCESSED, FAILED, RUNS): d.mkdir(parents=True, exist_ok=True)
    for p in QUEUE.glob("*.json"): process_event(p)        # re-process on startup
    obs = Observer(); obs.schedule(Handler(), str(QUEUE), recursive=False); obs.start()
    while True: time.sleep(60)

if __name__ == "__main__": main()
```

systemd 유닛(`~/.config/systemd/user/css-dashboard-bridge.service`):

```ini
[Unit]
Description=CSS Dashboard Bridge
After=network.target

[Service]
ExecStart=/usr/bin/python3 %h/.claude/css-dashboard/bin/bridge.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

## 테스트 전략

목표: ≥85% 라인 커버리지(CSS 파이프라인 표준).

| 레이어 | 도구 | 범위 |
|---|---|---|
| 백엔드 단위 | `pytest`, `pytest-asyncio` | 라우터, 서비스, 파일 watcher 이벤트 핸들러(FS 모킹) |
| 백엔드 통합 | `httpx.AsyncClient`, `testcontainers-postgres` | 실제 PostgreSQL 컨테이너, 전체 HTTP 스택 |
| 파일 watcher | `tmp_path` + 합성 JSON 기록 | watchdog → SSE 이벤트 체인 |
| 브리지 | `subprocess.run` 모킹 + 큐 픽스처 | 큐 소비 → 콜백 POST 동작 |
| 프론트엔드 단위 | `vitest`, RTL, `msw` | 컴포넌트, 스토어 전이 |
| 프론트엔드 드래그 | `@dnd-kit` 센서 모킹 + RTL `fireEvent` | 유효/무효 드롭 처리, 낙관적 UI |
| E2E | `Playwright` | 합성 세션 JSON → 드래그 → 모킹된 브리지 → SSE → UI |
| CSS 커맨드 | `tests/fixtures/toy-typescript/`의 골든 테스트(기존 패턴) | 이름 변경, 교차 경로 gate 분기, repo 캡처 |

E2E는 실제 `claude` 호출을 세션 JSON을 갱신하는 더미 스크립트로 모킹하여, API 비용 없이 전체 파이프라인을 실행할 수 있게 합니다.

## 에러 처리

| 시나리오 | 대응 |
|---|---|
| 손상된 세션 JSON | watcher가 ERROR 로깅, 이벤트 스킵. 카드는 마지막 정상 스냅샷과 함께 "⚠ corrupted" 표시. |
| 레거시 세션(`repo_root` 없음 / `gates` 객체 없음) | 하위 호환 기본값; 다음 `/css:*` 실행이 재채울 때까지 카드는 "(unknown repo)" 표시. |
| PostgreSQL 다운 | 성능 저하 모드: 활성 세션은 여전히 표시(파일 감시는 DB와 독립). 히스토리 + 설정 비활성. 배너: "DB unreachable". |
| 브리지 프로세스 사망 | systemd `Restart=on-failure`. 큐 파일 유지; 재시작 시 백로그를 멱등 처리. |
| 오래된 락(CSS 크래시) | 락 소유자 PID 죽음 AND 세션 JSON mtime > 5분 → "stale" 표시기. 상세 패널에 "force unlock" 버튼 노출. |
| 사용자가 드래그 중 탭 닫음 | 브라우저 낙관적 상태 손실; 백엔드 불변(POST 미발화). 무동작. |
| `claude` CLI가 PATH에 없음 | 브리지가 `FileNotFoundError` 포착, 명시적 메시지로 `resume_failed` POST. UI가 명확한 해결책 노출. |
| LAN 단절 | SSE 자동 재연결(1s/2s/4s/8s 백오프). 상단 배너 "재연결 중...". |
| 동시 projects.json 추가 | `flock` 권고 락이 직렬화. |
| 브리지가 실행 중 사망 | 다음 시작 시 큐 파일 재처리. 대시보드는 `run_id`로 콜백 중복 제거. |
| gate 상태 고착(approved지만 phase 미진행) | 상세 패널에 "force advance" / "reset gate" 관리 액션 노출. |
| 멀티 클라이언트 드래그 경쟁 | 첫 요청이 DB 행 수준 락 획득 + gate 상태 확인; 두 번째는 409 반환. |

## 보안

LAN 신뢰 가정(인증 없음)이지만 다음은 여전히 요구됩니다:

| 우려 | 완화책 |
|---|---|
| 산출물 엔드포인트의 경로 순회 | `Path.resolve()` 후 `session.repo_root` 대비 접두 검사. 산출물 이름에 화이트리스트 강제. |
| 읽기 전용 산출물 엔드포인트 | GET만. 이름 화이트리스트. 요청 본문에 사용자 제공 경로 없음. |
| SQL 인젝션 | SQLAlchemy 2.x async + asyncpg로 100% 파라미터화. |
| 브리지의 명령 인젝션 | `cmd`는 고정 템플릿에서 서버 측으로 구성된 리스트. `session_id`는 치환 전 `^[a-z0-9-]{1,64}$` 검증. |
| markdown의 XSS | `react-markdown` + `rehype-sanitize`가 원시 HTML 제거. `rehype-highlight`는 정적. |
| DB 자격증명 노출 | `.env`(gitignore) → docker-compose env 주입. compose YAML에 하드코딩 시크릿 없음. |
| 파일 권한 | `~/.claude/css-dashboard/` 700, queue/logs 600. 설치 스크립트가 강제. |
| CSRF | 모든 변경 엔드포인트가 허용 origin 대비 `Origin` 헤더 확인(구성 가능). SameSite 쿠키. |

## 배포

### 파일 구조 (저장소 신규)

```
css-claude/
├── commands/                         # MODIFIED — all 8 (rename + 4 gate-aware)
├── agents/                            # UNCHANGED
├── config/                            # UNCHANGED
├── scripts/
│   ├── install.{ps1,sh}              # existing — add `--with-dashboard` flag
│   ├── install-dashboard.sh           # NEW — Ubuntu
│   └── uninstall-dashboard.sh         # NEW
├── dashboard/                          # NEW (entire directory)
│   ├── README.md
│   ├── docker-compose.yml
│   ├── Dockerfile                     # multi-stage: node build → python runtime
│   ├── .env.example
│   ├── pyproject.toml
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/0001_initial.py
│   ├── backend/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── models.py
│   │   ├── watcher.py
│   │   ├── sse.py
│   │   ├── routers/
│   │   │   ├── sessions.py
│   │   │   ├── projects.py
│   │   │   ├── gates.py
│   │   │   ├── artifacts.py
│   │   │   ├── history.py
│   │   │   └── internal.py
│   │   ├── services/
│   │   │   ├── queue_writer.py
│   │   │   ├── session_reader.py
│   │   │   ├── archive.py
│   │   │   └── project_registry.py
│   │   └── tests/
│   ├── frontend/
│   │   ├── package.json
│   │   ├── vite.config.ts
│   │   ├── tailwind.config.ts
│   │   ├── tsconfig.json
│   │   ├── src/
│   │   │   ├── App.tsx
│   │   │   ├── main.tsx
│   │   │   ├── components/
│   │   │   │   ├── TopBar.tsx
│   │   │   │   ├── KanbanBoard.tsx
│   │   │   │   ├── Column.tsx
│   │   │   │   ├── SessionCard.tsx
│   │   │   │   ├── DetailSlideOver.tsx
│   │   │   │   ├── ArtifactAccordion.tsx
│   │   │   │   ├── SettingsModal.tsx
│   │   │   │   ├── HistoryView.tsx
│   │   │   │   └── ToastContainer.tsx
│   │   │   ├── stores/
│   │   │   │   ├── sessionsStore.ts
│   │   │   │   ├── projectsStore.ts
│   │   │   │   └── uiStore.ts
│   │   │   ├── api/
│   │   │   │   ├── client.ts
│   │   │   │   └── sse.ts
│   │   │   └── types.ts
│   │   └── tests/
│   └── bridge/
│       ├── bridge.py
│       ├── css-dashboard-bridge.service
│       └── tests/
├── docs/
│   ├── superpowers/specs/2026-05-28-pipeline-dashboard-design.md  # THIS FILE
│   ├── superpowers/plans/2026-05-28-pipeline-dashboard.md         # (output of /css:plan)
│   └── pipeline-dashboard/                                         # (output of /css:document)
└── tests/                              # existing fixtures + new dashboard-mode cases
```

### docker-compose.yml (스켈레톤)

```yaml
services:
  dashboard:
    build: .
    image: css-dashboard:latest
    ports: ["7421:7421"]
    environment:
      - DATABASE_URL=postgresql+asyncpg://css:${DB_PASSWORD}@postgres:5432/css_dashboard
    volumes:
      - ${HOME}/.claude:/host/.claude:rw
      - ${HOME}/projects:/host/projects:ro
    depends_on: [postgres]
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=css
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=css_dashboard
    volumes:
      - css-dashboard-pgdata:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  css-dashboard-pgdata:
```

### 설치 / 업그레이드 / 제거

**install-dashboard.sh** (v0.1에서는 Ubuntu 전용):

1. Docker + docker-compose 사용 가능 확인
2. `~/.claude/css-dashboard/` 생성(권한 700)
3. 임의의 DB 비밀번호 생성 → `.env`
4. `docker compose up -d --build`
5. alembic 마이그레이션 실행
6. `bridge.py` + systemd 유닛 배치; `systemctl --user enable --now css-dashboard-bridge`
7. `dashboard_enabled: true`로 `~/.claude/css-dashboard/config.json` 기록
8. 출력: `Dashboard up at http://<host-ip>:7421`

**uninstall-dashboard.sh**:

1. `systemctl --user disable --now css-dashboard-bridge`
2. `docker compose down [-v]`(볼륨 삭제 확인 프롬프트)
3. `config.json:dashboard_enabled = false` 설정(CSS가 레거시 모드로 복귀)
4. 선택적으로 `~/.claude/css-dashboard/` 제거(확인과 함께)

**업그레이드**: `git pull && bash scripts/install-dashboard.sh --upgrade` — 이미지 재빌드, 새 마이그레이션 실행.

## 관측성(Observability)

- 백엔드 로그: `structlog` JSON을 stdout으로(`docker compose logs dashboard`로 캡처)
- 브리지 로그: stdout → systemd journal(`journalctl --user -u css-dashboard-bridge`)
- 감사 추적: 모든 gate-reached, gate-approved, resume-started, resume-failed, archive 이벤트가 `gate_audit_log` 또는 `daemon_runs`에 행 기록
- UI: TopBar의 연결 상태 표시기(DB / watcher / bridge — 세 개의 색상 점)

## 인수 기준

v0.1 구현은 다음 조건을 만족하면 완료로 간주됩니다:

1. **멀티 세션, 멀티 프로젝트 Kanban 렌더링**. ≥2개 등록 저장소에 ≥2개 활성 세션이 있을 때, 대시보드가 올바른 카드를 올바른 컬럼에 올바른 저장소 색상 스트라이프와 함께 표시.
2. **카드 클릭으로 슬라이드아웃 상세 열림**. 타임라인, 상태 칩, 아이디어, 산출물 아코디언(기본 접힘)이 모두 렌더링.
3. **산출물 아코디언 지연 fetch**. `spec` 펼침이 markdown을 fetch·렌더링; `rich-spec-Txx`가 태스크별 파일을 fetch.
4. **Gate 2와 Gate 3 드래그 승인 동작**. pending 카드를 `review`→`execute`(또는 `document`→`pr`)로 드래그하면 세션 JSON에 승인 기록, 브리지 이벤트 큐잉, 브리지가 `claude --print '/css:ship --session X'`를 성공적으로 재생성하여 파이프라인 진행.
5. **교차 경로 승인**. 동일 세션을 Gate 2는 대시보드 드래그로, Gate 3은 터미널 `AskUserQuestion`으로(순서 무관) 승인 가능.
6. **락 기반 상호 배제**. CSS가 phase 락 보유 중(터미널 AskUserQuestion 진행 중)일 때, 대시보드 드래그는 명확한 메시지와 함께 409 Conflict 반환.
7. **드래그 규칙 강제**. Gate가 아닌 컬럼 이동은 토스트와 함께 스냅백.
8. **설정: 저장소별 색상**. 설정 모달로 프로젝트 색상 변경 시 그 프로젝트의 모든 카드(활성·히스토리)가 SSE로 즉시 갱신.
9. **히스토리 뷰**. 완료된 파이프라인이 phase 소요시간, PR URL, 클릭 가능한 상세와 함께 `/history`에 나타남.
10. **실패 복구**. 브리지 호출 실패(`claude` 미발견 / 비제로 종료) 시 카드에 빨간 표시기, 상세 패널에 Retry 노출, 재시도가 재큐잉되어 성공.
11. **`--slug` → `--session` 이름 변경**. 8개 커맨드 모두 `--session` 수용; 도움말 텍스트와 에러 메시지가 일관되게 "session" 사용. 내부 JSON `slug` 필드 보존.
12. **백엔드·프론트엔드·브리지 테스트 스위트 합산 커버리지 ≥85%**.
13. **깨끗한 Ubuntu 22.04 VM에서의 install-dashboard.sh**가 한 명령으로 전체 스택 구축(수동 DB 비밀번호 확인 후).
14. **레거시 모드 무회귀**. `dashboard_enabled=false`일 때 `/css:ship`이 현재 동작과 동일하게 작동(2-옵션 AskUserQuestion).

## 리스크 & 미해결 질문

| 리스크 | 완화책 |
|---|---|
| `claude --print` 비대화형 동작이 대화형과 다를 수 있음(출력 형식, 발화되는 hook) | /css:plan 단계에서 스모크 테스트; 요구되는 Claude Code 버전 문서화 |
| Ubuntu 외 호스트(macOS / WSL) | v0.1은 명시적으로 Ubuntu 전용. 설치 스크립트에 명시. |
| 큰 세션 JSON 파싱 비용(매우 긴 실행) | JSON은 작게 유지(상태 + phase 포인터만). 로그는 외부. 테스트 픽스처에서 벤치마크. |
| 네트워크/SMB 마운트 파일시스템에서 watchdog 이벤트 누락 | 파일시스템 요구사항 문서화: 로컬 ext4/btrfs/xfs만 |
| 호스트의 사용자 설치 Python 버전 | 브리지는 Python 3.10+ 필요. 설치 스크립트가 검증. |
| `$HOME` 매핑이 특이할 경우 컨테이너의 프로젝트 경로 뷰가 다를 수 있음 | 관례적 설정 문서화; 커스텀 볼륨 구성 허용 |
| 리버스 프록시를 통한 SSE 프록싱 | 범위 밖(LAN 직접 연결 가정) |

## 참고

- 상위 설계: [`docs/specs/2026-05-27-css-pipeline-design.ko.md`](../../specs/2026-05-27-css-pipeline-design.ko.md)
- 프로젝트 README: [`README.md`](../../../README.md)
- 시각적 brainstorming 목업: `.superpowers/brainstorm/851-1779912821/content/dashboard-layout*.html` (로컬 전용)
