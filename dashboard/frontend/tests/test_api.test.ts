import { setupServer } from "msw/node";
import { http, HttpResponse } from "msw";
import { listSessions, approveGate } from "../src/api/client";

const server = setupServer(
  http.get("/api/sessions", () => HttpResponse.json({ sessions: [{ slug: "x", repoName: "r" }] })),
  http.post("/api/sessions/:slug/gates/:gate/approve", () => HttpResponse.json({ approved: true }))
);

beforeAll(() => server.listen());
afterAll(() => server.close());

test("listSessions returns array", async () => {
  const sessions = await listSessions();
  expect(sessions[0].slug).toBe("x");
});

test("approveGate posts correctly", async () => {
  const r = await approveGate("x", "gate2_pre_execute");
  expect(r.approved).toBe(true);
});

test("listSessions maps snake_case API fields to camelCase Session", async () => {
  server.use(
    http.get("/api/sessions", () => HttpResponse.json({ sessions: [{
      slug: "epic-x-p2", idea: "i", repo_root: "/r", repo_name: "css-claude",
      current_phase: "execute", phases: {}, gates: {}, mtime: 1,
      kind: "phase", parent_slug: "epic-x", phase_index: 2, phase_label: "API", depends_on: [1],
    }] }))
  );
  const [s] = await listSessions();
  expect(s.repoRoot).toBe("/r");
  expect(s.repoName).toBe("css-claude");
  expect(s.currentStage).toBe("execute");
  expect(s.kind).toBe("phase");
  expect(s.parentSlug).toBe("epic-x");
  expect(s.phaseIndex).toBe(2);
  expect(s.phaseLabel).toBe("API");
  expect(s.dependsOn).toEqual([1]);
});
