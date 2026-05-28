import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";

// Mock SSEManager.start to prevent real EventSource in jsdom
vi.mock("../src/api/sse", () => ({
  SSEManager: class {
    start() {}
    stop() {}
    on(_type: string, _cb: any) { return () => {}; }
  }
}));

// Mock API calls to prevent real fetches
vi.mock("../src/api/client", async (importOriginal) => {
  const mod = await importOriginal<typeof import("../src/api/client")>();
  return {
    ...mod,
    listSessions: vi.fn().mockResolvedValue([]),
    listProjects: vi.fn().mockResolvedValue([]),
    listArtifacts: vi.fn().mockResolvedValue([]),
  };
});

import App from "../src/App";

test("App renders TopBar", () => {
  render(<MemoryRouter><App /></MemoryRouter>);
  expect(screen.getByText("CSS Pipeline Dashboard")).toBeInTheDocument();
});

// F2: project_registered SSE updates store color
import { useProjectsStore } from "../src/stores/projectsStore";

test("project_registered SSE updates store", () => {
  // App subscribes mgr.on("project_registered", d => useProjectsStore.getState().patch(d.project_id, d.color))
  useProjectsStore.setState({ projects: [{ id: 1, repo_root: "/a", repo_name: "a", color: "#000000" }] });
  // simulate by directly invoking the patch the listener would call
  useProjectsStore.getState().patch(1, "#22c55e");
  expect(useProjectsStore.getState().projects[0].color).toBe("#22c55e");
});
