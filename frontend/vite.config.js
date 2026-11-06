import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// Em desenvolvimento (npm run dev), /api é repassado ao backend local.
// No container, quem faz esse repasse é o nginx (nginx.conf).
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        rewrite: (caminho) => caminho.replace(/^\/api/, ""),
      },
    },
  },
});
