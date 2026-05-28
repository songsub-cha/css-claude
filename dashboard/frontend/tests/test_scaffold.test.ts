import { test, expect } from "vitest";
import { existsSync } from "fs";
import { join } from "path";

const root = join(__dirname, "..");
test("package.json has required dependencies", () => {
  const pkg = require(join(root, "package.json"));
  for (const dep of ["react", "react-dom", "@dnd-kit/core", "@dnd-kit/sortable", "zustand", "react-markdown", "rehype-sanitize", "rehype-highlight"]) {
    expect(pkg.dependencies[dep]).toBeDefined();
  }
  for (const dev of ["vite", "vitest", "@vitejs/plugin-react", "tailwindcss", "@testing-library/react", "msw", "@playwright/test"]) {
    expect(pkg.devDependencies[dev]).toBeDefined();
  }
});
test("index.html and main.tsx exist", () => {
  expect(existsSync(join(root, "index.html"))).toBe(true);
  expect(existsSync(join(root, "src/main.tsx"))).toBe(true);
});
