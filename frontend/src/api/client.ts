/**
 * Resolución de la URL base de la API.
 *
 * Nunca se cae a una ruta relativa (`/api`): eso funcionaba en desarrollo sólo
 * gracias al proxy de Vite y, en un hosting estático como Vercel, resolvía
 * contra el propio dominio del frontend, donde no hay ninguna API. La URL debe
 * ser siempre explícita vía VITE_API_URL.
 */
function resolveBaseUrl(): string {
  const raw = import.meta.env.VITE_API_URL;

  if (typeof raw === "string" && raw.trim() !== "") {
    return raw.trim().replace(/\/+$/, "");
  }

  const message =
    "VITE_API_URL no está definida. El frontend no sabe a qué backend hablar. " +
    "En desarrollo se define en frontend/.env.development; en Vercel, como " +
    "variable de entorno del proyecto (ver docs/DEPLOY.md).";

  if (import.meta.env.PROD) {
    // En producción fallar rápido y visible es mejor que emitir peticiones
    // silenciosas contra el dominio equivocado.
    throw new Error(message);
  }

  console.warn(`[elbarrio] ${message} Usando http://localhost:8000/api.`);
  return "http://localhost:8000/api";
}

export const API_BASE_URL = resolveBaseUrl();

/** Margen amplio: un servicio dormido en el plan gratuito de Render puede tardar ~50 s en despertar. */
const DEFAULT_TIMEOUT_MS = Number(import.meta.env.VITE_API_TIMEOUT_MS ?? 60000);

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  timeoutMs?: number;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public payload?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/** Fallo de transporte: el servidor no respondió (caído, CORS, DNS, timeout). */
export class NetworkError extends Error {
  constructor(
    message: string,
    public cause?: unknown,
  ) {
    super(message);
    this.name = "NetworkError";
  }
}

export async function request<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { body, headers, timeoutMs = DEFAULT_TIMEOUT_MS, signal, ...rest } = options;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  if (signal) {
    signal.addEventListener("abort", () => controller.abort(), { once: true });
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...rest,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...headers,
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch (err) {
    if (controller.signal.aborted) {
      throw new NetworkError(
        `El servidor no respondió en ${Math.round(timeoutMs / 1000)} s. ` +
          "Puede estar despertando; probá de nuevo en unos segundos.",
        err,
      );
    }
    throw new NetworkError(
      `No se pudo conectar con el servidor (${API_BASE_URL}). ` +
        "Verificá tu conexión o que el backend esté disponible.",
      err,
    );
  } finally {
    clearTimeout(timer);
  }

  const isJson = response.headers
    .get("content-type")
    ?.includes("application/json");
  const payload = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    const message =
      isJson && typeof payload === "object" && payload !== null && "detail" in payload
        ? String((payload as { detail: unknown }).detail)
        : response.statusText || `HTTP ${response.status}`;
    throw new ApiError(response.status, message, payload);
  }

  return payload as T;
}

export const api = {
  get: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "GET" }),
  post: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "POST", body }),
  patch: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "PATCH", body }),
  delete: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "DELETE" }),
};
