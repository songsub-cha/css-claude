import { Fragment, useEffect, useMemo, useState } from "react";
import { listHistory } from "../api/client";

export function HistoryView() {
  const [items, setItems] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const limit = 20;

  useEffect(() => {
    listHistory({ limit, offset }).then(j => {
      setItems(j.items);
      setTotal(j.total);
    });
  }, [offset]);

  // Group archived Phases (rows with parent_slug) under their Epic; rows without
  // a parent_slug (legacy single-session archives) stay flat (D9).
  const { epicGroups, loose } = useMemo(() => {
    const groups = new Map<string, any[]>();
    const flat: any[] = [];
    for (const it of items) {
      if (it.parent_slug) {
        if (!groups.has(it.parent_slug)) groups.set(it.parent_slug, []);
        groups.get(it.parent_slug)!.push(it);
      } else {
        flat.push(it);
      }
    }
    return { epicGroups: [...groups.entries()], loose: flat };
  }, [items]);

  const Row = (it: any) => (
    <tr key={it.id} className="border-t border-slate-700">
      <td>{it.finished_at?.slice(0, 10)}</td>
      <td>{it.session_id}</td>
      <td className={it.outcome === "completed" ? "text-emerald-400" : "text-red-400"}>{it.outcome}</td>
      <td>{it.pr_url ? <a href={it.pr_url} className="text-blue-300">view</a> : "—"}</td>
    </tr>
  );

  return (
    <div className="p-4">
      <h2 className="font-semibold mb-2">History</h2>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-slate-400">
            <th>Finished</th><th>Session</th><th>Outcome</th><th>PR</th>
          </tr>
        </thead>
        <tbody>
          {epicGroups.map(([epicSlug, rows]) => (
            <Fragment key={`epic-${epicSlug}`}>
              <tr data-testid="epic-history-group" className="bg-slate-800/50">
                <td colSpan={4} className="font-semibold text-slate-200 py-1">▸ {epicSlug}</td>
              </tr>
              {rows.map(Row)}
            </Fragment>
          ))}
          {loose.map(Row)}
        </tbody>
      </table>
      <div className="mt-2 flex gap-2 text-xs">
        <button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - limit))}>
          &larr; prev
        </button>
        <button disabled={offset + limit >= total} onClick={() => setOffset(offset + limit)}>
          next &rarr;
        </button>
        <span className="text-slate-400">
          {offset + 1}–{Math.min(offset + limit, total)} / {total}
        </span>
      </div>
    </div>
  );
}
