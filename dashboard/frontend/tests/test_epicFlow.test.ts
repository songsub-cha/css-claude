import { groupByEpic, toEpicFlow } from "../src/lib/epicFlow";
import type { Session } from "../src/types";

function sess(slug: string, over: Partial<Session> = {}): Session {
  return {
    slug, idea: "", repoRoot: "/r", repoName: "r",
    currentStage: "execute", phases: {}, gates: {}, mtime: 0,
    kind: "epic", parentSlug: null, phaseIndex: null, dependsOn: [],
    ...over,
  };
}

const phase = (slug: string, idx: number, deps: number[], over: Partial<Session> = {}) =>
  sess(slug, { kind: "phase", parentSlug: "epic-x", phaseIndex: idx, dependsOn: deps, ...over });

test("groupByEpic groups phases under epic, ordered by phaseIndex", () => {
  const groups = groupByEpic([
    sess("epic-x", { kind: "epic", idea: "the epic" }),
    phase("epic-x-p2", 2, [1]),
    phase("epic-x-p1", 1, []),
  ]);
  expect(groups["epic-x"].epic?.slug).toBe("epic-x");
  expect(groups["epic-x"].phases.map(p => p.phaseIndex)).toEqual([1, 2]);
});

test("groupByEpic: legacy session is its own group", () => {
  const groups = groupByEpic([sess("old", { kind: "epic" })]);
  expect(groups["old"].phases).toEqual([]);
});

test("toEpicFlow builds nodes + edges + open PR", () => {
  const g = groupByEpic([
    sess("epic-x", { kind: "epic", idea: "E" }),
    phase("epic-x-p1", 1, [], {
      currentStage: "verify",
      phases: { pr: { status: "completed", artifact: "https://gh/x/pull/3" } },
    }),
    phase("epic-x-p2", 2, [1], { currentStage: "execute" }),
  ])["epic-x"];
  const flow = toEpicFlow(g);
  expect(flow.epic).toEqual({ slug: "epic-x", label: "E" });
  expect(flow.nodes.map(n => n.phase_index)).toEqual([1, 2]);
  expect(flow.nodes[0].pr_status).toBe("open");
  expect(flow.nodes[0].pr_url).toBe("https://gh/x/pull/3");
  expect(flow.nodes[0].current_stage).toBe("verify");
  expect(flow.edges).toEqual([{ from: 1, to: 2 }]);
});

test("toEpicFlow: legacy single-phase epic -> one node, no edges", () => {
  const g = groupByEpic([sess("old", { kind: "epic", currentStage: "plan" })])["old"];
  const flow = toEpicFlow(g);
  expect(flow.nodes).toHaveLength(1);
  expect(flow.nodes[0].phase_index).toBe(1);
  expect(flow.edges).toEqual([]);
});
