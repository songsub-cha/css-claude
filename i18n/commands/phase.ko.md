---
description: plan 배치(batch)들을 의존성 순서의 Phase 로 묶고 자식 Phase 세션을 생성 (CSS 파이프라인 2.5단계)
argument-hint: "[--session <name>] [--slug <legacy-name>]"
---

# /css:phase

Epic 이 하나의 세션으로 남을지 의존성 순서의 자식 Phase 세션들이 될지 결정한다.

## 단계

1. `--session` 을 파싱한다; `--slug` 는 레거시 별칭으로 수용한다. 기본값은 `_active.json.latest_slug`.
2. Epic 세션을 해석하고 `phases.plan.status == completed` 를 요구한다. `task_count` 와 `batch_count` 를 읽는다.
3. 자체 완결적 임계치를 적용한다: `task_count > 20` 또는 `batch_count > 4` 이면 multi-Phase.
4. 임계치 미만이면:
   - `[{"idx":1,"label":"<idea>","batches":[1..batch_count],"depends_on":[]}]` 를 영속화한다.
   - `kind:"epic"`, `single_phase:true`, `child_slugs:[]` 를 설정하고 `phases.phasing` 을 완료 처리한다.
   - `/css:plan --session <slug>` 를 다시 호출한다. 스켈레톤을 상세 단일 세션 plan 으로 반드시 교체해야 한다.
   - `/css:review --session <slug>` 로 계속한다.
5. multi-Phase 이면, 수직 슬라이스 매니페스트를 제안하고 사용자에게 승인 또는 수정을 요청한다.
6. 저장소 로컬 헬퍼 의존성 없이 매니페스트를 검증한다. 비어 있지 않은 목록; 고유하게 증가하는 정수 `idx >= 1`; 비어 있지 않은 `label`; 비어 있지 않은 `batches`; 그리고 이미 선언된 더 작은 인덱스를 참조하는 `depends_on` 항목을 요구한다.
7. `.claude/css/plans/phase-manifest-{slug}.json` 을 영속화한다; `kind:"epic"`, `single_phase:false`, `phase_manifest`, `child_slugs` 를 설정한다.
8. 각 자식 세션을 `kind:"phase"`, `parent_slug`, `parent_session`, `phase_index`, `phase_label`, `depends_on`, `base_branch` 와 함께 생성한다.
   자식 슬러그는 `{slug}-p{idx}`, 브랜치는 `css/{slug}/p{idx}`. 독립 Phase 는 base_branch 가 Epic 이 캡처한 base/현재 브랜치; 의존 Phase 는 base_branch 가 선언된 의존성 중 가장 큰 인덱스의 브랜치.
   부모로부터 불변 다운스트림 컨텍스트를 복사한다: `idea`, `repo_root`, `repo_name`, `master_flow`, `config`, `language_profile`, 그리고 산출물을 포함한 `phases.interview`. plan/review/execute/verify/document/pr 스테이지, 재시도 카운터(`retries = {review: 0, verify: 0}`), 독립적인 Gate 2/Gate 3 상태를 초기화한다.
9. 자식 명령은 이전 CSS 버전이 만든 자식 세션과의 호환을 위해 `parent_session` 에서 누락된 컨텍스트를 해석한다.
10. `locks/{slug}-phasing.lock` 을 사용한다(Epic 슬러그 — phasing 은 자식이 생기기 전 Epic 하나에 대해 한 번만 실행되므로 자식 슬러그로 키를 잡으면 single-Phase 경로에서 미정의가 된다; 60분 경과 시 stale → 안내와 함께 교체; 다른 실행의 신선한 락 → 안내와 함께 중단); `_active.json.active_epic` 과 `active_phase` 를 갱신한다; 모든 종료 경로에서 락을 해제한다. 마지막 줄(단독 줄, 정확한 접두사): `NEXT=review`.

<self_check>
- [ ] Manifest satisfies the inline validation rules
- [ ] Single-Phase Epic has `single_phase:true` and a detailed plan
- [ ] Every child can resolve the parent spec artifact
- [ ] Final line contains `NEXT=review`
</self_check>

$ARGUMENTS
