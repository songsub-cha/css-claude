import { describe, it, expect } from "vitest";
import { add } from "./index";

describe("add", () => {
  it("returns the sum of two numbers", () => {
    expect(add(2, 3)).toBe(5);
  });
});
