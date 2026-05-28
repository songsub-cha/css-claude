import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { setupServer } from "msw/node";
import { http, HttpResponse } from "msw";
import { SettingsModal } from "../src/components/SettingsModal";
import { useProjectsStore } from "../src/stores/projectsStore";

const server = setupServer(
  http.patch("/api/projects/1", () =>
    HttpResponse.json({ id: 1, repo_root: "/a", repo_name: "alpha", color: "#ef4444" }))
);
beforeAll(() => server.listen());
afterAll(() => server.close());

test("color change PATCHes + updates store", async () => {
  useProjectsStore.setState({ projects: [{ id: 1, repo_root: "/a", repo_name: "alpha", color: "#22c55e" }] });
  render(<SettingsModal onClose={() => {}} />);
  const input = screen.getByLabelText(/alpha/) as HTMLInputElement;
  fireEvent.change(input, { target: { value: "#ef4444" } });
  fireEvent.blur(input);
  await waitFor(() => expect(useProjectsStore.getState().projects[0].color).toBe("#ef4444"));
});
