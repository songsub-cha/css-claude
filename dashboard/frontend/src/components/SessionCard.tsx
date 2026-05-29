import type { Session } from "../types";

interface Props {
  session: Session;
  color: string;
  isPendingGate: boolean;
  isFailed: boolean;
  onClick: () => void;
}

function elapsed(mtimeSec: number): string {
  const sec = Math.floor(Date.now()/1000 - mtimeSec);
  if (sec < 60) return `${sec}s`;
  if (sec < 3600) return `${Math.floor(sec/60)}m`;
  return `${Math.floor(sec/3600)}h`;
}

export function SessionCard({ session, color, isPendingGate, isFailed, onClick }: Props) {
  const isPhase = session.kind === "phase";
  const prUrl = (session.phases?.pr as any)?.artifact as string | undefined;
  return (
    <div
      role="article"
      onClick={onClick}
      className={[
        "relative flex bg-card rounded overflow-hidden cursor-grab select-none",
        isPendingGate ? "outline outline-2 outline-amber-500" : "",
        isFailed ? "shake-once" : ""
      ].join(" ")}
      data-slug={session.slug}
    >
      <div style={{ width: 3, background: color }} />
      <div className="px-2 py-1.5 flex-1">
        <div className="font-semibold text-sm">{session.slug}</div>
        <div className="text-xs text-slate-400">{session.repoName} · {elapsed(session.mtime)}</div>
        {isPhase && session.phaseIndex != null && (
          <div className="text-xs text-slate-300 mt-0.5 flex items-center gap-1 flex-wrap">
            <span>p{session.phaseIndex} · {session.phaseLabel ?? "phase"}</span>
            {session.dependsOn.length > 0 && (
              <span data-testid="stacked-marker" className="text-amber-400" title={`stacked on p${session.dependsOn.join(", p")}`}>⏶ stacked</span>
            )}
            {prUrl && <a href={prUrl} onClick={(e) => e.stopPropagation()} className="text-blue-300 underline">PR</a>}
          </div>
        )}
        {isPendingGate && <div data-testid="pending-gate-marker" className="text-xs text-amber-400 mt-1">⚠ drag right to approve</div>}
      </div>
      {isFailed && <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" data-testid="failed-marker" />}
    </div>
  );
}
