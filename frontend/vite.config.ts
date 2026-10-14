import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The backend runs on 127.0.0.1:8000 (see ../backend/run.ps1). In dev, Vite
// proxies API paths there so the app can use same-origin relative URLs and the
// backend's CORS config never comes into play.
const API_TARGET = process.env.VITE_API_PROXY ?? "http://127.0.0.1:8000";

const PROXY_PATHS = [
  "/health",
  "/entities",
  "/accounts",
  "/payments",
  "/docs",
  "/openapi.json",
];

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: Object.fromEntries(
      PROXY_PATHS.map((p) => [p, { target: API_TARGET, changeOrigin: true }]),
    ),
  },
});
