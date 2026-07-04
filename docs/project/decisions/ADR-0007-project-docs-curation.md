<!-- css:updated: 079b623 2026-07-04 -->

# ADR-0007: docs/project/ 살아있는 문서 큐레이션

- **상태**: accepted
- **날짜**: 2026-07-03
- **출처**: `docs/superpowers/specs/2026-07-03-project-wiki-design.md:30-37` (결정 사항, 브레인스토밍 승인)

## 배경 (Context)

파이프라인 문서는 전부 사건 기록(event log) 축으로만 쌓였다 — GitHub 이슈+스테이지 코멘트(slug별 시간순), ADR(이슈 댓글에만 존재, 발견성 최악), `docs/<slug>/README.md`(머지 시점 스냅샷, 이후 갱신 없음), spec/plan(착수 시점 문서). 기능 3개가 같은 대상을 순차 수정하면 현재 상태를 알기 위해 여러 이슈+스냅샷을 시간순으로 직접 병합해야 하는 문제가 있었다. 추가로 (1) 파이프라인을 거치지 않은 손 커밋도 반영되어야 하고 (2) 이미 진행 중인 기존 프로젝트에도 도입 가능해야 한다는 요구가 있어, 파이프라인 스테이지가 아닌 독립 커맨드가 필요했다.

## 결정 (Decision)

- 문서 정본 위치는 **in-repo `docs/project/`**, GitHub Wiki는 읽기 전용 미러(D1) — 에이전트가 worktree에서 문서를 컨텍스트로 재사용하는 선순환, 문서 변경이 PR diff에 실림, private+Free 요금제의 Wiki 불가/미초기화 제약 회피.
- 변경 반영 방식은 페이지별 diff 요약 → 터미널 승인 → **현재 브랜치에 직접 커밋**(`git add docs/project/`로 스코프)(D2) — 항상-PR은 실행 빈도를 떨어뜨리고, 무확인 자동 커밋은 정본 오염 위험이 있어 기각.
- 구현 형태는 **신규 커맨드(`/css:wiki`) + 전담 에이전트(`css-doc-curator`)**(D3) — `/css:document` 확장은 verify PASS 세션 게이팅 우회 분기를 낳고, 스테이지별 dual-write는 비파이프라인 수정을 못 덮음.
- 커맨드 이름은 **`/css:wiki`**(D4) — 사용자 멘탈모델과 일치, Wiki 미러가 스킵되어도 산출물 장르("프로젝트 위키")를 지칭.

## 결과 (Consequences)

- `docs/project/`가 이 저장소의 **현재 상태 뷰**로서 처음 생성되었다(이 문서 트리 자체가 그 결과물).
- 동기화 기준점이 `README.md` 푸터의 `css:last-synced` 마커 하나로 단순화되어 별도 상태 파일 없이 clone/fork에도 그대로 유지된다.
- 페이지 유형 계약(living/index/append-only)이 확립되어, 손 편집을 보존하면서도 회귀 없이 병합할 수 있게 되었다.
- 트레이드오프: 승인 게이트가 있어 완전 자동화는 아니며, 사람이 페이지별 요약을 검토해야 커밋된다 — 빈도와 정확성의 균형점으로 의도된 설계다.
- 이 기능은 [ADR-0005](ADR-0005-github-issues-projects-tracking.md)가 확립한 "GitHub 불가 시 경고 후 스킵" graceful degradation 철학을 Wiki 미러 단계에 그대로 재사용한다.
