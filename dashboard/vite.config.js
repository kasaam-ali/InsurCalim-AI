import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dashboard dev server on 5174. /api is proxied to the Starlette API on 8000 so
// the browser talks same-origin in development (no CORS surprises).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    host: true,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
