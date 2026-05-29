import { render, screen } from "@testing-library/react";
import { SessionCard } from "../src/components/SessionCard";

test("renders slug, repo, elapsed", () => {
  render(<SessionCard session={{slug:"feat-x",repoName:"alpha",repoRoot:"/a",currentStage:"review",idea:"i",phases:{},gates:{},mtime:Date.now()/1000-60} as any} color="#22c55e" isPendingGate={false} isFailed={false} onClick={()=>{}}/>);
  expect(screen.getByText("feat-x")).toBeInTheDocument();
  expect(screen.getByText(/alpha/)).toBeInTheDocument();
  expect(screen.getByText(/m$/)).toBeInTheDocument();
});
test("pending-gate shows marker", () => {
  const { container } = render(<SessionCard session={{slug:"feat-y",repoName:"a",repoRoot:"/a",currentStage:"review",idea:"",phases:{},gates:{},mtime:0} as any} color="#22c55e" isPendingGate={true} isFailed={false} onClick={()=>{}}/>);
  expect(container.querySelector("[data-testid=pending-gate-marker]")).toBeInTheDocument();
});

test("phase session shows index/label, PR link, stacked marker", () => {
  render(<SessionCard session={{
    slug:"epic-x-p2", repoName:"a", repoRoot:"/a", currentStage:"execute", idea:"",
    phases:{ pr:{ status:"completed", artifact:"https://gh/x/pull/4" } }, gates:{}, mtime:0,
    kind:"phase", parentSlug:"epic-x", phaseIndex:2, phaseLabel:"API layer", dependsOn:[1],
  } as any} color="#22c55e" isPendingGate={false} isFailed={false} onClick={()=>{}}/>);
  expect(screen.getByText(/p2 · API layer/)).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /PR/i })).toHaveAttribute("href", "https://gh/x/pull/4");
  expect(screen.getByTestId("stacked-marker")).toBeInTheDocument();
});

test("epic/legacy session shows no phase affordances", () => {
  render(<SessionCard session={{
    slug:"feat-x", repoName:"a", repoRoot:"/a", currentStage:"review", idea:"",
    phases:{}, gates:{}, mtime:0, kind:"epic", parentSlug:null, phaseIndex:null, dependsOn:[],
  } as any} color="#22c55e" isPendingGate={false} isFailed={false} onClick={()=>{}}/>);
  expect(screen.queryByTestId("stacked-marker")).not.toBeInTheDocument();
  expect(screen.queryByRole("link", { name: /PR/i })).not.toBeInTheDocument();
});
