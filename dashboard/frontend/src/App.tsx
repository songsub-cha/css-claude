import { useEffect, useState } from "react";
import { Routes, Route } from "react-router-dom";
import { TopBar } from "./components/TopBar";
import { KanbanBoard } from "./components/KanbanBoard";
import { DetailSlideOver } from "./components/DetailSlideOver";
import { SettingsModal } from "./components/SettingsModal";
import { HistoryView } from "./components/HistoryView";
import { ToastContainer } from "./components/ToastContainer";
import { useSessionsStore } from "./stores/sessionsStore";
import { useProjectsStore } from "./stores/projectsStore";
import { useUIStore } from "./stores/uiStore";
import { listSessions, listProjects, listArtifacts } from "./api/client";
import { SSEManager } from "./api/sse";

export default function App() {
  const sessions = useSessionsStore(s => s.sessions);
  const setAllSessions = useSessionsStore(s => s.setAll);
  const upsertSession = useSessionsStore(s => s.upsert);
  const setProjects = useProjectsStore(s => s.setAll);
  const colorOf = useProjectsStore(s => s.colorByRepoRoot);
  const selectedSlug = useUIStore(s => s.selectedSlug);
  const setSelected = useUIStore(s => s.setSelected);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [artifacts, setArtifacts] = useState<any[]>([]);

  useEffect(() => {
    listSessions().then(setAllSessions);
    listProjects().then(setProjects);
    const mgr = new SSEManager();
    mgr.start();
    const off1 = mgr.on("session_updated", (d: any) =>
      upsertSession({
        slug: d.slug,
        currentStage: d.phase,
        gates: d.gates,
        mtime: d.mtime
      } as any)
    );
    // F2: project_registered SSE → patch store color
    const off2 = mgr.on("project_registered", (d: any) =>
      useProjectsStore.getState().patch(d.project_id, d.color)
    );
    return () => {
      off1();
      off2();
      mgr.stop();
    };
  }, [setAllSessions, setProjects, upsertSession]);

  useEffect(() => {
    if (selectedSlug) listArtifacts(selectedSlug).then(setArtifacts);
  }, [selectedSlug]);

  const selected = sessions.find(s => s.slug === selectedSlug);

  return (
    <>
      <TopBar activeCount={sessions.length} onOpenSettings={() => setSettingsOpen(true)} />
      <Routes>
        <Route path="/" element={<KanbanBoard />} />
        <Route path="/history" element={<HistoryView />} />
      </Routes>
      {selected && (
        <DetailSlideOver
          session={selected}
          color={colorOf(selected.repoRoot)}
          artifacts={artifacts}
          onClose={() => setSelected(null)}
          onRetry={() => {}}
        />
      )}
      {settingsOpen && <SettingsModal onClose={() => setSettingsOpen(false)} />}
      <ToastContainer />
    </>
  );
}
