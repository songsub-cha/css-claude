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
