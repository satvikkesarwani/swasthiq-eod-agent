import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    coverage: {
      provider: "v8",
      reporter: ["text", "html"],
      thresholds: {
        statements: 85,
        lines: 85,
        functions: 80,
        branches: 80,
      },
      exclude: [
        "eslint.config.js",
        "vite.config.ts",
        "vitest.config.ts",
        "src/api/generated/**",
        "src/api/types.ts",
        "src/app/router.tsx",
        "src/main.tsx",
        "src/test/**",
        "src/vite-env.d.ts",
        "**/*.d.ts"
      ],
    },
  },
});
