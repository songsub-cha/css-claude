---
description: <project>/docs/<slug>/ 마크다운 문서 생성 (CSS 파이프라인 6단계)
argument-hint: "[--session <name>]"
---

# /css:document

검증된 구현 증거로부터 사용자 대상 문서를 생성한다.

## 단계

1. `--session` 을 해석한다; `session.phases.verify.verdict == "PASS"` 를 요구한다; document 락을 획득한다(`locks/{slug}-document.lock`; 60분 경과 시 stale → 안내와 함께 교체; 다른 실행의 신선한 락 → 안내와 함께 중단); `_active.json`(`latest_slug`, `active_epic`, `active_phase`)을 갱신한다.
2. `session.phases.interview.artifact` 또는 `parent_session.phases.interview.artifact` 에서 spec 을 해석한다.
3. docs 경로를 선택한다:
   - Phase: `docs/{parent_slug}/p{phase_index}/README.md`
   - Single-session: `docs/{slug}/README.md`
4. worktree, 해석된 spec, plan, verify 리포트, docs 경로와 함께 `css-documenter` 를 디스패치한다. Overview, Quick Start, Usage Examples, Architecture, Testing, Future Work 를 요구한다. 예시는 검증된 테스트를 인용해야 한다.
5. worktree 에서 docs 를 커밋하고, `phases.document.artifact` 를 기록하고, 락을 해제한다.

<self_check>
- [ ] 해석된 docs 경로가 존재함
- [ ] worktree 에 문서 커밋이 존재함
</self_check>

$ARGUMENTS
