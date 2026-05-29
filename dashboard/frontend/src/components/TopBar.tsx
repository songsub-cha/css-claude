import { useProjectsStore } from "../stores/projectsStore";
import { Link } from "react-router-dom";

interface Props { activeCount: number; onOpenSettings: () => void; }

export function TopBar({ activeCount, onOpenSettings }: Props) {
  const projects = useProjectsStore(s => s.projects);
  return (
    <div className="flex items-center gap-3 px-4 py-3 bg-panel border-b border-slate-700">
      <h1 className="font-semibold">CSS Pipeline Dashboard</h1>
      <span className="text-xs text-slate-400">· {activeCount} active</span>
      <div className="ml-auto flex items-center gap-2">
        {projects.map(p => (
          <span key={p.id} className="bg-slate-800 text-xs px-2 py-0.5 rounded flex items-center gap-1">
            <span style={{ width: 8, height: 8, background: p.color, borderRadius: 2 }} />
            {p.repo_name}
          </span>
        ))}
        <Link to="/history" className="text-xs text-slate-300">History</Link>
        <button onClick={onOpenSettings} className="text-xs text-slate-300" aria-label="settings">&#9881;</button>
      </div>
    </div>
  );
}
