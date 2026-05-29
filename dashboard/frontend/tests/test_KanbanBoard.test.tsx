import { render, screen, fireEvent } from "@testing-library/react";
import { KanbanBoard } from "../src/components/KanbanBoard";
import { useSessionsStore } from "../src/stores/sessionsStore";
import * as api from "../src/api/client"; import { vi } from "vitest";
test("renders 7 columns", () => {
  render(<KanbanBoard/>);
  for (const s of ["interview","plan","review","execute","verify","document","pr"]) expect(screen.getAllByText((t)=>t.includes(s)).length).toBeGreaterThan(0);
});
test("review→execute on pending calls approveGate", async () => {
  useSessionsStore.setState({sessions:[{slug:"feat-x",repoName:"a",repoRoot:"/a",currentStage:"review",idea:"",phases:{},mtime:0,gates:{gate2_pre_execute:{state:"pending",source:null,reached_at:"",approved_at:null,approved_by:null}}} as any]});
  const spy = vi.spyOn(api,"approveGate").mockResolvedValue({approved:true,event_id:"e"} as any);
  render(<KanbanBoard/>);
  fireEvent(screen.getByTestId("kanban-board"), new CustomEvent("test-drag",{detail:{activeSlug:"feat-x",overStage:"execute"}}));
  await new Promise(r=>setTimeout(r,50));
  expect(spy).toHaveBeenCalledWith("feat-x","gate2_pre_execute");
});
test("renders Epic swimlane with flow view when phases present", () => {
  useSessionsStore.setState({sessions:[
    {slug:"epic-x",repoName:"a",repoRoot:"/a",currentStage:"review",idea:"E",phases:{},mtime:0,gates:{},kind:"epic",parentSlug:null,phaseIndex:null,dependsOn:[]},
    {slug:"epic-x-p1",repoName:"a",repoRoot:"/a",currentStage:"verify",idea:"",phases:{},mtime:0,gates:{},kind:"phase",parentSlug:"epic-x",phaseIndex:1,phaseLabel:"foundation",dependsOn:[]},
    {slug:"epic-x-p2",repoName:"a",repoRoot:"/a",currentStage:"execute",idea:"",phases:{},mtime:0,gates:{},kind:"phase",parentSlug:"epic-x",phaseIndex:2,phaseLabel:"api",dependsOn:[1]},
  ] as any});
  render(<KanbanBoard/>);
  expect(screen.getAllByTestId("epic-swimlane").length).toBeGreaterThan(0);
  expect(screen.getAllByTestId("phase-node").length).toBe(2);
});

test("non-gate drag rejected", async () => {
  useSessionsStore.setState({sessions:[{slug:"feat-z",repoName:"a",repoRoot:"/a",currentStage:"plan",idea:"",phases:{},mtime:0,gates:{}} as any]});
  const spy = vi.spyOn(api,"approveGate").mockResolvedValue({approved:true} as any);
  render(<KanbanBoard/>);
  fireEvent(screen.getByTestId("kanban-board"), new CustomEvent("test-drag",{detail:{activeSlug:"feat-z",overStage:"review"}}));
  await new Promise(r=>setTimeout(r,50));
  expect(spy).not.toHaveBeenCalled();
});
