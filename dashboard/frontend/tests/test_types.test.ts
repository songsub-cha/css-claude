import type { Session, Project, GateName, ArtifactName } from "../src/types";

test("Session type shape", () => {
  const s: Session = {
    slug: "x", idea: "y", repoRoot: "/r", repoName: "r",
    currentPhase: "review", phases: {}, gates: {}, mtime: 0
  };
  expect(s.slug).toBe("x");
});
