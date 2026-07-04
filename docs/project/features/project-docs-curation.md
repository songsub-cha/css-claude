<!-- css:updated: 079b623 2026-07-04 -->

# 프로젝트 문서 큐레이션 (/css:wiki)

## 1. 현재 동작

slug별 세션/이슈 기록은 "그때 무슨 일이 있었는지"만 답한다. `docs/project/`는 이와 독립적으로 기능 SoT·아키텍처·데이터 스키마·운영·ADR을 **현재 상태**로 유지하는 living docs이며, `/css:wiki`가 갱신하고 원하면 GitHub Wiki에 읽기 전용으로 미러링한다 (`commands/wiki.md:8-12`). 세션과 무관하게 아무 때나 실행 가능하고, CSS 파이프라인을 거치지 않은 손 커밋이나 기존(비-CSS) 프로젝트도 git diff 기반으로 반영된다 (`docs/usage.md:85-100`).

이 페이지 자체가 이 기능의 최초 산출물입니다 — 지금 보고 있는 `docs/project/` 전체가 `/css:wiki --init`(bootstrap 모드)의 첫 실행 결과입니다.

## 2. 인터페이스

```
/css:wiki                # docs/project/ 부재 → bootstrap, 존재 → 증분
/css:wiki --init         # 전체 재생성 강제
/css:wiki --no-publish   # in-repo 커밋까지만 (Wiki 미러 생략)
```
(`commands/wiki.md:3`, `docs/usage.md:92-95`)

동작 흐름(6단계)은 [architecture.md 3.3](../architecture.md#33-csswiki-증분-동기화)의 시퀀스 다이어그램을 참조하세요. 승인 게이트 선택지는 [승인 / 페이지 제외 / 취소]이며, "페이지 제외"는 해당 파일 변경만 되돌리고 나머지로 재확인합니다 (`commands/wiki.md:44-48`).

## 3. 내부 설계 요점

- **동기화 기준점이 문서 안에 있다**: 별도 상태 파일 없이 `docs/project/README.md` 푸터의 `<!-- css:last-synced: <sha> ... -->` 마커만으로 증분/부트스트랩을 판정 — clone·fork해도 그대로 유지된다 (D1 계열, `commands/wiki.md:23-26`, `docs/superpowers/specs/2026-07-03-project-wiki-design.md:34`).
- **정본은 in-repo, Wiki는 읽기전용 미러**(D1): 에이전트가 worktree에서 문서를 컨텍스트로 재사용하는 선순환을 만들고, 문서 변경이 PR diff에 실리며, private+Free 요금제의 Wiki 불가 제약을 회피한다 (`docs/superpowers/specs/2026-07-03-project-wiki-design.md:34`).
- **스코프 커밋**(D2): `git add docs/project/`로 한정된 커밋만 만들어 dirty 워킹트리와 섞이지 않는다 (`commands/wiki.md:49-50`).
- **오버사이즈 증분 방어**: 200개 초과 변경 파일이면 부분 뷰를 넘기지 않고 `--init`을 권고하며 중단한다 (`commands/wiki.md:39-40`).
- **페이지 유형 계약**: living(제자리 병합, 손 편집 보존) / index(행 추가·수정) / append-only(파일 추가+`superseded` 표기만) — `agents/doc-curator.md`의 `Page_Contracts`가 11종 페이지 각각에 이 계약을 부여한다.
- **영역=capability, slug 아님**: 기능 페이지 단위는 파이프라인 slug가 아니라 영역이며, `features/README.md` 인덱스 표가 영역↔slug 매핑의 정본이다 (`docs/superpowers/specs/2026-07-03-project-wiki-design.md:104`).

## 4. 데이터

이 영역 자체는 `docs/project/` 트리 외의 영속 데이터를 소유하지 않는다. 입력으로 세션 JSON(ADR 백필), `docs/<slug>/`, git diff/log를 **읽기만** 하고 `_active.json`은 절대 갱신하지 않는다 (`commands/wiki.md:11-12`, `docs/session-schema.md:23-24`).

## 5. 제약·알려진 한계

- Wiki 미러는 `gh` 미인증, 리모트 없음, Wiki 비활성(private+Free), 미초기화 wiki 중 하나라도 해당하면 경고 한 줄과 함께 스킵되고 커맨드 자체는 성공 종료한다 (`commands/wiki.md:52-54`, `lib/gh_sync.sh:413-437`).
- 한 living 페이지가 ~300줄을 넘으면 curator는 분할을 제안만 하고 임의로 분할하지 않는다 (`docs/superpowers/specs/2026-07-03-project-wiki-design.md:106`).
- bootstrap 시점에 이 저장소의 세션 3개(`domain-expert-expansion`, `epic-phase-pipeline`, `pipeline-dashboard`) 모두 `GHS adr-list` 결과가 비어 있어 기록된 ADR이 없었다 — `decisions/`의 ADR은 대신 `docs/superpowers/specs/*-design.md`의 확정 결정을 소급 정리한 것이며, GitHub 이슈 ADR 코멘트 백필분이 아니다.

## 6. 변경 이력

| 날짜 | slug | 요약 | PR |
|---|---|---|---|
| 2026-07-03 | (설계, 미확인 slug) | `/css:wiki` + `css-doc-curator` 설계 승인 | 미확인 |
| 2026-07-04 | (bootstrap) | `docs/project/` 최초 생성 — 이 기능의 첫 실행 결과물 | — |
