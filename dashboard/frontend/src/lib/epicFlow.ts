// Client-side Epic grouping + flow derivation, mirroring backend
// services/epic_flow.py so the flow view can render from the flat session list
// (no extra fetch). See dashboard-epic-phase-view design (Phase B).
import type { Session, EpicFlow, PhaseNode } from "../types";

export interface EpicGroup {
  epic: Session | null;
  phases: Session[];
}

export function groupByEpic(sessions: Session[]): Record<string, EpicGroup> {
  const groups: Record<string, EpicGroup> = {};

  // Register every Epic (non-phase) first so phases can find their parent.
  for (const s of sessions) {
    if (s.kind !== "phase") {
      groups[s.slug] ??= { epic: s, phases: [] };
    }
  }
  // Attach phases to their parent (or an orphan group keyed by parentSlug).
  for (const s of sessions) {
    if (s.kind !== "phase") continue;
    const key = s.parentSlug ?? s.slug;
    (groups[key] ??= { epic: null, phases: [] }).phases.push(s);
  }
  for (const g of Object.values(groups)) {
    g.phases.sort((a, b) => (a.phaseIndex ?? Infinity) - (b.phaseIndex ?? Infinity));
  }
  return groups;
}

function prFields(s: Session): { pr_status: string; pr_url: string | null } {
  const pr = s.phases?.pr ?? {};
  const pr_url = (pr as any).artifact ?? null;
  return { pr_status: pr_url ? "open" : ((pr as any).status ?? "pending"), pr_url };
}

function node(phaseIndex: number, label: string | null, s: Session): PhaseNode {
  return {
    phase_index: phaseIndex,
    phase_label: label,
    current_stage: s.currentStage,
    ...prFields(s),
  };
}

export function toEpicFlow(group: EpicGroup): EpicFlow {
  const epic = group.epic
    ? { slug: group.epic.slug, label: group.epic.idea || group.epic.slug }
    : null;

  if (group.phases.length === 0) {
    if (!group.epic) return { epic: null, nodes: [], edges: [] };
    return { epic, nodes: [node(1, group.epic.idea || group.epic.slug, group.epic)], edges: [] };
  }

  const nodes: PhaseNode[] = [];
  const edges: { from: number; to: number }[] = [];
  for (const p of group.phases) {
    const idx = p.phaseIndex ?? 0;
    nodes.push(node(idx, p.phaseLabel ?? null, p));
    for (const dep of p.dependsOn) edges.push({ from: dep, to: idx });
  }
  return { epic, nodes, edges };
}
