# css-claude

**CSS — Claude Super System**: [Claude Code](https://claude.com/claude-code)를 위한 개인용 글로벌 소프트웨어 개발 자동화 파이프라인.

상태: **v0.1.0**. 개인 사용 파이프라인. 설치 방법은 [`docs/installation.md`](docs/installation.md)를 참고하세요.

## 개요

`/css:` 네임스페이스 아래 8개의 슬래시 커맨드로 구성되어 있으며, 아이디어에서 PR 머지까지 7단계를 거쳐 진행됩니다. 3개의 승인 게이트와 함께 전체 파이프라인을 실행하는 마스터 커맨드도 포함되어 있습니다.

```
/css:interview  →  /css:plan  →  /css:review  →  /css:execute  →  /css:verify  →  /css:document  →  /css:pr
                                                                                                        ↑
                                                /css:ship  ──── 3개 게이트로 전체 실행 ────────────────┘
```

## 빠른 시작

설치 후:

```
/css:ship "<아이디어>"
```

전체 커맨드 레퍼런스는 [`docs/usage.md`](docs/usage.md)를 참고하세요.

## 주요 기능

- **아이디어 → PR 자동화**: 중요한 결정 시점에 명시적인 사람의 승인 게이트 포함
- **TDD 강제 적용**: execute 단계에서 테스트 커버리지 ≥85% 요구
- **18개 전문 서브 에이전트**: 계획 검토, 코드 품질 리뷰, API, DB, UI (웹 + Android), 인프라, 보안, 테스트, 디버깅, 리팩토링, 비동기, LLM 앱, 프롬프트 엔지니어링 담당
- **언어 자동 감지**: JS/TS, Python, Go, Rust, Java (Maven), Java/Kotlin (Gradle, Android Jetpack Compose 포함)
- **상태 저장 및 재개 가능**: `<project>/.claude/css/sessions/{slug}.json`으로 관리
- **멀티 세션 동시 실행**: 같은 프로젝트에서 터미널 A는 기능 A, 터미널 B는 기능 B를 동시에 진행 가능 — 슬러그 단위로 세션 격리
- **자동 루프백 횟수 제한**: 한도 초과 시 사용자에게 에스컬레이션
- **OMC 독립**: Claude Code의 `superpowers` 플러그인과 `gh` CLI만 필요

## 설계 문서

전체 설계는 [`docs/specs/2026-05-27-css-pipeline-design.md`](docs/specs/2026-05-27-css-pipeline-design.md)를 참고하세요.

## 사전 조건

- Claude Code
- `superpowers` 플러그인 활성화
- `gh` CLI 인증 완료
- `git` ≥ 2.5

## 설치

플랫폼 스크립트로 설치:

- Windows: `scripts/install.ps1`
- Ubuntu 22.04: `scripts/install.sh`

자세한 내용은 설계 문서의 § Installation Scripts 항목을 참고하세요.

## 디렉토리 구조

```
css-claude/
├── README.md
├── commands/      # → ~/.claude/commands/css/
├── agents/        # → ~/.claude/agents/css/
├── config/        # 기본 설정
├── scripts/       # 설치 / 제거 스크립트 (Windows + Ubuntu)
├── docs/          # 설계 문서, 사용법, 트러블슈팅
└── tests/         # 에이전트 골든 테스트 + 토이 픽스처
```

## 라이선스

개인 사용 목적. 현 단계에서는 재배포 불가.
