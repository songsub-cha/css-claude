> [English](RUNTIME.md) · **한국어**

# CSS Codex 런타임 - 실행 모델 & 도구 매핑

설치된 모든 CSS skill(`~/.agents/skills/css-*/SKILL.md`)은 이 파일을 가리키는
포인터로 시작합니다. 행동하기 전에 먼저 읽으세요. CSS 커맨드와 에이전트 본문은
Claude Code에서 그대로 복사된 것이라 Claude 도구 이름을 참조하는데, 이 파일이
각각을 Codex 동작으로 매핑합니다. 사용자 지시와 skill 본문은 항상 여기의 예시보다
우선합니다.

## Skill 호출 인자

복사된 Claude 커맨드 본문은 `$ARGUMENTS`를 참조할 수 있습니다. Codex에서는
`$ARGUMENTS`를 skill 호출 시 함께 전달된 텍스트로 해석하세요:

- `$css-ship "small idea"`는 `$ARGUMENTS`가 `"small idea"`임을 뜻합니다.
- App이나 CLI의 skill 메뉴에서 `css-ship`을 선택한 뒤 후속 텍스트를 입력하면,
  그 후속 텍스트가 `$ARGUMENTS`가 됩니다.
- 사용자 요청에 의해 skill이 암묵적으로 트리거됐다면, 사용자의 요청 텍스트를
  `$ARGUMENTS`로 사용하세요.
- 전달된 텍스트가 없으면 `$ARGUMENTS`를 비어 있는 것으로 간주하고, 커맨드 본문이
  그 흐름을 지원하는 경우에만 진행하세요.

Codex 환경(surface)은 서로 다를 수 있습니다. `$css-*` 또는 App/CLI skill 메뉴를
통한 명시적 skill 호출을 우선하세요. 메뉴를 노출하지 않는 환경이라도 사용자는
skill mention을 직접 입력할 수 있습니다. 레거시 커맨드 산출물(artifact)을
사용하거나 그에 의존하지 마세요.

## 도구 매핑

| 본문이 호출하는 것 | Codex에서 할 일 |
|---|---|
| `Task(subagent_type=X, prompt=P)` | `~/.codex/css/agents/index.json`으로 `X`를 에이전트 파일로 해석합니다. `spawn_agent`를 쓸 수 있으면 그 파일 내용과 `P`를 프롬프트로 하여 `spawn_agent`를 호출하세요. 없으면 그 파일의 지시를 현재 스레드에서 순서대로 인라인 수행하세요. |
| 병렬 실행을 의도한 여러 개의 `Task(...)` 호출 | 작업마다 `spawn_agent`를 하나씩, 그다음 각각 `wait_agent`, 마지막으로 `close_agent`로 슬롯을 반환합니다. `spawn_agent`가 없으면 순차 실행하세요. |
| `TodoWrite` | `update_plan` |
| `AskUserQuestion(question, options=[...])` | 질문과 선택지를 번호 매긴 평문 목록으로 출력하고, 멈춰서 사용자의 입력 응답을 기다립니다. 응답을 선택지에 다시 매핑하세요. |
| `Read` / `Write` / `Edit` / `Bash` | 네이티브 파일·셸 도구 |

## 기능 탐지(Capability Detection)

`spawn_agent`가 도구 목록에 있으면 격리된 서브에이전트로 병렬 경로를 사용하세요.
없으면 현재 스레드에서 인라인으로 순차 경로를 사용하세요. 두 경로 모두 같은
산출물을 같은 위치에 생성합니다. 병렬 경로를 활성화하려면 `~/.codex/config.toml`에
다음을 추가하세요:

```toml
[features]
multi_agent = true
```

## 에이전트 해석(Agent Resolution)

`css-reviewer` 같은 `subagent_type` 값은 `~/.codex/css/agents/index.json`을 통해
파일로 매핑됩니다(`{ "css-reviewer": "agents/reviewer.md", ... }`). 파일의 텍스트를
로드해 해당 전문가의 프롬프트 또는 지시로 사용하세요. 에이전트 파일에는
frontmatter가 없고 본문 텍스트만 있습니다.

## 모델

Codex는 단일 세션 모델로 동작합니다. Claude의 에이전트별 `model:` 계층
(opus/sonnet/haiku)은 여기 존재하지 않으며 재현되지 않습니다 — 그 frontmatter 키는
설치 시점에 제거됩니다. 작업별 모델 전환이 없으므로 모델 기반 비용 계층화도
없습니다.

## Worktree / Finish 환경 탐지

worktree를 만들거나(`/css-execute`) push/PR(`/css-pr`)하기 전에, 읽기 전용 git으로
환경을 탐지하세요:

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
BRANCH=$(git branch --show-current)
```

- `GIT_DIR != GIT_COMMON`: 이미 연결된(linked) worktree 안에 있음 — worktree
  생성을 건너뜁니다.
- `BRANCH`가 비어 있음: detached HEAD 또는 샌드박스 — 브랜치·push·PR 생성이
  불가하므로 handoff를 사용하세요.

## PR / Finish

`gh`가 있고 인증돼 있으며 네트워크가 가능하면, 본문 지시대로 PR을 생성하세요.
그렇지 않으면 제안 브랜치명, 커밋 메시지, PR 본문을 담은 handoff 페이로드를 내보내
사용자가 자신의 호스트 UI나 로컬 체크아웃에서 적용하도록 하세요.

## 상태(State)

CSS 세션 상태는 `<project>/.claude/css/`에 있으며 Claude Code와 공유됩니다. 어느
도구에서 시작한 세션이든 다른 도구에서 이어갈 수 있도록 그곳에서 읽고 쓰세요.
위치를 옮기지 마세요.
