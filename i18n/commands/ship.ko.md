---
description: 마스터 파이프라인 — interview → plan → review → execute → verify → document → pr 를 세 개의 승인 게이트와 함께 실행
argument-hint: "[--session <name>] <idea>"
---

# /css:ship

전체 CSS 파이프라인을 실행한다. 세 개의 승인 게이트: Gate 1 은 암묵적(brainstorming 자체의 사용자 리뷰 단계); Gate 2(execute 직전)와 Gate 3(pr 직전)은 AskUserQuestion 을 사용한다.

## 단계

1. **인자 파싱**: `--session` 이 있으면 추출하고, 나머지는 아이디어다.

2. **세션 해석 또는 초기화**:
   - `--session` 제공 + 기존 `<project>/.claude/css/sessions/<slug>.json` 존재 → AskUserQuestion: "기존 세션 발견 (phase=`<current>`). 어떻게 진행할까요? [Resume / Restart / Cancel]".
   - `--session` 제공 + 파일 없음 → 초기화.
   - `--session` 없음 → 아이디어로부터 슬러그 도출(kebab-case, 필요 시 충돌 접미사), 세션 초기화, `_active.json` 갱신.
   - `session.master_flow = true` 로 설정.
   - **GitHub 추적 초기화**: `GHS() { bash "${CSS_LIB:-$HOME/.claude/css/lib}/gh_sync.sh" "$@"; }` 를 정의한다. `gh_on = ("$(GHS enabled --session <slug>)" == "1")` 로 설정한다. `gh_on` 이면 `GHS init-issue --session <slug>` 를 실행한다(멱등적 — 이슈를 생성하고 사용자 Projects 보드에 추가하거나, resume 시 저장된 이슈를 재사용).

3. **락 획득**.

### GitHub 스테이지 동기화 (`gh_on` 일 때)

아래의 모든 스테이지 호출을 감싼다(wrap):
- `/css:<stage>` 호출 **전**: `GHS set-state --session <slug> --state <stage>` (이슈 라벨 → `css:<stage>`, 보드 Status → 해당 컬럼).
- 완료 **후**: `GHS comment --session <slug> --stage <stage>`.
  - `interview` / `plan` / `document` → 헬퍼가 **전체** 산출물 문서(`session.phases.<stage>.artifact`)를 접을 수 있는(collapsible) 블록에 임베드한다(GitHub 댓글 한도를 초과하면 청크 분할).
  - 그 외 모든 스테이지 → `session.phases.<stage>` 로부터 만든 한 줄 요약.

이들은 `gh_on` 일 때만 실행되며, 그렇지 않으면 건너뛰고 파이프라인은 이전과 동일하게 동작한다.

4. **Stage 1 — interview**:
   - `/css:interview <idea>` 를 호출(또는 resume)하며 슬러그를 상속한다.
   - Gate 1 은 암묵적: brainstorming 자체의 "사용자가 spec 을 리뷰" 단계.
   - GitHub: 전에 `set-state --state interview`, 후에 `comment --stage interview`(전체 spec 문서) — "GitHub 스테이지 동기화" 참조. 아래 모든 스테이지에 동일한 래핑을 적용한다.

5. **Stage 2 — plan (skeleton)**:
   - `/css:plan --session <slug>` 호출.

5b. **Stage 2.5 — phasing**:
   - `/css:phase --session <slug>` 호출(승인된 매니페스트로부터 자식 Phase 세션 생성).
   - Epic 이 단일 Phase 로 남으면(임계치 미만), 6~12단계를 통해 레거시 선형 플로우와 정확히 동일하게 계속한다(세션 하나, PR 하나).
   - 다중 Phase 인 경우: Epic **아키텍처 리뷰**를 한 번 실행하고(`/css:review --session <epic>`, kind=epic → 거친 수준, rich-spec 없음), 13단계에서 자식별 루프를 실행한다.
   - `gh_on` 이고 다중 Phase 인 경우: 각 자식 Phase 마다 `GHS init-issue --session <child>`(자체 이슈 생성, 각 Phase 가 자신의 내용을 독립적으로 동기화) 후 `GHS link-child --epic <epic> --child <child> --index <phase_index> --label "<phase label>"`(Phase 이슈를 Epic 아래 네이티브 GitHub **서브이슈(sub-issue)**로 중첩 — 내장 중첩 리스트 + 진행률 바; 서브이슈 API 가 없는 구버전 GitHub 에서는 Epic 체크리스트 행으로 폴백).

6. **Stage 3 — review (loop)** *(단일 Phase / 레거시 경로)*:
   - `/css:review --session <slug>` 호출.
   - `LOOPBACK_TO_PLAN` 시, review 명령 자체가 최대 2회까지 plan 으로 되돌아간다.
   - `LOOPBACK_TO_INTERVIEW` 시, interview 재진입 전에 사용자에게 확인을 받는다.
   - `ESCALATE` 시, 중단하고 옵션을 노출한다.
   - `gh_on` 이고 review 가 주목할 만한 아키텍처 결정이나 사소하지 않은 판정 근거를 만들었다면 게시한다: `GHS adr --session <slug> --title "<short>" --context "<why>" --decision "<what>" --consequences "<tradeoffs>"`(중요한 결정만 게시; 헬퍼가 ADR-1, ADR-2, … 로 번호를 매기고 resume 시 중복을 제거).
   - *다중 Phase Epic: Epic 아키텍처 리뷰는 5b 단계에서 이미 실행됨. 13단계(Phase 별 루프)로 건너뛴다.*

7. **Gate 2 — execute 직전 (공통 경로)** *(단일 Phase / 레거시 경로)*:

   ```
   gate  = session.gates.gate2_pre_execute
   if gate and gate.state == "approved": proceed to step 8; return

   banner = "Plan 검증 완료. worktree 생성 후 execute 시작."
   if gh_on:
       GHS gate-open --session <slug> --gate 2          # @mention + css:awaiting-approval
       options = ["Yes (여기서 승인)", "원격(이슈)에서 답변 대기", "Cancel"]
   else:
       options = ["Yes", "Cancel"]
   answer = AskUserQuestion(banner, options)

   if answer startswith "Yes":
       decision = "approve"; source = "terminal_ask"
   elif answer startswith "원격":
       # inline poll — no servers; each call returns within ~9 min, re-poll until a human replies
       loop:
           reply = GHS gate-wait --session <slug> --gate 2 --timeout 540
           if reply is non-empty:
               interpret reply → decision in {approve, cancel}   # free-form/Korean OK
               if ambiguous: GHS comment ... "approve/cancel 중 무엇인가요?"; continue
               break
           else:
               inform user "이슈 #<n> 답변 대기 중 (9분째)"; continue
       source = "issue_reply"
   else:
       decision = "cancel"; source = "terminal_ask"

   if decision == "approve":
       session.gates.gate2_pre_execute = {state:"approved", source:source, reached_at: gate.reached_at or now(), approved_at: now(), approved_by: source}
       save_session()
       if gh_on: GHS gate-close --session <slug> --gate 2 --decision approve --source <source>
       proceed to step 8
   else:
       if gh_on: GHS gate-close --session <slug> --gate 2 --decision cancel --source <source>
       release_lock(); exit 0
   ```

8. **Stage 4 — execute** *(단일 Phase / 레거시 경로)*: `/css:execute --session <slug>` 호출. `master_flow` 플래그는 `/css:execute` 에게 Gate 2 를 다시 묻지 말라고 알린다(이 단계의 응답을 상속).

9. **Stage 5 — verify (loop)** *(단일 Phase / 레거시 경로)*:
   - `/css:verify --session <slug>` 호출.
   - `LOOPBACK_TO_EXECUTE` 시, verify 명령 자체가 최대 3회까지 execute 로 되돌아간다.
   - `ESCALATE` 시, 옵션과 함께 중단.

10. **Stage 6 — document** *(단일 Phase / 레거시 경로)*: `/css:document --session <slug>` 호출.

11. **Gate 3 — pr 직전 (공통 경로)** *(단일 Phase / 레거시 경로)*:

    ```
    gate = session.gates.gate3_pre_pr
    if gate and gate.state == "approved": proceed to step 12; return

    banner = "구현+문서 완료. 브랜치 'css/<slug>'를 push하고 PR 생성."
    if gh_on:
        GHS gate-open --session <slug> --gate 3          # @mention + css:awaiting-approval
        options = ["Yes (PR 생성)", "Draft PR", "원격(이슈)에서 답변 대기", "Cancel"]
    else:
        options = ["Yes (PR 생성)", "Draft PR", "Cancel"]
    answer = AskUserQuestion(banner, options)

    if answer startswith "Yes":        decision = "approve"; source = "terminal_ask"
    elif answer startswith "Draft":    decision = "draft";   source = "terminal_ask"
    elif answer startswith "원격":
        loop:
            reply = GHS gate-wait --session <slug> --gate 3 --timeout 540
            if reply is non-empty:
                interpret reply → decision in {approve, draft, cancel}
                if ambiguous: GHS comment ... "approve / draft / cancel 중?"; continue
                break
            else:
                inform user "이슈 #<n> 답변 대기 중 (9분째)"; continue
        source = "issue_reply"
    else: decision = "cancel"; source = "terminal_ask"

    if decision in {approve, draft}:
        session.gates.gate3_pre_pr = {state:"approved", source:source, reached_at: gate.reached_at or now(), approved_at: now(), approved_by: source, draft: (decision == "draft")}
        save_session()
        if gh_on: GHS gate-close --session <slug> --gate 3 --decision <decision> --source <source>
        proceed to step 12
    else:
        if gh_on: GHS gate-close --session <slug> --gate 3 --decision cancel --source <source>
        release_lock(); exit 0
    ```

12. **Stage 7 — pr** *(단일 Phase / 레거시 경로)*: `/css:pr --session <slug>` 호출(사용자가 선택했다면 `--draft` 포함). `master_flow` 플래그는 `/css:pr` 에게 Gate 3 를 다시 묻지 말라고 알린다.
    - `/css:pr` 가 PR URL 을 반환한 뒤, `gh_on` 이면: `GHS pr-link --session <slug> --url <PR URL>`(이슈 댓글 + 라벨 `css:pr` + 보드 `PR`; PR 본문 자체는 `Closes #<issue>` 를 포함 — `pr.md` / `pr-creator` 참조).

13. **Phase 별 plan→pr 스테이지** *(다중 Phase Epic)*:
   각 자식 슬러그에 대해 위상 순서(topological order)대로(`phase_index` 기준, `depends_on` 준수):
   a. `/css:plan --session <child>` (kind=phase → detailed) → `/css:review --session <child>` (kind=phase → 이 Phase 의 rich-spec).
   b. **Gate 2 (Phase 별)** — AskUserQuestion: "Phase {idx} '{label}' execute 시작. base=`{base_branch}`. [Yes / Show / Skip / Cancel]".
   c. `/css:execute --session <child>` → `/css:verify --session <child>` → `/css:document --session <child>`.
   d. **Gate 3 (Phase 별)** — AskUserQuestion: "Phase {idx} PR 생성 (base=`{base_branch}`). [Yes / Draft / Cancel]".
   e. `/css:pr --session <child> --base <base_branch>`.
   독립적인 Phase(서로소인 `depends_on`)는 병렬 실행을 위해 별도 세션으로 디스패치할 수 있다(MAY).

14. **마무리(Finalize)**: 모든 phase 를 completed 로 표시한다.
    - `gh_on` 이면 `GHS finalize --session <slug>`(라벨 `css:done` + 보드 `Done`) 를 실행한다.
    - 락을 해제하고 요약을 출력한다: "Pipeline 완료. PR: `<URL>`. 산출물: `<paths>`."

<self_check>
- [ ] All 7 phases recorded as completed in session
- [ ] Each gate prompt was shown when applicable
- [ ] PR URL captured
- [ ] Lock released
</self_check>

$ARGUMENTS
