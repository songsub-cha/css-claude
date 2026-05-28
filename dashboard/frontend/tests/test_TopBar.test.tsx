import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { TopBar } from "../src/components/TopBar";
import { useProjectsStore } from "../src/stores/projectsStore";

test("renders project chips + count", () => {
  useProjectsStore.setState({ projects: [
    { id: 1, repo_root: "/a", repo_name: "alpha", color: "#22c55e" },
    { id: 2, repo_root: "/b", repo_name: "beta", color: "#a855f7" }
  ]});
  render(<MemoryRouter><TopBar activeCount={3} onOpenSettings={() => {}} /></MemoryRouter>);
  expect(screen.getByText(/3 active/)).toBeInTheDocument();
  expect(screen.getByText("alpha")).toBeInTheDocument();
  expect(screen.getByText("beta")).toBeInTheDocument();
});
