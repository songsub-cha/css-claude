import type { EpicFlow } from "../types";

// Core Phase B deliverable: render an Epic's Phase nodes + dependency edges with
// per-Phase current Stage and PR status (the "work flow" view).
export function EpicFlowView({ flow }: { flow: EpicFlow }) {
  // Map each node's incoming dependency edges (for the "stacked on" indicator).
  const incoming = new Map<number, number[]>();
  for (const e of flow.edges) {
    incoming.set(e.to, [...(incoming.get(e.to) ?? []), e.from]);
  }

  return (
    <div data-testid="epic-flow" className="bg-panel rounded p-3 mb-3">
      {flow.epic && (
        <div className="text-sm font-semibold text-slate-200 mb-2">{flow.epic.label}</div>
      )}
      <div className="flex gap-2 flex-wrap items-stretch">
        {flow.nodes.map((n) => {
          const deps = incoming.get(n.phase_index) ?? [];
          return (
            <div
              key={n.phase_index}
              data-testid="phase-node"
              className="border border-slate-700 rounded p-2 min-w-[140px]"
            >
              <div className="text-xs text-slate-400">
                p{n.phase_index}
                {deps.length > 0 && (
                  <span className="text-amber-400"> {deps.map((d) => `← p${d}`).join(" ")}</span>
                )}
              </div>
              <div className="text-sm font-medium">{n.phase_label ?? `Phase ${n.phase_index}`}</div>
              <div className="mt-1 flex items-center gap-2">
                <span className="bg-blue-900 text-xs px-1.5 py-0.5 rounded">{n.current_stage}</span>
                {n.pr_url ? (
                  <a href={n.pr_url} className="text-xs text-blue-300 underline">PR</a>
                ) : (
                  <span className="text-xs text-slate-500">{n.pr_status}</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
