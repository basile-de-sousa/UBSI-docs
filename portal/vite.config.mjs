import { defineConfig } from "vite";

export default defineConfig({
  base: "/static/",
  build: {
    outDir: "static-built",
    emptyOutDir: true,
    manifest: true,
    sourcemap: false,
    rollupOptions: { input: "frontend/main.ts" },
  },
});
