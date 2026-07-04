---
description: docs/project/ living docs(feature SoT, 아키텍처, 스키마, 운영, ADR)를 큐레이션하고 GitHub Wiki 에 미러링
argument-hint: "[--init] [--no-publish]"
---

# /css:wiki

`docs/project/` 를 이 저장소의 **현재-상태(current-state)** 문서로 유지한다 — slug 별
스냅샷과 이슈 스레드가 결코 주지 않는 투영(projection)이다 — 그리고 선택적으로 GitHub Wiki 에
미러링한다. 세션 독립적: 변경사항이 CSS 파이프라인을 거쳤든 아니든 어떤 git 저장소에서도
작동한다. 세션 JSON 을 읽지만 절대 쓰지 않으며 `_active.json` 을 절대 건드리지 않는다.

## 단계

1. `--init`(전체 재구축 강제) 과 `--no-publish`(Wiki 미러링 생략) 를 파싱한다. 사전 점검:
   최소 커밋 하나가 있는 git 저장소를 요구한다. non-default 브랜치이거나 트리가 dirty 면
   경고하고 계속한다 — docs 커밋은 `docs/project/` 로 범위가 한정되므로 무관한 변경이
   섞여 들어가는 일은 절대 없다.
2. 락 `locks/_project-wiki.lock` 을 획득한다(60분 경과 시 stale → 안내와 함께 교체; 다른
   실행의 신선한 락 → 안내와 함께 중단). 취소와 오류를 포함한 모든 종료 경로에서 해제한다.
3. 동기화 기준점을 해석한다: `docs/project/README.md` 에서 `<!-- css:last-synced: <sha> ... -->`
   마커를 읽는다. 마커나 파일이 없거나, `--init` 이 주어지면 → **bootstrap** 모드; 그 외에는
   그 SHA 로부터 **incremental**. `head_sha = git rev-parse HEAD`(메시지용 short form)를
   기록한다 — 큐레이터가 이를 손댄 모든 페이지에 스탬프한다.
4. 입력 번들을 수집한다. GHS 헬퍼를 먼저 정의하고 이를 사용하는 모든 Bash 호출에서 다시
   정의한다(셸 상태는 유지되지 않는다):
   `CSS_PLUGIN_DIR="${CLAUDE_PLUGIN_ROOT}"; CSS_PLUGIN_DIR="${CSS_PLUGIN_DIR:-$HOME/.claude/css}"; GHS() { bash "${CSS_LIB:-$CSS_PLUGIN_DIR/lib}/gh_sync.sh" "$@"; }`
   설치 디렉터리를 `CSS_ROOT` 로 절대 export 하지 않는다(gh_sync.sh 는 `CSS_ROOT` 를 프로젝트
   루트로 읽는다). `GHS` 는 항상 프로젝트 루트에서 실행한다.
   - Incremental: `git diff --name-status <last_sha>..HEAD`, `git log --oneline <last_sha>..HEAD`,
     그리고 그 범위에서 손댄 `docs/<slug>/` 폴더.
   - Bootstrap: 전체 트리 목록(.gitignore 준수), 모든 `docs/<slug>/` 폴더, ADR 백필 —
     `_active.json` 을 제외한 각 `<project>/.claude/css/sessions/*.json` 에 대해
     `GHS adr-list --session <slug>` 를 실행하고 본문을 수집한다(gh 사용 불가 시 세션 JSON 의
     `github.adrs[]` 제목으로 폴백).
   - 두 모드 공통: 범위 내 스키마 관련 파일(migrations/, `*.sql`, 모델/엔티티 파일).
   - 지나치게 큰 incremental diff(변경 파일 약 200개 초과): 부분적인 뷰를 먹이지 않는다 —
     `/css:wiki --init` 을 권장하고, 락을 해제하고, 깔끔하게 중단한다.
5. mode, head_sha, 위의 하베스트, docs 루트 `docs/project/` 와 함께 `css-doc-curator` 를
   디스패치한다. 큐레이터는 페이지를 제자리에서 편집하고, living 페이지의 손 편집을
   보존하며, 페이지별 변경 요약을 반환한다. 절대 커밋하지 않는다.
6. 승인 게이트 — 페이지별 요약과 `git diff --stat docs/project/` 를 보여준 뒤,
   AskUserQuestion: [승인 / 페이지 제외 / 취소].
   - 페이지 제외 → 제외된 경로를 되돌리고(`git checkout -- <path>`; 새로 생성된 파일은
     삭제), 남은 요약을 다시 보여주고, 다시 묻는다.
   - 취소 → `docs/project/` 의 모든 변경을 되돌리고, 락을 해제하고, 0으로 종료한다.
7. docs 범위만 정확히 커밋한다: `git add docs/project/` 다음
   `git commit -m "docs(project): sync @ <short-sha>"`.
8. Wiki 미러링(`--no-publish` 시 생략): `GHS wiki-publish --sha <short-sha>`. gh 가
   인증되지 않았거나, 저장소에 원격이 없거나, Wiki 가 비활성(Free 플랜의 private 저장소)이거나,
   wiki 저장소가 미초기화 상태면 헬퍼가 경고 한 줄과 함께 스스로 스킵한다 — 커맨드는
   여전히 성공한다.
9. 보고: 변경된 페이지, 커밋 해시, Wiki 가 발행되었는지 여부, 그리고 Home 푸터에 지금
   기록된 새 baseline SHA.

<self_check>
- [ ] Baseline came from the Home footer marker (or bootstrap/--init) — no state files used
- [ ] Curator wrote only under docs/project/; no session JSON or _active.json was modified
- [ ] Gate shown; excluded pages actually reverted before the commit
- [ ] Commit contains docs/project/ paths only
- [ ] wiki-publish skipped gracefully when unavailable; lock released on every exit path
</self_check>

$ARGUMENTS
