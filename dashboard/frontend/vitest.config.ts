import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./tests/setup.ts"],
    // Playwright E2E specs live under tests/e2e and must not be collected by vitest
    exclude: ["**/node_modules/**", "**/tests/e2e/**"]
  }
});
