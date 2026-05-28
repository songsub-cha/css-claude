# Pipeline Dashboard — 설치 안내

## 사전 조건

Ubuntu 22.04에서 다음 소프트웨어가 필요합니다.

| 항목 | 확인 방법 | 비고 |
|------|-----------|------|
| Docker | `docker --version` | 20.10 이상 |
| Docker Compose | `docker compose version` | v2 (`docker-compose` 아닌 `docker compose`) |
| Python 3.10 이상 | `python3 --version` | 브리지 데몬 실행용 |
| systemd (유저 서비스) | `systemctl --user status` | Ubuntu 22.04 기본 포함 |
| CSS 파이프라인 설치 완료 | `ls ~/.claude/commands/css/` | `install.sh` 실행 후 |

> **Windows 개발 머신 주의**: `install-dashboard.sh`는 Ubuntu 전용입니다. Windows에서는 Docker 없이 동작하므로 컨테이너 빌드와 E2E 테스트는 Ubuntu에서 검증해야 합니다.

---

## 설치 (Ubuntu 22.04)

프로젝트 루트에서 실행합니다.

```bash
bash scripts/install-dashboard.sh
```

스크립트가 수행하는 작업:

1. Docker, docker compose, Python 3.10+ 존재 여부 확인
2. `~/.claude/css-dashboard/` 디렉터리 생성 (권한 700)
3. 랜덤 DB 비밀번호 생성 → `dashboard/.env` 작성
4. `docker compose up -d --build` 실행 (FastAPI + PostgreSQL 기동)
5. Alembic 마이그레이션 실행 (`alembic upgrade head`)
6. `bridge.py`와 systemd 유닛 파일 설치
7. `systemctl --user enable --now css-dashboard-bridge` 실행
8. `~/.claude/css-dashboard/config.json` 작성 (`dashboard_enabled: true`)
9. 접속 주소 출력: `Dashboard up at http://<host-ip>:7421`

설치 완료 후 LAN 브라우저에서 아래 주소로 접속합니다.

```
http://<host-ip>:7421
```

---

## 설정 파일

설치 후 생성되는 주요 설정 파일입니다.

### `~/.claude/css-dashboard/config.json`

CSS 커맨드가 참조하는 대시보드 연동 설정입니다.

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

이 파일이 없거나 `dashboard_enabled: false`이면 모든 CSS 커맨드가 레거시 터미널 2선택지 모드로 동작합니다.

### `dashboard/.env`

docker-compose에 주입되는 런타임 환경 변수입니다. 커밋하지 마세요 (`.gitignore`에 포함됨).

```env
DB_PASSWORD=<랜덤 생성값>
DATABASE_URL=postgresql+asyncpg://css:<비밀번호>@postgres:5432/css_dashboard
DASHBOARD_PORT=7421
DASHBOARD_BIND=0.0.0.0
```

템플릿: `dashboard/.env.example`

### `config/dashboard-config.example.json`

CSS 커맨드 배포 시 참조하는 기본값 템플릿입니다. 실제 설정은 위의 `~/.claude/css-dashboard/config.json`이 사용됩니다.

---

## 업그레이드

새 버전으로 업그레이드할 때:

```bash
git pull
bash scripts/install-dashboard.sh --upgrade
```

스크립트가 이미지를 재빌드하고 새 Alembic 마이그레이션을 적용합니다.

---

## 제거

```bash
bash scripts/uninstall-dashboard.sh
```

스크립트가 수행하는 작업:

1. `systemctl --user disable --now css-dashboard-bridge`
2. `docker compose down` (볼륨 삭제 여부를 확인 프롬프트로 선택)
3. `~/.claude/css-dashboard/config.json`의 `dashboard_enabled`를 `false`로 변경 (CSS 파이프라인이 레거시 모드로 복귀)
4. `~/.claude/css-dashboard/` 전체 삭제 여부를 확인 프롬프트로 선택

볼륨을 삭제하면 히스토리와 색상 설정이 모두 지워집니다. 이후 재설치 시 초기 상태로 시작됩니다.

---

## 브리지 데몬 관리

브리지는 호스트에서 systemd 유저 서비스로 실행됩니다.

```bash
# 상태 확인
systemctl --user status css-dashboard-bridge

# 로그 조회 (실시간)
journalctl --user -u css-dashboard-bridge -f

# 수동 재시작
systemctl --user restart css-dashboard-bridge
```

`Restart=on-failure` 설정으로 비정상 종료 시 자동 재시작됩니다. 큐 파일은 재시작 후 재처리됩니다.

---

## Docker 컨테이너 관리

```bash
cd dashboard

# 상태 확인
docker compose ps

# 로그 조회
docker compose logs dashboard -f
docker compose logs postgres -f

# 재시작
docker compose restart dashboard

# 전체 중지
docker compose down
```

포트 7421이 다른 서비스와 충돌한다면 `dashboard/.env`의 `DASHBOARD_PORT`를 변경하고 `docker compose up -d`로 재시작하세요.

---

## 문제 해결

### 대시보드 접속 불가

1. `docker compose ps` — 컨테이너가 `Up` 상태인지 확인
2. `docker compose logs dashboard` — 시작 오류 메시지 확인
3. 방화벽: `sudo ufw status` — 포트 7421 허용 여부 확인 (`sudo ufw allow 7421/tcp`)

### 세션 카드가 나타나지 않음

1. `~/.claude/css-dashboard/projects.json` — 프로젝트가 등록되어 있는지 확인
2. `<project>/.claude/css/sessions/` — 세션 JSON 파일이 있는지 확인
3. `docker compose logs dashboard` — watchdog 오류 여부 확인
4. 세션 JSON이 네트워크 마운트 위에 있는 경우 watchdog이 동작하지 않을 수 있습니다. 로컬 파일시스템을 사용하세요.

### Gate 승인 후 파이프라인이 재개되지 않음

1. `systemctl --user status css-dashboard-bridge` — 브리지 실행 중인지 확인
2. `journalctl --user -u css-dashboard-bridge -f` — 오류 메시지 확인
3. `claude` CLI가 PATH에 있는지 확인: `which claude`
4. `~/.claude/css-dashboard/queue/failed/` — 실패한 큐 파일 확인

### `claude` CLI not in PATH 오류

`~/.claude/css-dashboard/config.json`의 `claude_cli` 값을 절대 경로로 변경합니다.

```json
{
  "claude_cli": "/usr/local/bin/claude"
}
```

변경 후 `systemctl --user restart css-dashboard-bridge`로 브리지를 재시작합니다.
