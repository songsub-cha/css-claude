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
