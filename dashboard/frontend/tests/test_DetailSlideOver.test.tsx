import { render, screen } from "@testing-library/react"; import { vi } from "vitest";
import { DetailSlideOver } from "../src/components/DetailSlideOver";
test("renders + closes", () => {
  const onClose = vi.fn();
  render(<DetailSlideOver session={{slug:"feat-x",idea:"do thing",repoName:"alpha",repoRoot:"/a",currentPhase:"review",phases:{interview:{status:"completed"},plan:{status:"completed"},review:{status:"in_progress"}},gates:{},mtime:0} as any} color="#22c55e" artifacts={[]} onClose={onClose} onRetry={()=>{}}/>);
  expect(screen.getByText("feat-x")).toBeInTheDocument();
  expect(screen.getByText("do thing")).toBeInTheDocument();
  screen.getByText("✕").click();
  expect(onClose).toHaveBeenCalled();
});
