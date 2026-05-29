import { useState } from "react";
import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import rehypeHighlight from "rehype-highlight";
import remarkGfm from "remark-gfm";
import { useUIStore } from "../stores/uiStore";
import { getArtifact } from "../api/client";
import type { ArtifactRef } from "../types";

interface Props { slug: string; artifacts: ArtifactRef[]; }

export function ArtifactAccordion({ slug, artifacts }: Props) {
  const [open, setOpen] = useState<Set<string>>(new Set());
  const cache = useUIStore(s => s.artifactCache);
  const cacheArtifact = useUIStore(s => s.cacheArtifact);

  const toggle = async (name: string) => {
    const newOpen = new Set(open);
    if (newOpen.has(name)) { newOpen.delete(name); setOpen(newOpen); return; }
    newOpen.add(name); setOpen(newOpen);
    const key = `${slug}/${name}`;
    if (!cache[key]) {
      const a = await getArtifact(slug, name);
      cacheArtifact(key, { content_md: a.content_md, mtime: a.mtime });
    }
  };

  return (
    <div className="space-y-1">
      {artifacts.map(a => (
        <div key={a.name} className="bg-card rounded">
          <button onClick={() => toggle(a.name)}
                  className="w-full text-left px-2 py-1 text-sm flex justify-between">
            <span><span aria-hidden="true">{open.has(a.name) ? "▾" : "▸"} </span>{a.name}</span>
            <span className="text-xs text-slate-400">{a.size}B</span>
          </button>
          {open.has(a.name) && (
            <div className="p-3 prose prose-invert max-w-none text-xs">
              {cache[`${slug}/${a.name}`]
                ? <ReactMarkdown
                    rehypePlugins={[[rehypeSanitize], [rehypeHighlight]]}
                    remarkPlugins={[remarkGfm]}>
                    {cache[`${slug}/${a.name}`].content_md}
                  </ReactMarkdown>
                : <span className="text-slate-500">loading…</span>}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
