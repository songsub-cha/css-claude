import type {
  Session, Project, GateName, ArtifactName,
  StageName, SessionKind, Phase, PhaseNode, EpicFlow,
} from "../src/types";

test("Session type shape (with hierarchy fields)", () => {
  const s: Session = {
    slug: "x", idea: "y", repoRoot: "/r", repoName: "r",
    currentStage: "review", phases: {}, gates: {}, mtime: 0,
    kind: "phase", parentSlug: "epic-x", phaseIndex: 2, dependsOn: [1],
  };
  expect(s.slug).toBe("x");
  expect(s.currentStage).toBe("review");
  expect(s.phaseIndex).toBe(2);
});

test("EpicFlow + PhaseNode shape", () => {
  const node: PhaseNode = {
    phase_index: 1, phase_label: "foundation",
    current_stage: "execute", pr_status: "open",
    pr_url: "https://gh/x/y/pull/3",
  };
  const flow: EpicFlow = {
    epic: { slug: "epic-x", label: "the epic" },
    nodes: [node],
    edges: [{ from: 1, to: 2 }],
  };
  expect(flow.nodes[0].phase_index).toBe(1);
  expect(flow.edges[0]).toEqual({ from: 1, to: 2 });
});

test("Phase shape", () => {
  const p: Phase = {
    slug: "epic-x-p2", parentSlug: "epic-x", phaseIndex: 2,
    phaseLabel: "api", dependsOn: [1], currentStage: "plan",
  };
  expect(p.phaseIndex).toBe(2);
});

test("StageName + SessionKind are usable", () => {
  const stage: StageName = "verify";
  const kind: SessionKind = "epic";
  expect([stage, kind]).toEqual(["verify", "epic"]);
});
