import { render, screen } from "@testing-library/react";
import { EpicFlowView } from "../src/components/EpicFlowView";
import type { EpicFlow } from "../src/types";

const flow: EpicFlow = {
  epic: { slug: "epic-x", label: "The Epic" },
  nodes: [
    { phase_index: 1, phase_label: "foundation", current_stage: "verify", pr_status: "open", pr_url: "https://gh/x/pull/3" },
    { phase_index: 2, phase_label: "api", current_stage: "execute", pr_status: "pending", pr_url: null },
    { phase_index: 3, phase_label: "ui", current_stage: "plan", pr_status: "pending", pr_url: null },
  ],
  edges: [{ from: 1, to: 2 }, { from: 2, to: 3 }],
};

test("renders one node per Phase with label + stage", () => {
  render(<EpicFlowView flow={flow} />);
  expect(screen.getAllByTestId("phase-node")).toHaveLength(3);
  expect(screen.getByText(/foundation/)).toBeInTheDocument();
  expect(screen.getByText(/verify/)).toBeInTheDocument();
  expect(screen.getByText("The Epic")).toBeInTheDocument();
});

test("renders a PR link when pr_url present", () => {
  render(<EpicFlowView flow={flow} />);
  const link = screen.getByRole("link", { name: /PR/i });
  expect(link).toHaveAttribute("href", "https://gh/x/pull/3");
});

test("shows stacked-on indicator for dependent phases", () => {
  render(<EpicFlowView flow={flow} />);
  // p2 depends on p1, p3 on p2
  expect(screen.getByText(/← p1/)).toBeInTheDocument();
  expect(screen.getByText(/← p2/)).toBeInTheDocument();
});

test("empty flow renders without crashing", () => {
  render(<EpicFlowView flow={{ epic: null, nodes: [], edges: [] }} />);
  expect(screen.queryAllByTestId("phase-node")).toHaveLength(0);
});
