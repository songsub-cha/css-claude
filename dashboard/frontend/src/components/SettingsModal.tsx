import { useProjectsStore } from "../stores/projectsStore";
import { patchProjectColor } from "../api/client";

interface Props { onClose: () => void; }

export function SettingsModal({ onClose }: Props) {
  const projects = useProjectsStore(s => s.projects);
  const patch = useProjectsStore(s => s.patch);

  const handleChange = async (id: number, color: string) => {
    try {
      const updated = await patchProjectColor(id, color);
      patch(id, updated.color);
    } catch (_e) { /* toast handled elsewhere */ }
  };

  return (
    <div
      className="fixed inset-0 bg-black/60 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div className="bg-panel p-6 rounded w-[480px]" onClick={(e) => e.stopPropagation()}>
        <h2 className="font-semibold mb-4">Project Colors</h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-slate-400">
              <th>Repo</th><th>Path</th><th>Color</th>
            </tr>
          </thead>
          <tbody>
            {projects.map(p => (
              <tr key={p.id} className="border-t border-slate-700">
                <td className="py-2">{p.repo_name}</td>
                <td className="py-2 text-xs text-slate-400">{p.repo_root}</td>
                <td className="py-2">
                  <input
                    type="color"
                    aria-label={p.repo_name}
                    defaultValue={p.color}
                    onBlur={(e) => handleChange(p.id, e.target.value)}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <button onClick={onClose} className="mt-4 px-3 py-1 bg-slate-700 rounded">Close</button>
      </div>
    </div>
  );
}
