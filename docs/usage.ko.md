> [English](usage.md) · **한국어**

# 사용법

## 빠른 시작

git 프로젝트 어디서든:

```
/css:ship "<아이디어>"
```

파이프라인이 interview → plan → review → execute → verify → document → pr 순서로 진행되며, 3개의 승인 게이트가 있습니다.

## 단독 커맨드

각 단계는 `--slug`와 함께 독립적으로 실행할 수도 있습니다:

```
/css:interview "<아이디어>"
/css:plan --slug <slug>
/css:review --slug <slug>
/css:execute --slug <slug>
/css:verify --slug <slug>
/css:document --slug <slug>
/css:pr --slug <slug>
```

`--slug`는 생략 가능합니다. 생략하면 CSS가 `<project>/.claude/css/sessions/_active.json`에서 가장 최근 세션을 자동으로 찾습니다.

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
| 도메인 전문가 Rich Spec | `<project>/.claude/css/plans/<domain>-spec-<slug>-<ts>.md` |
| 최종 사용자 문서 | `<project>/docs/<slug>/{README,api,changelog}.md` |
| 구현 브랜치 | `css/<slug>` (워크트리: `../<repo>-css-<slug>`) |

## 재개

- `Ctrl+C`는 언제든 안전합니다. 세션 상태가 유지됩니다.
- `/css:ship --slug <slug>` (또는 `--slug`를 붙인 단독 커맨드)로 재시작하면 중단된 단계부터 자동으로 이어집니다.
