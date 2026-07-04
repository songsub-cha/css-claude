---
description: PR 머지 후 세션 worktree 와 머지된 브랜치를 제거 (CSS 파이프라인 하우스키핑)
argument-hint: "[--session <name>] [--keep-branch] [--force]"
---

# /css:clean

PR 이 머지된 후 세션의 격리 worktree(그리고 선택적으로 로컬 브랜치)를 정리한다. 기본적으로 안전함: 명시적 확인 없이는 dirty, unpushed, unmerged 작업을 절대 삭제하지 않는다.

## 단계

1. `--session`(기본값 `_active.json.latest_slug`), `--keep-branch`, `--force` 를 파싱한다. 세션을 해석한다. `child_slugs` 를 가진 `kind:"epic"` 세션의 경우, 완료된 각 자식 세션에 대해 같은 절차를 실행할지 제안한다.
2. clean 락을 획득한다(`locks/{slug}-clean.lock`; 60분 경과 시 stale → 안내와 함께 교체; 다른 실행의 신선한 락 → 안내와 함께 중단).
3. `phases.execute.worktree` 와 `phases.execute.branch` 를 읽는다. 둘 다 없으면(또는 worktree 디렉터리가 이미 사라졌으면), "정리할 worktree가 없습니다" 를 보고하고, `phases.clean` 을 기록하고, 락을 해제하고, 종료한다.
4. 안전 점검 — 실패한 점검마다 진행 전에 명시적 AskUserQuestion 확인이 필요하다(`--force` 는 질문을 건너뛰지 않는다; 버려질 모든 것을 하나의 확인으로 미리 요약할 뿐이다):
   - **Dirty**: `git -C <worktree> status --porcelain` 가 비어 있어야 한다.
   - **Merged**: `phases.pr.artifact` 가 PR URL 이고 `gh` 를 사용할 수 있으면, `gh pr view <url> --json state` 가 `MERGED` 를 보고해야 한다; OPEN/CLOSED(또는 PR 이 없을 때)는 진행 전에 확인을 요청한다.
   - **Unpushed**: `git -C <worktree> log origin/<branch>..<branch> --oneline` 가 비어 있어야 한다; 한 번도 push 되지 않은 브랜치도 확인이 필요하다.
5. 제거: `git worktree remove <worktree>`(일반; 위 확인 이후에만 `--force` 추가), 그다음 `git worktree prune`. `--keep-branch` 가 아니면 `git branch -d <branch>` 로 로컬 브랜치를 삭제한다(`-D` 는 확인 후에만). 원격 브랜치는 절대 건드리지 않는다 — GitHub 의 "delete branch on merge" 또는 사용자가 그것을 소유한다.
6. 세션 갱신: `phases.clean = {status: "completed", removed_worktree: <bool>, removed_branch: <bool>, completed_at: <ISO>}`. 락을 해제하고 정확히 무엇이 제거되었는지 출력한다.

<self_check>
- [ ] 명시적 확인 없이 dirty, unpushed, unmerged 작업이 삭제되지 않음
- [ ] Worktree 가 제거되고 prune 됨(또는 없음이 보고됨)
- [ ] 브랜치 처리가 --keep-branch 와 확인 사항에 부합함
- [ ] phases.clean 기록됨; 락 해제됨
</self_check>

$ARGUMENTS
