> [English](README.md) · **한국어**

# CSS 파이프라인 대시보드

여러 프로젝트에 걸친 CSS 파이프라인 진행 상황을 시각화하고, 드래그&드롭으로 Gate를 승인할 수 있는 로컬 호스팅 대시보드입니다.

전체 설계는 [설계 spec](../docs/superpowers/specs/2026-05-28-pipeline-dashboard-design.ko.md)과 [구현 계획서](../docs/superpowers/plans/2026-05-28-pipeline-dashboard.md)(영어)를 참고하세요.

## 빠른 시작 (Ubuntu 22.04)

```bash
bash scripts/install-dashboard.sh
```

LAN의 아무 브라우저에서 `http://<host-ip>:7421`을 엽니다.

## 설치 / 제거

### 설치

```bash
# 저장소 루트에서:
bash scripts/install-dashboard.sh
```

스크립트가 수행하는 작업:
1. `~/.claude/css-dashboard/` 디렉토리 구조 생성
2. 브리지 데몬을 `~/.claude/css-dashboard/bin/bridge.py`로 복사
3. systemd 유저 서비스 `css-dashboard-bridge.service` 설치 및 활성화
4. 임의의 `DB_PASSWORD` 생성 후 `dashboard/.env`에 기록
5. `docker compose up -d --build`로 스택 시작
6. 컨테이너 내부에서 `alembic upgrade head` 실행해 DB 마이그레이션 적용

### 제거

```bash
bash scripts/uninstall-dashboard.sh
```

PostgreSQL 데이터 볼륨(모든 세션 히스토리)을 삭제할지 여부를 묻습니다.

## 아키텍처

```
Browser (LAN의 아무 기기)
    │ HTTP :7421
    ▼
[Nginx / Uvicorn] ← React 정적 빌드 (/static에서 서빙)
    │
    ├── FastAPI 라우터 (/api/*)
    │       ├── GET  /api/sessions          — 활성 세션 목록
    │       ├── GET  /api/sessions/{slug}   — 세션 상세 + gate 상태
    │       ├── POST /api/sessions/{slug}/gates/{gate}/approve — Gate 드래그
    │       ├── GET  /api/sse               — Server-Sent Events 스트림
    │       ├── GET  /api/history           — 완료된 세션 로그
    │       └── PATCH /api/projects/{id}   — 프로젝트별 색상
    │
    ├── SQLAlchemy async → PostgreSQL 16
    │
    └── SessionWatcher (watchdog) → <project>/.claude/css/sessions/*.json 읽기

[Bridge daemon] (호스트 systemd 유저 서비스)
    ├── ~/.claude/css-dashboard/queue/ 에서 승인 파일 폴링
    └── 실행: claude --print '/css:ship --session <slug>' (env CSS_DASHBOARD_RESUME=1)
```

## 드래그&드롭 Gate 승인

Kanban 보드는 드래그로 두 가지 Gate 전환을 지원합니다:

| 드래그 방향 | 트리거되는 Gate |
|----------------|---------------|
| review → execute | Gate 2 (실행 전 승인) |
| document → pr | Gate 3 (PR 전 승인) |

Gate가 아닌 컬럼으로 카드를 드래그하면 토스트 경고와 함께 거부됩니다. gate 상태가 `pending`인 카드만 gate 경계를 넘어 드래그할 수 있습니다.

## 트러블슈팅

| 증상 | 추정 원인 | 해결 |
|---------|-------------|-----|
| :7421에서 대시보드에 접속 불가 | Docker 스택 미실행 | `cd dashboard && docker compose up -d` |
| 카드가 갱신되지 않음 | 브리지 데몬 미실행 | `systemctl --user status css-dashboard-bridge` |
| Gate 드래그가 동작 안 함 | 세션 gate 상태가 `pending`이 아님 | `~/.claude/css/sessions/<slug>.json` 확인 |
| 시작 시 Alembic 에러 | 스키마가 최신이 아님 | `docker compose exec dashboard alembic upgrade head` |
| `DB_PASSWORD` 미설정 | `.env` 누락 | `install-dashboard.sh` 재실행 또는 `.env.example`에서 복사 |

## 기술 스택

- 백엔드: FastAPI + SQLAlchemy async + watchdog
- 프론트엔드: React 19 + Vite + TailwindCSS v4 + dnd-kit
- 데이터베이스: PostgreSQL 16
- 오케스트레이션: docker-compose
- 브리지 데몬: Python systemd 유저 서비스 (호스트에서 실행)
- 테스트: pytest + pytest-asyncio + testcontainers-postgres (백엔드), vitest + msw + @testing-library/react (프론트엔드), Playwright (E2E)
