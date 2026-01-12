// frontend/src/config/endpoints.ts

// En producción queremos SIEMPRE /api para usar el proxy (sin CORS).
// En local puedes sobreescribir con VITE_API_BASE_URL=http://localhost:8000
const DEFAULT_API_BASE_URL =
  import.meta.env.MODE === "development" ? "http://localhost:8000" : "/api";

function normalizeApiBase(value: string): string {
  const v = value.trim();
  if (!v) return "";

  // URL absoluta
  if (/^https?:\/\//i.test(v)) {
    return v.replace(/\/$/, "");
  }

  // Path relativo: "/api"
  if (v.startsWith("/")) {
    return v.replace(/\/$/, "");
  }

  const normalized = `/${v}`.replace(/\/$/, "");
  return normalized;
}

export function resolveApiBase(): string {
  const raw = (import.meta.env.VITE_API_URL ?? import.meta.env.VITE_API_BASE_URL ?? "").trim();
  if (raw) {
    return normalizeApiBase(raw);
  }

  if (import.meta.env.PROD) {
    return "/api";
  }

  const fallback = normalizeApiBase(DEFAULT_API_BASE_URL);
  if (import.meta.env.VITE_UI_DEBUG === "true") {
    console.debug("[api] resolved baseUrl", { fallback });
  }
  return fallback || "/api";
}

export const API_BASE_URL = resolveApiBase().replace(/\/$/, "");

if (import.meta.env.VITE_UI_DEBUG === "true" && typeof window !== "undefined") {
  console.debug("[api] baseUrl resolved", {
    apiBaseUrl: API_BASE_URL,
    origin: window.location.origin,
  });
}

type ResolveWsOptions = {
  apiBaseUrl?: string;
  wsOverride?: string;
};

export function resolveWsUrl(path: string, options: ResolveWsOptions = {}): string {
  const rawOverride =
    (options.wsOverride ?? import.meta.env.VITE_THREATMAP_WS_URL ?? "").trim();
  if (rawOverride) return rawOverride;

  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const baseUrl = (options.apiBaseUrl?.replace(/\/$/, "") || API_BASE_URL).trim();

  try {
    const url = new URL(baseUrl);
    url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
    url.pathname = normalizedPath;
    url.search = "";
    url.hash = "";
    return url.toString();
  } catch (err) {
    // Si baseUrl es relativo (ej: "/api"), construimos desde el origin:
    if (typeof window !== "undefined" && window.location?.origin) {
      const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
      return `${proto}//${window.location.host}${normalizedPath}`;
    }
    // último fallback
    const fallback = baseUrl.replace(/^http/i, "ws");
    return `${fallback.replace(/\/$/, "")}${normalizedPath}`;
  }
}

export const EMAIL_PROTECT_BASE_URL = (() => {
  const rawValue = (import.meta.env.VITE_EMAIL_PROTECT_BASE_URL ?? "").trim();
  if (rawValue) return rawValue.replace(/\/$/, "");

  if (typeof window !== "undefined" && window.location) {
    const { protocol, hostname } = window.location;
    return `${protocol}//${hostname}:8100`;
  }

  return "http://localhost:8100";
})();
