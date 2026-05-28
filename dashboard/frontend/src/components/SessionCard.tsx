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
        {isPendingGate && <div data-testid="pending-gate-marker" className="text-xs text-amber-400 mt-1">⚠ drag right to approve</div>}
      </div>
      {isFailed && <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" data-testid="failed-marker" />}
    </div>
  );
}
