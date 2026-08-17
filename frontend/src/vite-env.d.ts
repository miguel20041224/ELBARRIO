/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** URL absoluta de la API, incluyendo el prefijo /api. Obligatoria en producción. */
  readonly VITE_API_URL?: string;
  /** Tiempo máximo por petición en milisegundos. Por defecto 60000. */
  readonly VITE_API_TIMEOUT_MS?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
