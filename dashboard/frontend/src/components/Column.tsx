import { useDroppable } from "@dnd-kit/core";
import type { StageName } from "../types";

const GATE_AFTER: Partial<Record<StageName, string>> = {
  review: "Gate 2",
  document: "Gate 3"
};

interface Props {
  stage: StageName;
  hasPendingGate: boolean;
  children: React.ReactNode;
}

export function Column({ stage, hasPendingGate, children }: Props) {
  const { setNodeRef, isOver } = useDroppable({ id: `col-${stage}` });
  const dashed = hasPendingGate;
  return (
    <div
      ref={setNodeRef}
      className={[
        "bg-panel rounded p-2 min-h-[300px]",
        dashed ? "border-2 border-dashed border-amber-500" : "",
        isOver ? "ring-2 ring-blue-500" : ""
      ].join(" ")}
      data-stage={stage}
    >
      <div className="text-xs uppercase tracking-wide text-slate-400 mb-2">
        {stage}{hasPendingGate && GATE_AFTER[stage] && <span className="text-amber-400"> ⚠ {GATE_AFTER[stage]}</span>}
      </div>
      <div className="flex flex-col gap-2">{children}</div>
    </div>
  );
}
