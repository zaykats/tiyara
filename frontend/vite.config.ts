import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";

// https://vitejs.dev/config/
export default defineConfig({
  server: {
    host: "::",
    port: 8080,
    proxy: {
      "^/auth/(signin|signup|refresh|me)": { target: "http://localhost:8000", changeOrigin: true },
      "^/sessions": { target: "http://localhost:8000", changeOrigin: true },
      "^/documents": { target: "http://localhost:8000", changeOrigin: true },
      "^/chat": { target: "http://localhost:8000", changeOrigin: true },
    },
  },
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
    dedupe: ["react", "react-dom", "react/jsx-runtime", "react/jsx-dev-runtime"],
  },
});
