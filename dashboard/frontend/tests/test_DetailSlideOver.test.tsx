import { render, screen } from "@testing-library/react"; import { vi } from "vitest";
import { DetailSlideOver } from "../src/components/DetailSlideOver";
test("renders + closes", () => {
  const onClose = vi.fn();
  render(<DetailSlideOver session={{slug:"feat-x",idea:"do thing",repoName:"alpha",repoRoot:"/a",currentStage:"review",phases:{interview:{status:"completed"},plan:{status:"completed"},review:{status:"in_progress"}},gates:{},mtime:0} as any} color="#22c55e" artifacts={[]} onClose={onClose} onRetry={()=>{}}/>);
  expect(screen.getByText("feat-x")).toBeInTheDocument();
  expect(screen.getByText("do thing")).toBeInTheDocument();
  screen.getByText("✕").click();
  expect(onClose).toHaveBeenCalled();
});

test("phase session shows index/label, deps, and stacked note", () => {
  render(<DetailSlideOver session={{
    slug:"epic-x-p2", idea:"api layer", repoName:"alpha", repoRoot:"/a", currentStage:"execute",
    phases:{}, gates:{}, mtime:0,
    kind:"phase", parentSlug:"epic-x", phaseIndex:2, phaseLabel:"API layer", dependsOn:[1],
  } as any} color="#22c55e" artifacts={[]} onClose={()=>{}} onRetry={()=>{}}/>);
  expect(screen.getByText(/Phase 2: API layer/)).toBeInTheDocument();
  expect(screen.getByTestId("phase-deps")).toHaveTextContent("1");
  expect(screen.getByText(/stacked/i)).toBeInTheDocument();
});
