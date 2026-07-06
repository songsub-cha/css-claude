---
description: 격리된 worktree 에서 엄격한 TDD 로 plan 구현, rich spec 기반 cache-first (CSS 파이프라인 4단계)
argument-hint: "[--session <name>] [--plan <plan-path>] [--resume]"
---

# /css:execute

격리된 worktree 안에서 엄격한 Red-Green-Refactor TDD 를 사용해 태스크 단위 Rich Spec 을 구현한다.

## 단계

1. `--session`, `--plan`, `--resume`, 선택적 `--phase` 를 파싱한다; 세션과 상세 plan 을 해석한다.
2. language profile 이 없으면 해석한다. 기존 프로젝트 스크립트를 보존한다:
   - `pyproject.toml`/`uv.lock`: Python, `uv run pytest`, `uv run pytest --cov`
   - `package.json`: Node/TypeScript, 기존 테스트·커버리지 스크립트
   - `pom.xml`: Maven, `./mvnw test` 또는 `mvn test`
   - `build.gradle[.kts]`: Gradle, `./gradlew test`
   - `go.mod`: Go, `go test ./...`, `go test -cover ./...`
   - 그 외에는 테스트와 커버리지 명령을 물어본 뒤 저장한다.
3. `session.phases.review.rich_specs` 에서 실행 가능한 Rich Spec 을 해석한다. 없을 때만 Phase `{parent_slug}-p{phase_index}-T*.md`, single-session `{slug}-T*.md`, 그다음 레거시 `*-spec-{slug}-*.md` 로 폴백한다.
4. 라우팅된 모든 태스크를 사전 점검(pre-flight)한다. `/css:review` 로부터 온, canonical 필드를 모두 갖춘 advisory 아닌 산출물 정확히 하나를 요구한다; `Phase: {phase_index or 1}` 을 요구한다.
5. `session.base_branch`(interview 에서 캡처; 폴백 `main`)로부터 잘라낸 격리 worktree 와 브랜치를 생성하거나 재개한다. Phase 경로/브랜치는 `../{repo}-css-{parent_slug}-p{phase_index}` 와 `css/{parent_slug}/p{phase_index}`; single-session 경로/브랜치는 `../{repo}-css-{slug}` 와 `css/{slug}`. worktree 부모 디렉터리는 설정되어 있으면 `session.config.execute.worktree_parent`, 아니면 `..`. 참고: 형제(`..`) worktree 는 프로젝트 디렉터리 밖에 위치하므로 Claude Code 가 그곳의 쓰기에 권한 승인을 요구할 수 있다 — worktree 경로를 사전 승인(추가 작업 디렉터리 / `--add-dir`)하거나, `worktree_parent` 를 `.worktrees` 로 설정해 worktree 를 저장소 안에 유지한다(`.worktrees/` 가 git-ignore 되었는지 확인). worktree, 브랜치, base_branch 를 세션에 기록한다. 해석된 worktree 밖의 모든 쓰기를 거부한다.
6. 마스터 플로우에 대해 Gate 2 를 강제한다 — `session.master_flow == true` 이면 `session.gates.gate2_pre_execute.state == "approved"` 를 요구한다; 아니면 중단한다: "Gate 2가 승인되지 않았습니다. `/css:ship --session <name>`으로 진행하세요."(단독 non-master 실행은 게이트가 필요 없다 — 사용자가 execute 를 직접 호출했다). execute 락을 획득하고(`locks/{slug}-execute.lock`; 60분 경과 시 stale → 안내와 함께 교체; 다른 실행의 신선한 락 → 안내와 함께 중단), `_active.json`(`latest_slug`, `active_epic`, `active_phase`)을 갱신하고, 정확한 `rich_specs` 목록과 함께 `css-executor` 를 디스패치한다. executor 는 서브에이전트이며 사용자에게 프롬프트를 띄울 수 없다; 마지막 줄은 전체 일치가 아니라 `VERDICT=` 접두사로 매칭한다(뒤에 `reason="..."` 가 붙을 수 있다); `VERDICT=PAUSE` 시 인용된 사유를 노출하고, 여기서 사용자에게 묻고, `--resume` 으로 재디스패치한다. 어떤 쓰기 전에도 worktree 로 `cd` 하고 검증하도록(`pwd` 가 일치해야 함; 불일치 시 ESCALATE) 지시하고, 모든 변경과 `git` 명령을 그 안에 유지하도록 하며, 절대 force-push, hard-reset, 추적 경로에 대한 `rm -rf`, `chmod 777` 을 하지 않도록 한다.
7. 각 태스크에 대해:
   - `RED scaffold` 를 적용하고, `RED command` 를 실행하며, 0 이 아닌 종료 코드를 요구한다.
   - `GREEN template` 을 적용하고, `GREEN command` 를 실행하며, 0 종료 코드를 요구한다.
   - 태스크별 명령이 없는 레거시 산출물에만 `language_profile.test_command` 를 사용한다.
   - 제한된 debugger(최대 `session.config.execute.tdd_self_heal_max` 회, 기본 2)를 사용한 뒤 전문가 폴백 사다리를 사용한다; 전문가는 worktree 안에만 쓰고 절대 테스트하거나 커밋하지 않는다.
   - 리팩터하고, 검증을 재실행하고, CSS-* trailer 만으로 태스크를 커밋한다(Claude/AI 귀속 없음).
8. 각 배치 후 전체 테스트와 커버리지를 실행한다; cache_miss_count 와 함께 실행 로그를 작성한다(캐시 미스 = Rich Spec 템플릿이 그대로 통하지 않아 폴백 전문가를 호출해야 했던 태스크); 최종 판정으로부터 세션 상태를 갱신하고 `phases.execute.commit_count` 와 `phases.execute.test_summary = {tests, passed, coverage_pct}` 를 기록한다(gh_sync stage-summary 코멘트가 이를 읽는다); 락을 해제한다.

<self_check>
- [ ] 정확히 기록된 Rich Spec 이 인덱싱되었고 advisory 는 제외됨
- [ ] 모든 태스크가 RED 와 GREEN 명령을 실행함
- [ ] Executor 가 쓰기 전에 worktree cwd(Step 0)를 검증함
- [ ] worktree 경로와 브랜치가 기록됨
- [ ] 메인 워킹 트리에 예기치 않은 변경이 없음
</self_check>

$ARGUMENTS
