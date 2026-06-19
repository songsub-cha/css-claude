---
description: plan 배치(batch)들을 의존성 순서의 Phase 로 묶고 자식 Phase 세션을 생성 (CSS 파이프라인 2.5단계)
argument-hint: "[--slug <name>]"
---

# /css:phase

Epic 의 Phase 분해(decomposition)를 결정한다. `/css:plan` 과 `/css:review` 사이에서 실행된다.

## 단계

1. **인자 파싱**: `--slug` (Epic 슬러그). 기본값은 `_active.json.latest_slug`.

2. **세션 해석**; `phases.plan.status == completed` 를 요구한다. `task_count` 와 `batch_count` 를 읽는다.

3. **임계치 게이트** (`tools/css_schema/derive.py:should_phase` 사용):
   - `should_phase(task_count, batch_count)` 가 **false** 이면 → 단일 Phase 매니페스트
     `[{"idx":1,"label":"<idea>","batches":[1..batch_count],"depends_on":[]}]` 를 작성하고,
     `kind:"epic"` 을 최소한으로 표시하며, `child_slugs:[]` 로 설정한다(레거시 단일 세션 경로). 그리고
     "단일 세션 경로 (임계치 미만)" 을 안내한다. 7단계로 건너뛴다.
   - 그렇지 않으면 계속 진행한다.

4. **`phase_manifest` 제안**: 배치들을 `depends_on` 엣지를 가진 2~5개의 Phase 로 묶는다
   (수직 슬라이스는 순서대로, 독립 슬라이스는 `depends_on:[]`). 제안한
   매니페스트를 AskUserQuestion 으로 사용자에게 제시한다: "[승인 / 수정 / 취소]". 수정 선택 시 편집 내용을 받아 다시 제시한다.

5. 승인된 매니페스트를 `python -c "import json,sys; from css_schema.schema import validate_manifest; validate_manifest(json.load(open(sys.argv[1])))" <manifest.json>` 로 **검증**한다(`tools/` 에서 실행). SchemaError 발생 시 중단한다.

6. **영속화(Persist)**:
   - `.claude/css/plans/phase-manifest-{slug}.json` 을 작성한다.
   - Epic 세션 갱신: `kind:"epic"`, `phases.phasing = {status: completed, artifact: <manifest path>}`,
     `phase_manifest = <manifest>`, `child_slugs = [phase_slug(slug, idx) for each]`.
   - 각 Phase 마다 자식 세션 `sessions/{phase_slug}.json` 을 생성하되
     `kind:"phase"`, `parent_slug`, `phase_index`, `phase_label`, `depends_on`,
     `base_branch = base_branch_for(manifest, idx, slug)`, 그리고 비어 있는 execute/verify/document/pr 스테이지를 포함한다.

7. **락 이름 규칙**: 형제(sibling) Phase 끼리 충돌하지 않도록 `locks/{child_slug}-phasing.lock` 을 사용한다. `_active.json` 을 작성하는 곳에서는 `active_epic`(`parent_slug` 또는 자신)과 `active_phase`(`phase_index` 또는 null)도 함께 설정한다.

8. **락 해제** 후 안내: "Phasing 완료: {N} Phases. 다음 단계: `/css:review --slug {slug}`. NEXT=review".

<self_check>
- [ ] phase-manifest-{slug}.json exists and passes validate_manifest
- [ ] Epic session has phase_manifest + child_slugs
- [ ] One child session file per Phase, each passing validate_session
- [ ] Final line contains NEXT=review
</self_check>

$ARGUMENTS
