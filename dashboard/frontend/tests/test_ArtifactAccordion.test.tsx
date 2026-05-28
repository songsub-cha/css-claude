import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { setupServer } from "msw/node"; import { http, HttpResponse } from "msw";
import { ArtifactAccordion } from "../src/components/ArtifactAccordion";
const server = setupServer(http.get("/api/sessions/feat-x/artifacts/spec", ()=>HttpResponse.json({name:"spec",content_md:"# spec body",mtime:1})));
beforeAll(()=>server.listen()); afterAll(()=>server.close());
test("expand fetches + renders markdown", async () => {
  render(<ArtifactAccordion slug="feat-x" artifacts={[{name:"spec",path:"/p",size:1,mtime:1} as any]}/>);
  fireEvent.click(screen.getByText("spec"));
  await waitFor(()=>expect(screen.getByText("spec body")).toBeInTheDocument());
});
