import type { Session, ArtifactRef, StageName } from "../types";
import { ArtifactAccordion } from "./ArtifactAccordion";

const STAGES: StageName[] = ["interview","plan","review","execute","verify","document","pr"];

interface Props {
  session: Session;
  color: string;
  artifacts: ArtifactRef[];
  onClose: () => void;
  onRetry: () => void;
  isFailed?: boolean;
}

export function DetailSlideOver({ session, color, artifacts, onClose, onRetry, isFailed }: Props) {
  return (
    <aside className="fixed right-0 top-0 h-screen w-80 bg-panel border-l border-slate-700 p-4 overflow-y-auto shadow-2xl">
      <div className="flex items-center gap-2 mb-3">
        <div style={{ width: 4, height: 20, background: color }} />
        <h2 className="font-semibold flex-1">{session.slug}</h2>
        <button onClick={onClose} aria-label="close">✕</button>
      </div>
      <div className="flex gap-1 flex-wrap mb-3">
        <span className="bg-slate-800 text-xs px-2 py-0.5 rounded">{session.repoName}</span>
        <span className="bg-blue-900 text-xs px-2 py-0.5 rounded">{session.currentStage}</span>
      </div>
      <section className="mb-3">
        <div className="text-xs uppercase text-slate-400 mb-1">Idea</div>
        <div className="text-sm">{session.idea}</div>
      </section>
      <section className="mb-3">
        <div className="text-xs uppercase text-slate-400 mb-1">Timeline</div>
        <ul className="text-xs space-y-1">
          {STAGES.map((st) => {
            const ph = session.phases[st];
            const icon = ph?.status === "completed" ? "✓" : ph?.status === "in_progress" ? "●" : "—";
            return <li key={st}><span className="inline-block w-4">{icon}</span> {st}</li>;
          })}
        </ul>
      </section>
      <section className="mb-3">
        <div className="text-xs uppercase text-slate-400 mb-1">Artifacts</div>
        <ArtifactAccordion slug={session.slug} artifacts={artifacts} />
      </section>
      {isFailed && (
        <section>
          <button onClick={onRetry} className="bg-red-700 text-white px-3 py-1 rounded text-sm">▶ Retry resume</button>
        </section>
      )}
    </aside>
  );
}
