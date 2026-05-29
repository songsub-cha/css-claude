import { create } from "zustand";
import type { Session } from "../types";

interface State {
  sessions: Session[];
  upsert: (s: Session) => void;
  removeBySlug: (slug: string) => void;
  setAll: (list: Session[]) => void;
}
export const useSessionsStore = create<State>((set) => ({
  sessions: [],
  upsert: (s) => set((st) => ({
    sessions: st.sessions.some(x => x.slug === s.slug)
      ? st.sessions.map(x => x.slug === s.slug ? { ...x, ...s } : x)
      : [...st.sessions, s]
  })),
  removeBySlug: (slug) => set((st) => ({ sessions: st.sessions.filter(s => s.slug !== slug) })),
  setAll: (list) => set({ sessions: list })
}));
