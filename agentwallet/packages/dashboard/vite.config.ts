import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Default to the hosted devnet API; override with VITE_API_PROXY
// when running the full local stack (e.g. VITE_API_PROXY=http://localhost:8000).
const API_TARGET =
  process.env.VITE_API_PROXY || "https://api-production-6421a.up.railway.app";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: "0.0.0.0",
    proxy: {
      "/api": {
        target: API_TARGET,
        changeOrigin: true,
        secure: false,
        // Dashboard calls /api/v1/...; the API mounts routes at /v1/...
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
  build: {
    outDir: "dist",
    sourcemap: true,
  },
});
