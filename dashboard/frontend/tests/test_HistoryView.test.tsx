import { render, screen, waitFor } from "@testing-library/react";
import { setupServer } from "msw/node";
import { http, HttpResponse } from "msw";
import { HistoryView } from "../src/components/HistoryView";

const server = setupServer(
  http.get("/api/history", () =>
    HttpResponse.json({
      total: 2,
      items: [
        { id: 1, session_id: "feat-a", outcome: "completed", finished_at: "2026-05-01", pr_url: "u" },
        { id: 2, session_id: "feat-b", outcome: "failed", finished_at: "2026-05-02", pr_url: null }
      ]
    })
  )
);
beforeAll(() => server.listen());
afterAll(() => server.close());

test("renders rows", async () => {
  render(<HistoryView />);
  await waitFor(() => expect(screen.getByText("feat-a")).toBeInTheDocument());
  expect(screen.getByText("feat-b")).toBeInTheDocument();
});

test("groups archived phases under their Epic", async () => {
  server.use(
    http.get("/api/history", () =>
      HttpResponse.json({
        total: 2,
        items: [
          { id: 10, session_id: "epic-x-p1", parent_slug: "epic-x", phase_index: 1, outcome: "completed", finished_at: "2026-05-03", pr_url: "u1" },
          { id: 11, session_id: "epic-x-p2", parent_slug: "epic-x", phase_index: 2, outcome: "completed", finished_at: "2026-05-04", pr_url: "u2" }
        ]
      })
    )
  );
  render(<HistoryView />);
  await waitFor(() => expect(screen.getByTestId("epic-history-group")).toBeInTheDocument());
  expect(screen.getByTestId("epic-history-group")).toHaveTextContent("epic-x");
  expect(screen.getByText("epic-x-p1")).toBeInTheDocument();
  expect(screen.getByText("epic-x-p2")).toBeInTheDocument();
});
