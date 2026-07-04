> [English](usage.md) · **한국어**

# 사용법

## 빠른 시작

git 프로젝트 어디서든:

```
/css:ship "<아이디어>"
```

파이프라인이 interview → plan → phase → review → execute → verify → document → pr 순서로 진행되며, 3개의 승인 게이트가 있습니다.

## 단독 커맨드

각 단계는 `--session`과 함께 독립적으로 실행할 수도 있습니다:

```
/css:interview "<아이디어>"
/css:plan --session <slug>
/css:phase --session <slug>
/css:review --session <slug>
/css:execute --session <slug>
/css:verify --session <slug>
/css:document --session <slug>
/css:pr --session <slug>
/css:clean --session <slug>    # PR 머지 후 정리
/css:wiki                      # (수시) docs/project/ 살아있는 문서 갱신 + Wiki 미러
```

`--session`은 생략 가능합니다. 생략하면 CSS가 `<project>/.claude/css/sessions/_active.json`에서 가장 최근 세션을 자동으로 찾습니다.

## Codex App / CLI 대응 skill

`scripts/install-codex.*` 설치 후 Codex에서는 같은 단계를 설치된 `css-*` skills로 사용합니다. App/CLI의 skill 메뉴에서 선택하거나 직접 mention합니다:

```
$css-ship "<아이디어>"
$css-review --session <slug>
```

전체 목록은 `$css-interview`, `$css-plan`, `$css-phase`, `$css-review`, `$css-execute`, `$css-verify`, `$css-document`, `$css-pr`, `$css-clean`입니다. Skill invocation 뒤의 텍스트는 커맨드의 `$ARGUMENTS`로 해석하며, 실행 동작은 `~/.codex/css/RUNTIME.md`가 규정합니다.

## 멀티 세션 동시 실행

같은 프로젝트에서 터미널을 두 개 열어 동시에 작업할 수 있습니다:

```
# 터미널 1
/css:ship "기능 A"

# 터미널 2
/css:ship "기능 B"
```

각 호출은 독립된 슬러그를 생성하고 별도의 세션 파일, 별도의 워크트리, 별도의 브랜치로 격리됩니다. 두 세션은 서로의 상태에 영향을 주지 않습니다.

## 산출물 위치

| 종류 | 경로 |
|------|------|
| Spec | `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md` |
| Plan | `docs/superpowers/plans/YYYY-MM-DD-<feature>.md` |
| 스테이징 (review / execute / verify / document) | `<project>/.claude/css/{reviews,executions,verifies,documents}/` |
| 태스크 단위 Rich Spec | `<project>/.claude/css/plans/{<slug>-T<task-id>.md | <epic>-p<phase>-T<task-id>.md}` |
| 최종 사용자 문서 | `<project>/docs/<slug>/{README,api,changelog}.md` |
| 구현 브랜치 | `css/<slug>` (워크트리: `../<repo>-css-<slug>`) |

## 재개

- `Ctrl+C`는 언제든 안전합니다. 세션 상태가 유지됩니다.
- `/css:ship --session <slug>` (또는 `--session`을 붙인 단독 커맨드)로 재시작하면 중단된 단계부터 자동으로 이어집니다.

## 정리

PR이 머지되면 워크트리와 로컬 브랜치를 정리할 수 있습니다:

```
/css:clean --session <slug>
```

dirty 변경·미푸시 커밋·미머지 PR이 있으면 확인 없이 삭제하지 않습니다. `--keep-branch`로 로컬 브랜치를 남길 수 있고, 원격 브랜치는 건드리지 않습니다.

## 프로젝트 문서 (/css:wiki)

slug별 스냅샷(`docs/<slug>/`)과 별개로, `docs/project/`를 "현재 상태" 문서(기능 SoT ·
아키텍처 · 데이터 스키마 · 운영 · ADR)로 유지합니다. 세션과 무관하게 아무 때나 실행할 수
있고, 파이프라인을 거치지 않은 손 커밋도 diff 기반으로 반영됩니다.

```
/css:wiki                # docs/project/ 없으면 전체 부트스트랩, 있으면 증분 갱신
/css:wiki --init         # 전체 재생성 강제
/css:wiki --no-publish   # in-repo 커밋까지만 (Wiki 미러 생략)
```

- 변경은 페이지별 요약 + 승인 게이트 후 `docs/project/`만 스코프해 커밋됩니다.
- 동기화 기준점은 `docs/project/README.md` 푸터의 `css:last-synced` 마커입니다.
- GitHub Wiki가 불가한 환경(private + Free 요금제, 미초기화 wiki, gh 미인증)에서는 미러만
  건너뛰고 나머지는 동일하게 동작합니다.
