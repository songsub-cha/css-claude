import { render, screen, fireEvent } from "@testing-library/react";
import { KanbanBoard } from "../src/components/KanbanBoard";
import { useSessionsStore } from "../src/stores/sessionsStore";
import * as api from "../src/api/client"; import { vi } from "vitest";
test("renders 7 columns", () => {
  render(<KanbanBoard/>);
  for (const s of ["interview","plan","review","execute","verify","document","pr"]) expect(screen.getAllByText((t)=>t.includes(s)).length).toBeGreaterThan(0);
});
test("review→execute on pending calls approveGate", async () => {
  useSessionsStore.setState({sessions:[{slug:"feat-x",repoName:"a",repoRoot:"/a",currentPhase:"review",idea:"",phases:{},mtime:0,gates:{gate2_pre_execute:{state:"pending",source:null,reached_at:"",approved_at:null,approved_by:null}}} as any]});
  const spy = vi.spyOn(api,"approveGate").mockResolvedValue({approved:true,event_id:"e"} as any);
  render(<KanbanBoard/>);
  fireEvent(screen.getByTestId("kanban-board"), new CustomEvent("test-drag",{detail:{activeSlug:"feat-x",overStage:"execute"}}));
  await new Promise(r=>setTimeout(r,50));
  expect(spy).toHaveBeenCalledWith("feat-x","gate2_pre_execute");
});
test("non-gate drag rejected", async () => {
  useSessionsStore.setState({sessions:[{slug:"feat-z",repoName:"a",repoRoot:"/a",currentPhase:"plan",idea:"",phases:{},mtime:0,gates:{}} as any]});
  const spy = vi.spyOn(api,"approveGate").mockResolvedValue({approved:true} as any);
  render(<KanbanBoard/>);
  fireEvent(screen.getByTestId("kanban-board"), new CustomEvent("test-drag",{detail:{activeSlug:"feat-z",overStage:"review"}}));
  await new Promise(r=>setTimeout(r,50));
  expect(spy).not.toHaveBeenCalled();
});
