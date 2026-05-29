import type { Session, Project, ArtifactRef, GateName } from "../types";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(path, { headers: { "Content-Type": "application/json" }, ...init });
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}: ${await r.text()}`);
  return r.json();
}

export const listSessions = () => req<{ sessions: Session[] }>("/api/sessions").then(r => r.sessions);
export const getSession = (slug: string) => req<Session>(`/api/sessions/${slug}`);
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
