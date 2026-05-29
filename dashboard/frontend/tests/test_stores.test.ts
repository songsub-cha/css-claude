import { useSessionsStore } from "../src/stores/sessionsStore";
import { useProjectsStore } from "../src/stores/projectsStore";

test("sessionsStore initial empty", () => {
  expect(useSessionsStore.getState().sessions).toEqual([]);
});
test("sessionsStore upsert updates by slug", () => {
  useSessionsStore.getState().upsert({ slug: "x", currentStage: "plan" } as any);
  expect(useSessionsStore.getState().sessions[0].slug).toBe("x");
  useSessionsStore.getState().upsert({ slug: "x", currentStage: "review" } as any);
  expect(useSessionsStore.getState().sessions).toHaveLength(1);
  expect(useSessionsStore.getState().sessions[0].currentStage).toBe("review");
});
test("projectsStore colorMap derived", () => {
  useProjectsStore.setState({ projects: [{ id: 1, repo_root: "/r", repo_name: "r", color: "#22c55e" }] });
  expect(useProjectsStore.getState().colorByRepoRoot("/r")).toBe("#22c55e");
});
