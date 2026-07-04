<!-- css:updated: 079b623 2026-07-04 -->

# GitHub 추적

## 1. 현재 동작

`/css:ship`를 실행하면 파이프라인 진행 상황이 상주 서버 없이 `gh` CLI만으로 GitHub Issues + Projects에 미러링됩니다 (`README.md:177`, `lib/gh_sync.sh:1-4`). 슬러그마다 이슈 1개가 생성되어 유저 단위 Projects 칸반 보드에 등록되고(`lib/gh_sync.sh:126-143`), 스테이지 전환마다 라벨(`css:interview`…`css:pr`, 완료 시 `css:done`)과 보드의 `CSS Stage` 컬럼이 함께 이동합니다(`lib/gh_sync.sh:196-208`). **정본은 로컬**입니다 — GitHub는 사람용 미러일 뿐, 상태의 정본은 `<project>/.claude/css/sessions/<slug>.json`입니다 (`README.md:186`).

Epic이 여러 Phase로 분해되면 각 Phase는 Epic 이슈 아래 GitHub 네이티브 **서브이슈**로 등록되어 내용이 개별 동기화됩니다(구버전 GitHub는 체크리스트로 폴백) (`lib/gh_sync.sh:310-341`).

## 2. 인터페이스

`lib/gh_sync.sh <subcommand> [--flag value ...]` — 서브커맨드: `enabled | init-issue | comment | set-state | adr | adr-list | gate-open | gate-wait | gate-close | pr-link | finalize | link-child | wiki-publish` (`lib/gh_sync.sh:11-15`).

파이프라인 커맨드는 매 Bash 호출마다 헬퍼를 재정의해서 사용합니다:
```bash
CSS_PLUGIN_DIR="${CLAUDE_PLUGIN_ROOT}"; CSS_PLUGIN_DIR="${CSS_PLUGIN_DIR:-$HOME/.claude/css}"
GHS() { bash "${CSS_LIB:-$CSS_PLUGIN_DIR/lib}/gh_sync.sh" "$@"; }
```
(`commands/ship.md:21`, `commands/wiki.md:29`) — `CSS_ROOT`는 절대 설치 디렉터리 이름으로 export하면 안 되며(gh_sync.sh가 세션 조회용 **프로젝트** 루트로 읽음), `GHS`는 항상 프로젝트 루트에서 실행합니다.

승인 게이트는 이슈에 `@멘션`이 달리고 `approve`/`cancel`(Gate 3는 `draft` 포함) 자유 문장(한국어 OK)으로 답할 수 있습니다 (`lib/gh_sync.sh:235-260`, `commands/ship.md:57-95, 106-142`).

## 3. 내부 설계 요점

- **인라인 폴링, 서버 없음**: `gate-wait`는 최대 9분(`timeout=540`) 동안 `poll_interval_sec`(기본 20초)마다 REST `since` 필터로 새 코멘트를 확인 — `gh issue view --json comments`의 100개 제한을 피하려 페이지네이션 REST API를 우선 사용 (`lib/gh_sync.sh:261-286`, `lib/gh_sync.sh:248-256` 주석).
- **ADR 코멘트**: review 단계의 중요 결정이 `### 🏛️ ADR-N` 형식 이슈 코멘트로 남고 세션의 `github.adrs[]`에 번호·제목이 기록된다 (`lib/gh_sync.sh:210-221`).
- **Graceful degradation**: `gh_enabled()`가 `github.tracking_enabled`, `gh` 설치, `gh auth status`, `gh repo view` 네 조건을 모두 확인하며 하나라도 실패하면 모든 GHS 서브커맨드가 조용히 스킵되어 파이프라인은 순수 터미널 게이트로 폴백한다 (`lib/gh_sync.sh:60-67`).
- **PR 연결**: `pr-link`가 이슈에 PR 링크 코멘트를 달고 상태를 `pr`로 전환하며, PR 본문 자체의 `Closes #<issue>`는 `css-pr-creator`(via `commands/pr.md:61`)가 작성한다 (`lib/gh_sync.sh:296-303`).
- **설정 키**: `github.tracking_enabled`(기본 true), `github.project_owner`/`project_number`(미설정 시 자동 생성), `github.mention_user`, `github.auto_close_issue`(기본 true), `github.poll_interval_sec`(기본 20) — `lib/gh_sync.sh`가 세션이 아닌 자체 설정 해석(`$CSS_CONFIG` → 유저 설정 → 번들)으로 직접 읽는다 (`config/default-config.json:26-33`, `docs/session-schema.md:73`).

## 4. 데이터

`session.github` 필드(`issue_number`, `issue_url`, `repo`, `project_item_id`, `adrs[]`, `gate2`, `gate3`)는 [data/schema.md](../data/schema.md#session)를 참조하세요. 별도의 영속 DB는 없으며 상태는 GitHub 이슈/보드와 세션 JSON에만 존재합니다.

## 5. 제약·알려진 한계

- Projects 보드 생성/갱신에는 `gh auth refresh -s project` 스코프가 최초 1회 필요합니다 (`README.md:189`).
- 대시보드(별도 백엔드/프론트엔드로 세션 이력을 시각화하는 레이어)는 설계 논의는 있었으나(`docs/superpowers/plans/2026-06-15-github-pipeline-tracking-p3-dashboard-removal.md` 파일명 자체가 "제거"를 시사) 코드베이스에 구현 흔적이 없다 — 미확인/범위 밖으로 처리.
- Private 저장소가 Free 요금제이거나 Wiki가 비활성화된 경우 이 영역 자체는 영향받지 않지만 Wiki 미러(별도 영역, [project-docs-curation](project-docs-curation.md))는 스킵됩니다.

## 6. 변경 이력

| 날짜 | slug | 요약 | PR |
|---|---|---|---|
| 2026-06-15 | (설계, 미확인 slug) | GitHub Issues/Projects 파이프라인 추적 도입 — 인라인 폴링, 터미널 우선 게이트, ADR 코멘트 | 미확인 |
| 2026-07-04 | (bootstrap) | `docs/project/` 최초 생성 — 이 페이지 신설 | — |
