import type { Config } from "tailwindcss";
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0e1018",
        panel: "#161922",
        card: "#222633"
      }
    }
  }
} satisfies Config;
