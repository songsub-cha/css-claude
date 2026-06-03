# CSS Codex CLI 호환 — 설계 문서

- **날짜:** 2026-06-03
- **세션 slug:** `css-codex-compat`
- **상태:** 승인 대기 (브레인스토밍 게이트 — 사용자 검토 중)
- **유형:** CSS 파이프라인 이식성 (OpenAI Codex CLI 호환 레이어)

---

## 1. 배경 & 문제

CSS 파이프라인(`/css:interview` → `plan` → `phase` → `review` → `execute` → `verify` → `document` → `pr`, 그리고 오케스트레이터 `/css:ship`)은 전적으로 **Claude Code 전용**으로 만들어졌다. 커맨드 9개(`commands/*.md`), 전문가 에이전트 21개(`agents/*.md`), `config/`, 설치 스크립트, 대시보드로 구성된다.

목표는 **OpenAI Codex CLI에서도 동일 파이프라인을 동작**시키되 **기존 Claude Code 동작은 한 줄도 깨지 않는 것**이다. Codex App(샌드박스/클라우드)은 2차이며 v1에서는 우아한 degrade만 보장한다.

### Claude Code 결합 인벤토리

| 요소 | Claude Code | Codex 대응 | 심각도 |
|------|-------------|------------|:---:|
| 슬래시 커맨드 `commands/*.md` (`description`/`argument-hint`, `/css:` 네임스페이스) | 네이티브 | `~/.codex/prompts/*.md` 커스텀 프롬프트. `:` 네임스페이스 없음 | 中 |
| 서브에이전트 `agents/*.md` 21개 (`name`/`model`/`css_stages`/`disallowedTools`) | `~/.claude/agents/`에 설치되는 1급 객체 | 명명 에이전트 레지스트리 없음. `multi_agent` 플래그의 익명 `spawn_agent`만 존재 | 최상 |
| 에이전트별 모델 opus/sonnet/haiku | frontmatter `model:` | 세션 단일 모델. 비용 티어링 불가 | 高 |
| `AskUserQuestion` (승인 게이트 3개) | 구조화 선택 UI 툴 | 구조화 질문 툴 없음 → 평문 질의·대기 | 中 |
| `Skill` 툴 → `superpowers:*` 호출 | 플러그인/Skill 툴 | **이미 해결.** Codex에서 skill 네이티브 로드 | 低 |
| worktree 생성 `git worktree add -b` | 자유로운 git | Codex App 샌드박스에서 detached HEAD + `checkout -b` 차단 | 中 |
| `gh pr create` | 동작 | Codex App 샌드박스에서 네트워크 차단 (CLI는 OK) | 中 |
| `TodoWrite` | 네이티브 | `update_plan` | 低 |
| `$ARGUMENTS` (커맨드 9개 전부) | 인자 토큰 | **Codex도 동일 지원** → 변환 불필요 | 없음 |

**선행 사실:** CSS가 의존하는 `superpowers` 플러그인은 이미 Codex 호환 작업을 끝냈다 — `.codex-plugin/plugin.json`, `skills/using-superpowers/references/codex-tools.md`(툴 매핑), `scripts/sync-to-codex-plugin.sh`, 환경 감지 패턴. 본 설계는 이 검증된 패턴을 차용한다.

---

## 2. 목표 & 원칙

- **Claude 不깨짐:** `commands/`, `agents/`, 기존 `install.sh`/`install.ps1`는 무수정. 모든 Codex 산출물은 설치 시점에 별도로 생성된다.
- **단일 소스:** repo의 `commands/`·`agents/`가 유일 진실의 원천. Codex용 본문을 따로 유지하지 않는다 (drift 방지).
- **토큰 절약:** 플랫폼에 따라 의미가 갈리는 메타(`model:` 등)는 런타임에 들고 다니며 중화하지 않고, **변환 시점에 제거**한다.
- **우아한 degrade:** Codex 제약(단일 모델, 구조화 질문 없음, 샌드박스 git)은 "동작 유지, UX만 저하"로 처리하고 RUNTIME.md에 문서화한다.
- **개인 설치 범위:** 마켓플레이스 발행은 비범위 (`.codex-plugin/` 매니페스트, sync 스크립트 없음).

---

## 3. 범위

### 3.1 In scope

1. `scripts/install-codex.sh` + `scripts/install-codex.ps1` — Codex 설치 스크립트(변환·복사).
2. `codex/RUNTIME.md` (신규 소스) — Codex 실행 두뇌(툴 매핑 + 하이브리드 분기 + degrade 규칙).
3. 변환 로직 — `commands/*.md` → `~/.codex/prompts/css-*.md`, `agents/*.md` → `~/.codex/css/agents/*.md` + `index.json`, `config/` 복사.
4. 테스트 — 설치 idempotency, 변환 충실도, RUNTIME 매핑 lint, 상태 경로 일치, Claude 회귀 무영향.
5. 문서 — `docs/installation` Codex 섹션 + README Codex 사용 안내.

### 3.2 Out of scope (v1 제외)

- 마켓플레이스 발행(`.codex-plugin/plugin.json`, `sync-to-codex-plugin.sh`).
- 대시보드 + 브리지 Codex 연동 (브리지가 `claude`를 spawn — Claude 전용 유지).
- Codex App 완전 finishing 흐름 (env 감지 가드로 degrade만; 완전 대응은 v2).
- 모델 티어링 재현 (Codex 단일 모델 — 구조적으로 불가).
- 에이전트 본문/커맨드 본문 리팩터 (무수정 원칙).

---

## 4. 확정된 결정 (브레인스토밍 게이트)

| # | 결정 | 선택 | 근거 |
|---|------|------|------|
| D1 | 배포 범위 | **개인 설치만** | README "개인 사용" 기조 유지, 작업량 최소. codex-tools 매핑·env 감지 "패턴"은 차용하되 발행용 자산은 제외 |
| D2 | 에이전트 실행 모델 | **하이브리드 (감지 후 폴백)** | `multi_agent` 가능 시 `spawn_agent`로 병렬+격리(Claude에 근접), 없으면 순차 단일 에이전트. 양쪽 환경 커버 |
| D3 | 소스 관리 | **단일 소스 + 설치 시 변환·복사** | repo `commands`/`agents`가 유일 소스. Claude 파일 무수정 → 회귀 위험 최소, drift 없음 |
| D4 | 세션 상태 위치 | **공유 — 둘 다 `<project>/.claude/css/`** | cross-tool resume 가능(Claude↔Codex), Claude 파일 무수정 |
| D5 | `model:` frontmatter 처리 | **변환 시 제거(분리)** | 런타임 중화는 매 호출 토큰 낭비. Codex 복사본에서 아예 떼어내 RUNTIME 규칙 불필요 |
| D6 | `Task()` → 행동 해석 | **α: RUNTIME.md 매핑 해석** | 본문 무수정 + 프롬프트별 1줄 포인터. 설치 시 재작성(β)·AGENTS.md 주입(γ)은 취약/침범적이라 기각 |

---

## 5. 아키텍처 — 설치 레이아웃

```
~/.codex/
├── prompts/
│   └── css-<stage>.md      ← commands/<stage>.md  (/css-ship, /css-interview, …)
└── css/
    ├── RUNTIME.md          ← 실행 두뇌 (codex/RUNTIME.md에서 복사)
    ├── agents/
    │   ├── <name>.md       ← agents/*.md 21개, frontmatter 전체 제거 후 본문만
    │   └── index.json      ← subagent_type → 파일 경로 맵 (설치 시 생성)
    └── config.json         ← config/default-config.json (Claude와 동일)
```

- Codex는 `:` 네임스페이스가 없으므로 `/css:ship` → **`/css-ship`** (`css-` 프리픽스). 9개 스테이지 + ship 모두 동일 규칙.
- 에이전트 본문은 **Codex 명명 에이전트로 등록되지 않는다.** 런타임이 읽어 `spawn_agent` 프롬프트로 쓰거나 인라인하는 *데이터 파일*이다.
- 세션 상태는 D4대로 `<project>/.claude/css/`를 그대로 읽고 쓴다. Codex 산출물은 이 경로를 변경하지 않는다.
- 사용자 전역 `~/.codex/AGENTS.md`는 **건드리지 않는다.** 각 프롬프트가 맨 위 1줄 포인터로 RUNTIME.md를 참조한다(D6).

---

## 6. `RUNTIME.md` — 실행 두뇌

각 설치된 프롬프트는 맨 위에 1줄 포인터를 갖는다: *"진행 전 `~/.codex/css/RUNTIME.md`의 실행 모델·툴 매핑을 따르라."* RUNTIME.md 내용:

### 6.1 툴 매핑

| 본문이 부르는 것 | Codex 동작 |
|---|---|
| `Task(subagent_type=X, prompt=P)` | `css/agents/index.json`에서 X resolve → **`spawn_agent` 가능 시** 본문+P를 프롬프트로 spawn(병렬 호출 후 `wait_agent`·`close_agent`), **불가 시** 그 본문 지시를 메인 스레드에서 순차 수행 |
| 다중 `Task` 병렬 | 다중 `spawn_agent`; 폴백 시 순차 |
| `TodoWrite` | `update_plan` |
| `AskUserQuestion(question, options=[…])` | 질문 + 번호 매긴 옵션을 **평문 출력 후 사용자 입력 대기** → 응답을 옵션에 매핑 |
| `Read`·`Write`·`Edit`·`Bash` | 네이티브 파일/셸 툴 |

### 6.2 capability 감지 (하이브리드 분기)

`spawn_agent` 사용 가능 여부로 병렬/순차를 결정한다. 에이전트는 자신의 툴셋을 알고 있으므로, "spawn_agent가 있으면 병렬 dispatch 경로, 없으면 순차 inline 경로"를 RUNTIME.md가 명시한다. (`multi_agent`는 `~/.codex/config.toml`의 `[features] multi_agent = true`로 켠다 — 설치 안내에 포함.)

### 6.3 에이전트 해석

`subagent_type`(예: `css-reviewer`)를 `index.json`에서 파일 경로로 resolve한다. `index.json`은 설치 시 각 에이전트 frontmatter의 `name`에서 생성한다(`css-reviewer` → `agents/reviewer.md`).

### 6.4 환경 감지 (worktree / finish) — superpowers 패턴

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
BRANCH=$(git branch --show-current)
```

- `GIT_DIR != GIT_COMMON` → 이미 linked worktree → `/css-execute`의 worktree 생성 skip.
- `BRANCH` 빈 값 → detached HEAD(샌드박스) → 브랜치/푸시/PR 불가 → finish 시 handoff.

### 6.5 PR / finish

`gh`가 있고 인증+네트워크면 PR 생성. 아니면 브랜치명·커밋 메시지·PR 본문을 **handoff 페이로드로 출력**해 사용자가 호스트 UI/로컬에서 마무리.

> **모델 티어링 없음:** Codex는 세션 단일 모델로 동작한다. Claude의 작업별 저비용 모델 전환(haiku/sonnet/opus)은 일어나지 않는다. (이 사실은 README/본 spec에만 기록하며, `model:` 필드는 D5대로 변환 시 제거되므로 RUNTIME에 별도 런타임 규칙을 두지 않는다.)

---

## 7. 변환 규칙 (설치 스크립트가 파일마다 하는 일)

| 입력 | 처리 | 출력 |
|------|------|------|
| `commands/*.md` | frontmatter에서 Claude 전용 키(`argument-hint`) 제거, `description`은 Codex 지원 시 유지(미지원 시 드롭). **본문 내용 무수정** — 선두에 RUNTIME 포인터 1줄만 부가. `$ARGUMENTS` 그대로 | `~/.codex/prompts/css-*.md` |
| `agents/*.md` | frontmatter **전체 제거**(본문만 유지) — `model`(D5)·`disallowedTools`·`css_stages`·`adapted_from`·`description` 모두. `name`은 제거 전 `index.json` 생성에만 사용. **본문 무수정** | `~/.codex/css/agents/*.md` |
| (생성) | 각 에이전트 `name` → 파일 경로 맵 | `~/.codex/css/agents/index.json` |
| `config/default-config.json` | 그대로 복사 | `~/.codex/css/config.json` |
| `codex/RUNTIME.md` | 그대로 복사 | `~/.codex/css/RUNTIME.md` |

**소스 분리 상태:**

| | `model:` |
|---|---|
| repo `agents/*.md` (소스) | 유지 — Claude가 사용. 무수정 |
| `~/.codex/css/agents/*.md` | 제거 — 변환 시 분리 |

설치 스크립트는 idempotent(재실행 안전)해야 하며, `FORCE` 없이는 기존 `config.json`을 덮지 않는다(기존 install.sh 관례 계승).

---

## 8. 데이터 흐름 — `/css-review` 예시

```
/css-review → RUNTIME.md 로드 → css-reviewer + 도메인 전문가 필요
  ├─ spawn_agent 가능: 전문가별 spawn_agent 병렬 → wait_agent → rich spec을
  │                    .claude/css/plans/{slug}-T*.md 에 수집 → close_agent
  └─ spawn_agent 불가: 메인 에이전트가 reviewer → 각 전문가 지시문을 순차 수행,
                       동일 산출물을 동일 경로에 기록
→ Gate 2: AskUserQuestion 매핑(평문 질문 + 입력 대기) → /css-execute
```

전 스테이지가 동일 패턴: 본문은 Claude 그대로, RUNTIME.md가 `Task`/`AskUserQuestion`/`TodoWrite`를 Codex 동작으로 치환. 산출물 경로는 양 도구 공통(`.claude/css/`).

---

## 9. Graceful degradation (전부 RUNTIME.md에 문서화)

| 제약 | degrade 동작 |
|------|------|
| `multi_agent`/`spawn_agent` 없음 | 순차 단일 에이전트 (context 격리·병렬성 포기, 결과 동일) |
| Codex App 샌드박스 worktree 차단 | env 감지 → 생성 skip / detached 시 handoff |
| `gh` 없음·미인증·네트워크 차단 | PR 대신 handoff 페이로드 출력 |
| 구조화 질문 없음 | 게이트를 평문 질의 + 대기로 |
| 모델 티어링 불가 | 세션 단일 모델 (비용 차등 없음) |

모두 "동작 유지, UX만 저하"이며 파이프라인 정합성(산출물·게이트·상태)은 보존한다.

---

## 10. 테스트

- **설치 idempotency:** 임시 `HOME`에 `install-codex` 2회 → 경로/포인터/`index.json`/`RUNTIME.md` 존재, 2회차 변경 없음.
- **변환 충실도:** 샘플 커맨드 변환 후 본문이 원본과 동치(+포인터 1줄)인지, `$ARGUMENTS` 보존 여부 assert.
- **frontmatter 분리:** 변환된 에이전트 복사본에 `model:`/`disallowedTools`/`css_stages`가 **없음** assert. 소스 `agents/*.md`는 `model:` **유지** assert(분리 정합성).
- **`index.json` 정합성:** 21개 에이전트 `name` ↔ 파일 1:1 매핑 검증 (`tools/agent_registry/` 재사용 가능).
- **RUNTIME 매핑 lint:** RUNTIME.md에 필수 매핑(`Task`/`TodoWrite`/`AskUserQuestion`/env 감지/`gh` handoff) 항목 존재 grep.
- **상태 경로 일치:** Codex 산출물이 `.claude/css/`를 가리킴 assert.
- **Claude 회귀:** `commands/`·`agents/`·`install.sh`/`install.ps1` 무수정 → 기존 Claude 골든/설치 테스트 영향 없음.
- **(수동) Codex CLI 스모크:** `multi_agent` on/off 각각에서 `/css-interview` 등 실행. (현 개발 머신에 codex 바이너리 없음 → 수동/문서화.)

---

## 11. 바뀌지 않는 것 (Claude Code 측)

- `commands/*.md`, `agents/*.md` — 본문·frontmatter 전부 무수정.
- `scripts/install.sh`, `scripts/install.ps1` — 무수정.
- `config/`, 대시보드, 브리지 — 무수정.
- 세션 상태 스키마·경로(`.claude/css/`) — 무수정 (Codex가 같은 경로 공유).

---

## 12. 미해결 / 리스크

- **Codex 커스텀 프롬프트 frontmatter 지원 범위:** `description` 지원 여부가 버전별로 다를 수 있음 → 변환은 "지원 시 유지, 아니면 본문화"로 보수적으로.
- **`multi_agent` API 안정성:** 실험 플래그이며 빌드별 차이(과거 `wait` → 현 `wait_agent`) 존재. RUNTIME.md는 현행 `spawn_agent`/`wait_agent`/`close_agent` 기준, 폴백이 안전망.
- **Codex 프롬프트 네임스페이스:** `:` 미지원 가정 → `css-` 프리픽스. Codex가 하위 디렉토리 네임스페이스를 지원하면 후속에서 재검토.
- **Codex App(v2):** env 감지 가드로 degrade만 보장. 완전한 "Create branch" handoff 흐름은 별도 설계.

---

## 13. 향후 (Future)

- 마켓플레이스 발행이 필요해지면 `.codex-plugin/plugin.json` + sync 스크립트를 superpowers 패턴대로 추가(D1 재검토).
- 대시보드 브리지가 `codex`도 spawn하도록 확장하면 Codex 세션도 Kanban·게이트 시각화 가능.
- Codex App 완전 대응(샌드박스 finishing UI 연동).
