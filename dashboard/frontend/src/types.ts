// Stage = one of the 7 pipeline steps within a session (was "PhaseName").
// The feature-level unit is now "Phase" (an Epic's shippable increment). See
// docs/superpowers/specs/2026-05-29-epic-phase-pipeline-design.md (D1 vocabulary).
export type StageName = "interview" | "plan" | "review" | "execute" | "verify" | "document" | "pr";
export type SessionKind = "epic" | "phase";
export type GateName = "gate2_pre_execute" | "gate3_pre_pr";
export type ArtifactName = "spec" | "plan" | "exec-log" | "verify" | "code-review" | "security-review" | "docs" | `rich-spec-${string}`;

export interface GateState {
  state: "pending" | "approved" | null;
  source: "dashboard_drag" | "terminal_ask" | null;
  reached_at: string | null;
  approved_at: string | null;
  approved_by: string | null;
}

export interface Session {
  slug: string;
  idea: string;
  repoRoot: string;
  repoName: string;
  currentStage: StageName;
  phases: Record<string, { status: string; artifact?: string; completed_at?: string }>;
  gates: Partial<Record<GateName, GateState | null>>;
  mtime: number;
  // Epic/Phase hierarchy (Phase B). Legacy sessions are kind="epic" with
  // parentSlug=null and dependsOn=[].
  kind: SessionKind;
  parentSlug: string | null;
  phaseIndex: number | null;
  phaseLabel?: string | null;
  dependsOn: number[];
}

export interface Project {
  id: number;
  repo_root: string;
  repo_name: string;
  color: string;
}

export interface ArtifactRef {
  name: ArtifactName;
  path: string;
  size: number;
  mtime: number;
}

// A single Phase node in an Epic flow graph (matches the backend epic_flow shape).
export interface PhaseNode {
  phase_index: number;
  phase_label: string | null;
  current_stage: StageName;
  pr_status: string;
  pr_url: string | null;
}

// The Epic -> Phase flow graph returned by GET /api/sessions/epics (build_epic_flow).
export interface EpicFlow {
  epic: { slug: string; label: string } | null;
  nodes: PhaseNode[];
  edges: { from: number; to: number }[];
}

// A child Phase session (camelCase view of the kind="phase" session).
export interface Phase {
  slug: string;
  parentSlug: string;
  phaseIndex: number;
  phaseLabel: string | null;
  dependsOn: number[];
  currentStage: StageName;
}

export type SSEEvent =
  | { type: "session_updated"; data: { slug: string; phase: StageName; gates: Session["gates"]; mtime: number } }
  | { type: "gate_reached"; data: { session_id: string; gate: GateName; reached_at: string } }
  | { type: "gate_approved"; data: { session_id: string; gate: GateName; source: string } }
  | { type: "resume_started"; data: { session_id: string; run_id: string } }
  | { type: "resume_failed"; data: { session_id: string; gate: GateName; error: string; retry_count: number } }
  | { type: "session_completed"; data: { session_id: string; pr_url: string; outcome: string } }
  | { type: "project_registered"; data: { project_id: number; repo_name: string; color: string } }
  | { type: "phase_started"; data: { slug: string; parent_slug: string | null; phase_index: number | null } }
  | { type: "phase_completed"; data: { slug: string; parent_slug: string | null; phase_index: number | null } }
  | { type: "phase_pr_opened"; data: { slug: string; parent_slug: string | null; phase_index: number | null; pr_url: string } };
