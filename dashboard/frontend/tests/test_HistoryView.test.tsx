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
