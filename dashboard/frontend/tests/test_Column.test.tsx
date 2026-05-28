import { render, screen } from "@testing-library/react";
import { DndContext } from "@dnd-kit/core";
import { Column } from "../src/components/Column";

test("review column shows Gate 2 label when pending", () => {
  render(<DndContext><Column stage="review" hasPendingGate={true}>{null}</Column></DndContext>);
  expect(screen.getByText(/Gate 2/)).toBeInTheDocument();
});
