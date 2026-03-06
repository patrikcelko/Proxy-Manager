import { defineConfig } from "vitest/config";
import path from "path";

export default defineConfig({
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "proxy_manager/static/ts"),
    },
  },
  test: {
    environment: "jsdom",
    include: ["tests/static/**/*.test.ts"],
    globals: true,
    setupFiles: ["tests/static/setup.ts"],
    restoreMocks: true,
  },
});
