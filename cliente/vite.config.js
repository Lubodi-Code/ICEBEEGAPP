import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  server: {
    // Respeta el puerto asignado por el entorno (preview/CI); 5173 por defecto.
    port: Number(process.env.PORT) || 5173,
  },
});
