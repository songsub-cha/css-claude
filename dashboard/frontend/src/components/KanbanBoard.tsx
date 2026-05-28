import { DndContext, DragEndEvent, useSensor, useSensors, PointerSensor } from "@dnd-kit/core";
import { useEffect } from "react";
import { useSessionsStore } from "../stores/sessionsStore";
import { useProjectsStore } from "../stores/projectsStore";
import { useUIStore } from "../stores/uiStore";
import { approveGate } from "../api/client";
import { Column } from "./Column";
import { SessionCard } from "./SessionCard";
import type { PhaseName, GateName } from "../types";

const STAGES: PhaseName[] = ["interview","plan","review","execute","verify","document","pr"];

const VALID_TRANSITIONS: Array<[PhaseName, PhaseName, GateName]> = [
  ["review", "execute", "gate2_pre_execute"],
  ["document", "pr", "gate3_pre_pr"]
];

export function KanbanBoard() {
  const sessions = useSessionsStore(s => s.sessions);
  const colorOf = useProjectsStore(s => s.colorByRepoRoot);
  const setSelected = useUIStore(s => s.setSelected);
  const pushToast = useUIStore(s => s.pushToast);
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 6 } }));

  const handleDragEnd = async (e: DragEndEvent) => {
    const slug = String(e.active.id);
    const overId = String(e.over?.id ?? "");
    if (!overId.startsWith("col-")) return;
    const toStage = overId.slice(4) as PhaseName;
    const sess = sessions.find(s => s.slug === slug);
    if (!sess) return;
    const transition = VALID_TRANSITIONS.find(([from, to]) => from === sess.currentPhase && to === toStage);
    if (!transition) {
      pushToast("warn", "Gates 외 이동은 불가");
      return;
    }
    const [, , gate] = transition;
    const gateState = (sess.gates[gate] as any)?.state;
    if (gateState !== "pending") {
      pushToast("warn", `${gate} is not pending`);
      return;
    }
    try {
      await approveGate(slug, gate);
      pushToast("ok", `${gate} approved — resuming…`);
    } catch (err) {
      pushToast("err", `Approval failed: ${(err as Error).message}`);
    }
  };

  // Test escape hatch: allows unit tests to simulate drag without real pointer events
  useEffect(() => {
    const root = document.querySelector("[data-testid=kanban-board]");
    if (!root) return;
    const handler = (e: any) => handleDragEnd({ active: { id: e.detail.activeSlug }, over: { id: `col-${e.detail.overStage}` } } as any);
    root.addEventListener("test-drag", handler as any);
    return () => root.removeEventListener("test-drag", handler as any);
  });

  return (
    <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
      <div data-testid="kanban-board" className="grid grid-cols-7 gap-2 p-4">
        {STAGES.map((stage) => {
          const inCol = sessions.filter(s => s.currentPhase === stage);
          const hasPendingGate = inCol.some(s =>
            (stage === "review" && (s.gates.gate2_pre_execute as any)?.state === "pending") ||
            (stage === "document" && (s.gates.gate3_pre_pr as any)?.state === "pending")
          );
          return (
            <Column key={stage} stage={stage} hasPendingGate={hasPendingGate}>
              {inCol.map(s => (
                <SessionCard
                  key={s.slug}
                  session={s}
                  color={colorOf(s.repoRoot)}
                  isPendingGate={
                    (stage === "review" && (s.gates.gate2_pre_execute as any)?.state === "pending") ||
                    (stage === "document" && (s.gates.gate3_pre_pr as any)?.state === "pending")
                  }
                  isFailed={false}
                  onClick={() => setSelected(s.slug)}
                />
              ))}
            </Column>
          );
        })}
      </div>
    </DndContext>
  );
}
