import { create } from "zustand";
interface State {
  selectedSlug: string | null;
  setSelected: (slug: string | null) => void;
  toasts: { id: string; kind: "ok" | "info" | "warn" | "err"; msg: string }[];
  pushToast: (kind: State["toasts"][0]["kind"], msg: string) => void;
  dismissToast: (id: string) => void;
  artifactCache: Record<string, { content_md: string; mtime: number }>;
  cacheArtifact: (key: string, val: State["artifactCache"][string]) => void;
}
export const useUIStore = create<State>((set) => ({
  selectedSlug: null,
  setSelected: (slug) => set({ selectedSlug: slug }),
  toasts: [],
  pushToast: (kind, msg) => set((st) => ({ toasts: [...st.toasts, { id: crypto.randomUUID(), kind, msg }] })),
  dismissToast: (id) => set((st) => ({ toasts: st.toasts.filter(t => t.id !== id) })),
  artifactCache: {},
  cacheArtifact: (k, v) => set((st) => ({ artifactCache: { ...st.artifactCache, [k]: v } }))
}));
