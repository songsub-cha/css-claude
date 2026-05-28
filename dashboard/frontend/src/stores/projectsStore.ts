import { create } from "zustand";
import type { Project } from "../types";

interface State {
  projects: Project[];
  setAll: (p: Project[]) => void;
  patch: (id: number, color: string) => void;
  colorByRepoRoot: (repoRoot: string) => string;
}
const DEFAULT = "#9ca3af";
export const useProjectsStore = create<State>((set, get) => ({
  projects: [],
  setAll: (p) => set({ projects: p }),
  patch: (id, color) => set((st) => ({ projects: st.projects.map(p => p.id === id ? { ...p, color } : p) })),
  colorByRepoRoot: (repoRoot) => get().projects.find(p => p.repo_root === repoRoot)?.color ?? DEFAULT
}));
