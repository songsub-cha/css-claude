export type PhaseName = "interview" | "plan" | "review" | "execute" | "verify" | "document" | "pr";
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
  currentPhase: PhaseName;
  phases: Record<string, { status: string; artifact?: string; completed_at?: string }>;
  gates: Partial<Record<GateName, GateState | null>>;
  mtime: number;
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

export type SSEEvent =
  | { type: "session_updated"; data: { slug: string; phase: PhaseName; gates: Session["gates"]; mtime: number } }
  | { type: "gate_reached"; data: { session_id: string; gate: GateName; reached_at: string } }
  | { type: "gate_approved"; data: { session_id: string; gate: GateName; source: string } }
  | { type: "resume_started"; data: { session_id: string; run_id: string } }
  | { type: "resume_failed"; data: { session_id: string; gate: GateName; error: string; retry_count: number } }
  | { type: "session_completed"; data: { session_id: string; pr_url: string; outcome: string } }
  | { type: "project_registered"; data: { project_id: number; repo_name: string; color: string } };
