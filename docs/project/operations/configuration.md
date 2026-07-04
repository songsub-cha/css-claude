<!-- css:updated: 079b623 2026-07-04 -->

# 설정

## 1. 환경변수

| 키 | 필수 | 기본값 | 설명 | 정의·사용 위치 |
|---|---|---|---|---|
| `CLAUDE_PLUGIN_ROOT` | 아니오(플러그인 모드에서 Claude Code가 자동 설정) | — | 플러그인 설치 디렉터리. 커맨드/에이전트 본문에서 인라인 치환됨 | `commands/ship.md:21`, `commands/wiki.md:29` |
| `CSS_LIB` | 아니오 | `${CLAUDE_PLUGIN_ROOT 또는 ~/.claude/css}/lib` | `gh_sync.sh` 위치 override (테스트/스크립트 모드용) | `commands/ship.md:21` |
| `CSS_ROOT` | 아니오 | `$PWD` | `gh_sync.sh`가 세션 파일을 찾는 **프로젝트 루트**. 설치 디렉터리 이름으로 절대 export하면 안 됨 | `lib/gh_sync.sh:53`, `commands/ship.md:21` (경고 문구) |
| `CSS_CONFIG` | 아니오 | `~/.claude/css/config.json` → 번들 `config/default-config.json` 순으로 탐색 | 설정 파일 경로 override | `lib/gh_sync.sh:29-37` |
| `GH_COMMENT_LIMIT` | 아니오 | `60000` | 이슈 코멘트 청크 분할 임계 문자수 | `lib/gh_sync.sh:146` |
| `CSS_WIKI_URL` | 아니오 | (미설정 시 `gh repo view`로 자동 해석) | Wiki git remote override — 테스트 seam | `lib/gh_sync.sh:417` |
| `FORCE` | 아니오 | `0` | Ubuntu 설치 스크립트가 기존 개인 설정을 덮어쓸지 여부 | `scripts/install.sh:12` |
| `CLAUDE_CONFIG_DIR` | 아니오 | `$HOME/.claude` | 설치 스크립트가 대상으로 삼는 Claude 설정 디렉터리 | `scripts/install.sh:11` |

시크릿 값은 위 표에 없습니다 — 아래 §3 참조.

## 2. 설정 파일

### 2.1 `config/default-config.json` (번들 기본값)

세션의 `session.config`는 인터뷰 단계에서 유저 설정을 이 번들 기본값 위에 deep-merge한 결과입니다 (`commands/interview.md:25`).

| 키 | 기본값 | 설명 |
|---|---|---|
| `interview.ambiguity_threshold` | `0.2` | 브레인스토밍 모호성 임계치 |
| `interview.max_rounds` | `20` | 브레인스토밍 최대 질의 라운드 |
| `review.max_loopback_attempts` | `2` | review→plan 루프백 한도 |
| `verify.coverage_threshold` | `85` | 커버리지 최소 요구치(%) |
| `verify.max_loopback_attempts` | `3` | verify→execute 루프백 한도 |
| `execute.tdd_self_heal_max` | `2` | 태스크당 debugger self-heal 시도 횟수 |
| `execute.worktree_parent` | `null`(→`..`) | worktree 상위 디렉터리. `.worktrees`로 설정하면 저장소 내부에 worktree 생성 |
| `pr.default_base_branch` | `null` | PR 기본 base 브랜치 |
| `pr.default_draft` | `false` | 기본 draft 여부 |
| `github.tracking_enabled` | `true` | GitHub 추적 켬/끔 |
| `github.project_owner` | `null` | Projects 보드 소유자(미설정 시 `gh api user` 로그인 계정) |
| `github.project_number` | `null` | Projects 보드 번호(미설정 시 자동 생성) |
| `github.mention_user` | `null` | 게이트 알림 시 멘션할 사용자(미설정 시 로그인 계정) |
| `github.auto_close_issue` | `true` | PR 본문에 `Closes #`를 넣어 자동 종료할지 |
| `github.poll_interval_sec` | `20` | 게이트 원격 폴링 주기(초) |

(출처: `config/default-config.json:1-34`)

유저 오버라이드는 `~/.claude/css/config.json`에 위 구조와 동일한 키만 덮어써서 배치합니다. `writable_config_path()`는 쓰기 대상이 절대 번들 플러그인 사본을 향하지 않도록 보장합니다 (`lib/gh_sync.sh:44-52`).

### 2.2 `.claude-plugin/plugin.json` / `.claude-plugin/marketplace.json`

플러그인 배포 메타데이터. 상세는 [features/plugin-distribution.md](../features/plugin-distribution.md) 참조.

## 3. 시크릿

CSS 자신은 시크릿을 저장하지 않습니다. 유일한 외부 인증은 **GitHub CLI(`gh`) 인증 토큰**이며, `gh`가 자체 관리(keyring/설정 파일)합니다. CSS는 `gh auth status`로 인증 여부만 확인하고 토큰 값을 직접 다루거나 세션 JSON/설정 파일에 기록하지 않습니다 (`lib/gh_sync.sh:63`, `docs/installation.md:9`).

주입 방법: 사용자가 최초 1회 `gh auth login`(및 Projects 보드용 `gh auth refresh -s project`)을 실행하면 이후 모든 `gh` 호출이 자동으로 인증됩니다 (`README.md:189`).
