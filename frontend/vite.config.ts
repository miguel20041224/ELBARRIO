import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, __dirname, "VITE_");

  // Un build sin VITE_API_URL genera un bundle que revienta en el navegador del
  // usuario. Es preferible romper aquí, donde el error sale en los logs de
  // Vercel y el despliegue anterior sigue en pie.
  if (command === "build" && !env.VITE_API_URL) {
    throw new Error(
      "Falta VITE_API_URL. Definila como variable de entorno del proyecto en " +
        "Vercel (o en frontend/.env.production para un build local). " +
        "Ejemplo: https://elbarrio-api.onrender.com/api — ver docs/DEPLOY.md",
    );
  }

  return {
    plugins: [react()],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    // Sin proxy a propósito: el frontend habla con el backend por su URL absoluta
    // (VITE_API_URL) igual en desarrollo que en producción. Un proxy aquí haría que
    // las peticiones fueran del mismo origen en dev, ocultando los errores de CORS
    // hasta el despliegue.
    server: {
      port: 5173,
    },
    preview: {
      port: 4173,
    },
  };
});
