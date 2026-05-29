import type { Session, Project, ArtifactRef, GateName } from "../types";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(path, { headers: { "Content-Type": "application/json" }, ...init });
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}: ${await r.text()}`);
  return r.json();
}

// The backend serves snake_case session JSON (repo_root, current_phase, parent_slug,
// …); the frontend Session is camelCase. Map at the boundary, tolerating either
// casing so mocks/tests that already use camelCase keep working.
export function mapSession(s: any): Session {
  return {
    slug: s.slug,
    idea: s.idea ?? "",
    repoRoot: s.repo_root ?? s.repoRoot ?? "",
    repoName: s.repo_name ?? s.repoName ?? "(unknown)",
    currentStage: s.current_phase ?? s.current_stage ?? s.currentStage ?? "interview",
    phases: s.phases ?? {},
    gates: s.gates ?? {},
    mtime: s.mtime ?? 0,
    kind: s.kind ?? "epic",
    parentSlug: s.parent_slug ?? s.parentSlug ?? null,
    phaseIndex: s.phase_index ?? s.phaseIndex ?? null,
    phaseLabel: s.phase_label ?? s.phaseLabel ?? null,
    dependsOn: s.depends_on ?? s.dependsOn ?? [],
  };
}

export const listSessions = () => req<{ sessions: any[] }>("/api/sessions").then(r => r.sessions.map(mapSession));
export const getSession = (slug: string) => req<any>(`/api/sessions/${slug}`).then(mapSession);
export const listArtifacts = (slug: string) => req<{ artifacts: ArtifactRef[] }>(`/api/sessions/${slug}/artifacts`).then(r => r.artifacts);
export const getArtifact = (slug: string, name: string) => req<{ name: string; content_md: string; mtime: number }>(`/api/sessions/${slug}/artifacts/${name}`);
export const approveGate = (slug: string, gate: GateName) => req<{ approved: boolean; event_id: string }>(`/api/sessions/${slug}/gates/${gate}/approve`, { method: "POST" });
export const retryGate = (slug: string, gate: GateName) => req<{ retried: boolean; event_id: string }>(`/api/sessions/${slug}/gates/${gate}/retry`, { method: "POST" });
export const listProjects = () => req<{ projects: Project[] }>("/api/projects").then(r => r.projects);
export const patchProjectColor = (id: number, color: string) => req<Project>(`/api/projects/${id}`, { method: "PATCH", body: JSON.stringify({ color }) });
export const listHistory = (opts: { project_id?: number; outcome?: string; limit?: number; offset?: number } = {}) => {
  const q = new URLSearchParams(Object.entries(opts).filter(([, v]) => v !== undefined).map(([k, v]) => [k, String(v)]));
  return req<{ total: number; items: any[] }>(`/api/history?${q}`);
};
