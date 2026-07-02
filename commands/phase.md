---
description: Group plan batches into dependency-ordered Phases and create child Phase sessions (CSS pipeline stage 2.5)
argument-hint: "[--session <name>] [--slug <legacy-name>]"
---

# /css:phase

Decide whether an Epic stays in one session or becomes dependency-ordered child Phase sessions.

## Steps

1. Parse `--session`; accept `--slug` as a legacy alias. Default from `_active.json.latest_slug`.
2. Resolve the Epic session and require `phases.plan.status == completed`. Read `task_count` and `batch_count`.
3. Apply the self-contained threshold: multi-Phase when `task_count > 20` OR `batch_count > 4`.
4. If below threshold:
   - Persist `[{"idx":1,"label":"<idea>","batches":[1..batch_count],"depends_on":[]}]`.
   - Set `kind:"epic"`, `single_phase:true`, `child_slugs:[]`, and complete `phases.phasing`.
   - Invoke `/css:plan --session <slug>` again. It MUST replace the skeleton with a detailed single-session plan.
   - Continue to `/css:review --session <slug>`.
5. If multi-Phase, propose a vertical-slice manifest and ask the user to approve or edit it.
6. Validate the manifest without repo-local helper dependencies. Require a non-empty list; unique strictly increasing integer `idx >= 1`; non-empty `label`; non-empty `batches`; and `depends_on` entries that reference already-declared smaller indices.
7. Persist `.claude/css/plans/phase-manifest-{slug}.json`; set `kind:"epic"`, `single_phase:false`, `phase_manifest`, and `child_slugs`.
8. Create each child session with `kind:"phase"`, `parent_slug`, `parent_session`, `phase_index`, `phase_label`, `depends_on`, and `base_branch`.
   Child slug is `{slug}-p{idx}` and branch is `css/{slug}/p{idx}`. For an independent Phase, base_branch is the Epic's captured base/current branch; for a dependent Phase, base_branch is the branch of the greatest declared dependency index.
   Copy immutable downstream context from the parent: `idea`, `repo_root`, `repo_name`, `master_flow`, `config`, `language_profile`, and `phases.interview` including its artifact. Initialize plan/review/execute/verify/document/pr stages, retry counters (`retries = {review: 0, verify: 0}`), and independent Gate 2/Gate 3 state.
9. Child commands resolve missing context from `parent_session` for compatibility with child sessions created by older CSS versions.
10. Use `locks/{child_slug}-phasing.lock` (stale after 60 min → replace with a note; a fresh lock from another run → abort with guidance); update `_active.json.active_epic` and `active_phase`; release locks on every exit path.

<self_check>
- [ ] Manifest satisfies the inline validation rules
- [ ] Single-Phase Epic has `single_phase:true` and a detailed plan
- [ ] Every child can resolve the parent spec artifact
- [ ] Final line contains `NEXT=review`
</self_check>

$ARGUMENTS
