# CSS 파이프라인 GitHub 전환 설계

- **상태**: Draft (브레인스토밍 승인 완료, 구현 계획 대기)
- **작성일**: 2026-06-15
- **대상**: `/css:ship` 및 CSS 파이프라인 전 스테이지
- **요지**: 로컬 대시보드(FastAPI·React·Postgres·bridge 데몬)를 전면 제거하고, GitHub Issues + Projects를 파이프라인의 사람용 미러 + 게이트 제어 채널로 사용한다.

---

## 1. 배경 / 문제

현재 진행 상황 가시화와 게이트 승인은 로컬 대시보드가 담당한다:

- 로컬 웹앱(FastAPI + React + PostgreSQL + docker-compose, `:7421`)이 `<project>/.claude/css/sessions/*.json`을 읽어 칸반 보드 렌더링.
- 게이트 승인 = 카드를 게이트 경계로 드래그(review→execute = Gate 2, document→pr = Gate 3).
- **bridge 데몬**(systemd 사용자 서비스)이 큐를 감시하다 `claude --print '/css:ship --session <slug>'`(env `CSS_DASHBOARD_RESUME=1`)를 재실행해 파이프라인을 재개.

문제: 무거운 인프라(DB·웹앱·상주 데몬)를 깔아야 하고, 가시화·승인이 로컬에 갇혀 협업/원격 제어가 안 된다.

## 2. 목표 / 비목표

**목표**

1. `/css:ship <idea>` 실행 시 해당 slug에 대한 GitHub 이슈 생성.
2. 스테이지 진행에 따라 이슈에 **요약** 작업 기록 코멘트 + 중요 의사결정(ADR) 코멘트.
3. 단계 변경마다 이슈 라벨을 현재 상태(`css:<current_state>`)로 변경.
4. 이슈를 **유저 단위 통합 GitHub Projects 보드**에서 칸반으로 관리.
5. 사람 승인 게이트에서 이슈에 @mention → 사람이 댓글로 답하면 그 결정을 읽어 진행(터미널 답변과 동일 효과).
6. slug 개발 완료 시 PR 생성 + 이슈에 연결(`Closes #`).
7. 기존 대시보드 자산 전면 삭제, 백그라운드 인프라 0.

**비목표**

- GitHub를 파이프라인 상태의 **정본**으로 만들지 않는다(정본은 계속 로컬 JSON).
- 실시간 웹 UI를 자체 구현하지 않는다(GitHub Projects 기본 UI 사용).
- 비-GitHub / 오프라인 프로젝트 지원을 깨지 않는다(우아한 폴백).

## 3. 아키텍처 개요

```
/css:ship (터미널 세션, 인라인 폴링 — 서버 없음)
   │  각 스테이지 경계 / 게이트에서
   ▼
bash ~/.claude/css/lib/gh_sync.sh <subcommand> --session <slug>
   │  (gh + jq)
   ▼
GitHub  ── Issue (코멘트·라벨·@mention)  ──┐
        └─ Projects v2 보드 (Status 필드) ─┘  ← 사람이 보고/답함
```

- **정본 상태**: `<project>/.claude/css/sessions/<slug>.json`. 재개/락/스테이지 데이터는 지금과 동일하게 이 JSON이 관리.
- **GitHub = 미러 + 제어 채널**: JSON을 렌더링한 이슈/보드. 게이트에서만 사람 입력을 역방향으로 받는다.
- **로직 위치**: 신규 `gh_sync` 헬퍼 1곳. 명령 마크다운은 이 헬퍼를 호출만 한다(9개 명령에 gh 보일러플레이트 복붙 금지).

### 3.1 단일 책임 경계

- **명령 마크다운**(`ship.md` 등): 오케스트레이션, 세션 JSON의 비-github 키 쓰기, 게이트 답글 **해석**(자연어 → approve/draft/cancel).
- **`gh_sync` 헬퍼**: GitHub 측 부수효과(이슈/코멘트/라벨/보드/폴링) 전담. 세션 JSON에서 **`github` 하위 블록만** 읽고 쓴다(이슈 번호·보드 item id·ADR 마커·게이트 코멘트 id). 자연어 해석은 하지 않는다(Claude 몫).
- 두 쓰기 주체의 JSON 키가 disjoint(`github.*` vs 그 외)하고, 세션은 락으로 직렬화되므로 충돌 없음.

## 4. 크로스플랫폼 (Windows · Ubuntu)

- 헬퍼는 **bash + jq**로 작성. 호출은 항상 `bash "$HOME/.claude/css/lib/gh_sync.sh" <args>` 형태(주변 셸이 PowerShell이든 bash든 무관).
- **전제**: `git`은 이미 필수 도구이고, Windows의 표준 git 설치는 Git Bash(`bash.exe`)를 포함한다 → git이 있는 모든 환경에 bash가 존재. `gh`·`jq`도 기존 필수 도구.
- `install.sh`(Ubuntu)와 `install.ps1`(Windows) **둘 다** `lib/` → `~/.claude/css/lib/` 복사하도록 갱신.
- 라인 엔딩: 헬퍼는 LF 고정(`.gitattributes`로 `lib/*.sh text eol=lf` 보장).

## 5. 이슈 생애주기

`/css:ship <idea>` 시작 시(slug 확정 직후), `github.tracking_enabled == true` && GitHub 리모트 존재 시:

1. `gh_sync init-issue --session <slug>`:
   - 보드 미존재(`project_number == null`) 시 **최초 1회 자동 부트스트랩**: 유저 보드 + Status 단일선택 필드(옵션 8종) 생성, 번호를 전역 config에 영구 저장.
   - `gh issue create` — 제목 `[CSS] <idea 요약>`, 본문 = 아이디어 + 스테이지 체크리스트 + (Epic이면) 자식 Phase 자리표시. 라벨 `css:tracked` + `css:interview`.
   - `gh project item-add`로 보드에 추가, Status = `Interview`.
   - 이슈 번호·URL·보드 item id를 `session.github`에 기록.
2. **멱등성**: `session.github.issue_number`가 이미 있으면(재개/재시작) 재사용. 절대 재생성하지 않는다.

## 6. 스테이지별 코멘트 · 라벨 · 보드

각 스테이지 완료 경계에서 `ship.md`가 `gh_sync comment` + `gh_sync set-state` 호출.

### 6.1 코멘트 내용

- **interview(스펙) · plan · document 스테이지 → 문서 전체**를 코멘트 본문에 포함.
  - 산출물 파일(예: `docs/superpowers/specs/YYYY-MM-DD-*.md`, `docs/superpowers/plans/YYYY-MM-DD-*.md`, `docs/<slug>/README.md`)을 읽어 접이식 블록으로 게시:
    `<details><summary>📄 spec: <path></summary>\n\n<full markdown>\n</details>`
  - GitHub 코멘트 상한(65,536자) 초과 시 자동 분할(`(1/N)` 헤더), 또는 상한 근접 시 앞부분 + "전문은 `<path>` 참조" 링크.
- **그 외 스테이지(review·execute·verify) → 요약만**. 세션 JSON `phases.<stage>`에서 핵심 수치 추출:
  - `review`: `✅ review 완료 — verdict=PASS, findings c0/h0/m0/l3, rich-spec 캐시됨`
  - `execute`: `✅ execute 완료 — branch css/<slug>, 12 commits, tests 28/28, cov 97%`
  - `verify`: `✅ verify 완료 — verdict=PASS, cov 97%`

> 결정: 사용자 요구의 "spec 작성이나 문서 단계" = **interview + plan + document** (세 스테이지 모두 문서 전문 포함).

### 6.2 라벨 (현재 상태)

- 스테이지 진입마다 이전 `css:<prev>` 제거 + `css:<current>` 부여. 항상 현재 스테이지 1개(= `session.current_phase`)만 활성 + 영구 `css:tracked`.
- 라벨 세트(부족분은 `gh label create`로 자동 생성):
  - 스테이지: `css:interview` `css:plan` `css:review` `css:execute` `css:verify` `css:document` `css:pr`
  - 특수: `css:awaiting-approval`(게이트 대기), `css:done`(완료), `css:cancelled`(취소/중단)

### 6.3 보드 Status (라벨과 lockstep)

- `set-state`가 라벨 변경과 **동시에** 보드 item의 Status 단일선택을 같은 스테이지로 설정(`gh project item-edit`).
- Status 옵션: `Interview` `Plan` `Review` `Execute` `Verify` `Document` `PR` `Done`.
- GitHub Projects 내장 자동화에 의존하지 않고 파이프라인이 명시적으로 설정 → 결정적.

## 7. ADR 처리

- 스테이지 중 **중요 의사결정**이 있을 때만 별도 코멘트(`gh_sync adr ...`). 전부가 아님.
- 형식:
  ```
  ### 🏛️ ADR-<n>: <제목>
  - **Context**: ...
  - **Decision**: ...
  - **Consequences**: ...
  ```
- 주 출처: interview(스펙 핵심 결정), review(verdict 근거/트레이드오프).
- 재개 시 중복 게시 방지: `session.github.adrs[]`에 `{n, title, posted_at}` 마커 저장 후 게시.

## 8. 게이트 흐름 (terminal-first + 이슈 기록 + 원격 폴링)

Gate 2(pre-execute) / Gate 3(pre-pr)에서 기존 대시보드 분기를 GitHub 분기로 교체.

1. **게이트 오픈** — `gh_sync gate-open --session <slug> --gate <2|3>`:
   - 이슈에 @mention 게이트 코멘트 게시 + 라벨 `css:awaiting-approval` 추가.
   - 예: `@<user> ✋ **Gate 2 — pre-execute**\nplan 검증 완료(review PASS, c0/h0/m0/l3). 승인 시 worktree 생성 후 execute 시작.\n답글: \`approve\` / \`cancel\` (자유 문장·한국어 OK).`
   - 게이트 코멘트의 id/시각을 `session.github.gate<2|3>_comment`에 기록(폴링 기준점).
2. **터미널 AskUserQuestion 동시 표시**: `[Yes(여기서 승인) / 원격(이슈)에서 답변 / Cancel]`.
   - **Yes** → 즉시 승인(`source: terminal_ask`).
   - **Cancel** → 중단(라벨 `css:cancelled`).
   - **원격** → 인라인 폴링 진입(아래).
3. **인라인 폴링** — `gh_sync gate-wait --session <slug> --gate <g> --timeout 540`:
   - 헬퍼 내부에서 **bounded until-loop**(`gh issue view --json comments` → 게이트 코멘트 시각 이후 첫 사람 답글 탐지, 사이에 `poll_interval_sec` 대기). foreground `sleep` 무관(루프는 단일 bash 호출 안에서 ≤9분).
   - 답글 발견 시 그 본문을 stdout으로 반환, 미발견 시 빈 출력으로 timeout 종료.
   - **해석은 Claude가**: 반환된 본문을 자유 문장으로 해석 → approve / draft(Gate 3) / cancel. 애매하면 되묻는 코멘트 게시 후 `gate-wait` 재호출. timeout(빈 출력)이면 `gate-wait` 재호출(무기한 대기, 사용자가 터미널에서 끊을 때까지).
4. **게이트 클로즈**:
   - 결정은 채널 무관 **동일하게** `session.gates.gate<g>.{state, source, approved_at, draft?}`에 기록(`source: terminal_ask | issue_reply`).
   - `gh_sync gate-close --decision <d> --source <s>`: `css:awaiting-approval` 제거, 결과 코멘트(`✅ 승인됨 (이슈 답글)` 등) 게시, 다음 스테이지 라벨/Status로 전환.

"동일 효과" 보장: 터미널 답이든 이슈 답글이든 최종적으로 같은 `gates.*` 상태를 만들고 파이프라인은 동일 경로로 진행.

## 9. PR ↔ 이슈 연결

- `/css:pr` (및 `css-pr-creator`): PR 본문에 `Closes #<issue_number>` 포함 → 머지 시 이슈 자동 종료 + 타임라인에 PR이 이슈에 "tag"됨.
- PR 생성 후 `gh_sync pr-link`: 이슈에 `🔀 PR 생성: <url>` 코멘트, 라벨 `css:pr` + Status `PR`.
- 파이프라인 종료 시 `gh_sync finalize`: 라벨 `css:done` + Status `Done`(이슈 자동 종료는 PR 머지가 담당).

## 10. 멀티-Phase Epic (v1 포함)

- 각 slug(Epic·Phase 무관) = 이슈 1개.
- **Epic 이슈**: 본문에 자식 Phase 이슈를 체크리스트로 링크(`- [ ] Phase 1 — <label> #<child_issue>`). Phase 완료 시 해당 항목 체크.
- **Phase 이슈**: 자기 PR을 `Closes #<phase_issue>`로 연결. 스택 PR(`--base <predecessor>`)은 기존대로.
- 보드: Epic·Phase 이슈 모두 같은 유저 보드에 표시(Phase는 Status가 자기 진행 스테이지).
- `init-issue`가 `session.kind`(epic/phase/단일)에 따라 본문 템플릿 분기. Epic→Phase 링크는 `/css:phase`가 자식 세션 생성 후 `gh_sync link-child` 호출.

## 11. 설정 · 셋업 · 우아한 폴백

### 11.1 config (`config/default-config.json`에 추가)

```json
"github": {
  "tracking_enabled": true,
  "project_owner": null,      // 기본 = gh 인증 유저
  "project_number": null,     // 보드 최초 부트스트랩 후 채워짐
  "mention_user": null,       // 기본 = gh 인증 유저
  "auto_close_issue": true,   // Closes # (false면 Refs #)
  "poll_interval_sec": 20
}
```

기존 `dashboard_enabled` 개념과 `config/dashboard-config.example.json`은 제거.

### 11.2 셋업

- 최초 1회: `gh auth refresh -s project`(Projects 스코프 부여). 누락 시 헬퍼가 안내 메시지 출력 후 추적만 skip(파이프라인은 계속 진행).
- 보드/필드/라벨은 첫 실행 시 자동 생성(idempotent).

### 11.3 폴백 (비-GitHub / 오프라인)

- GitHub 리모트 없음 / `gh` 미인증 / `tracking_enabled=false` 중 하나라도면 → 모든 `gh_sync` 단계 no-op, **기존 터미널 게이트(AskUserQuestion) 그대로**. 파이프라인 동작 불변.

## 12. 삭제 범위

- `dashboard/` 전체(backend·frontend·bridge·alembic·docker-compose.yml·Dockerfile·.dockerignore·.env.example·pyproject.toml·README*).
- `scripts/install-dashboard.sh`, `scripts/uninstall-dashboard.sh`.
- `config/dashboard-config.example.json`.
- 추적 안 된 WIP 문서: `docs/superpowers/plans/2026-05-30-dashboard-epic-phase-view-skeleton.md`, `docs/superpowers/plans/dashboard-epic-phase-view-p1..p4.md`(구 대시보드용, 폐기).
- README(`README.md`·`README.en.md`)의 대시보드 섹션, `.gitignore`의 `dashboard/.env`.
- 세션 JSON 게이트의 `source: "dashboard_drag"`/`CSS_DASHBOARD_RESUME` 처리 → `issue_reply`로 교체(이전 대시보드 분기 제거).

> 과거 대시보드 설계/계획 문서(이미 커밋된 `docs/superpowers/specs|plans`)는 히스토리로 보존하되 본 문서가 대체함을 명시.

## 13. 영향 파일 / 변경 요약

- **수정**: `commands/ship.md`(이슈 생성·스테이지 sync·게이트 GitHub 분기), `commands/pr.md`·`agents/pr-creator.md`(`Closes #` + pr-link), `commands/phase.md`(Epic→child 링크), 각 스테이지 명령에 sync 훅(표준 호출 1줄), `config/default-config.json`, `scripts/install.sh`·`scripts/install.ps1`(lib/ 복사), `scripts/uninstall.*`, README, `.gitignore`, `.gitattributes`(신규/갱신).
- **신설**: `lib/gh_sync.sh`(+ 내부 함수), GitHub 추적 사용 문서(`docs/` 또는 README 섹션), `lib/` 단위 테스트.
- **삭제**: §12.

## 14. 테스트 전략

- 기존 방식 준수(골든/스키마 검증 + `tools/css_schema` 스타일). 프롬프트 명령은 단위테스트 하네스가 없으므로 구조 검증 + 행위 체크리스트 병행.
- **`gh_sync` 단위 테스트**: `gh`를 PATH 셰임(가짜 `gh` 스크립트가 인자/입력을 기록)으로 모킹해 각 subcommand의 인자 구성·멱등성·분할 로직·폴백 검증. **순수 bash assert**(외부 러너 의존 없음; CI는 Ubuntu, 로컬은 Git Bash).
- **명령 마크다운 구조 검증**: `ship.md`에 필요한 gh_sync 호출 단계/게이트 분기/Closes # 가 존재하는지 검사(기존 골든 테스트 스타일).
- **행위 체크리스트**(수동): 실제 토이 repo에서 이슈 생성→스테이지 라벨/코멘트→게이트 원격 답글→PR 링크 1회 end-to-end 확인.
- 대시보드 테스트(`dashboard/**/tests`, `bridge/tests`)는 삭제와 함께 제거.

## 15. 리뷰 포인트 (해소됨)

1. 전문 포함 범위 → **interview·plan·document 모두 전문 포함**(§6.1).
2. `gate-wait` 대기 알림 → **9분마다 "아직 대기 중" 1줄 출력**으로 확정.
3. 헬퍼 테스트 러너 → **순수 bash assert**(외부 러너 미도입)로 확정.

## 16. 합의된 결정 (브레인스토밍)

- 게이트 대기 = **인라인 폴링(서버 없음)**, 대시보드 전면 삭제.
- 게이트 채널 = **터미널 우선 + 이슈 기록**, "원격" 선택 시 이슈 폴링.
- 보드 = **유저 단위 통합 Projects 보드 1개**.
- 삭제 범위 동의 / `gh_sync` 헬퍼 채택(크로스플랫폼) / Epic·Phase v1 포함 / `Closes #` 자동 종료 / interview·plan·document 코멘트는 문서 전문 / 게이트 대기 알림 9분 / 테스트는 순수 bash assert.
