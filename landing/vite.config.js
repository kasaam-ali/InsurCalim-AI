import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server runs on 5173; the Streamlit dashboard runs separately on 8501.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
  },
});
