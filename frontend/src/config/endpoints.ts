// frontend/src/config/endpoints.ts

// En producción (Vercel) queremos SIEMPRE /api para usar el proxy (sin CORS).
// En local puedes sobreescribir con VITE_API_BASE_URL=http://localhost:8000
const DEFAULT_API_BASE_URL =
  (import.meta.env.MODE === "development" ? "http://localhost:8000" : "/api");

function isVercelHostname(hostname: string | undefined): boolean {
  return Boolean(hostname && hostname.endsWith(".vercel.app"));
function resolveWithOrigin(path: string): string {
  if (typeof window !== "undefined" && window.location?.origin) {
    return `${window.location.origin}${path}`.replace(/\/$/, "");
  }
  return path.replace(/\/$/, "");
}

export function resolveApiBase(): string {
  const raw = (import.meta.env.VITE_API_URL ?? import.meta.env.VITE_API_BASE_URL ?? "").trim();
  const v = raw || DEFAULT_API_BASE_URL;
  const isBrowser = typeof window !== "undefined" && window.location;
  const origin = isBrowser ? window.location.origin : "";
  const hostname = isBrowser ? window.location.hostname : "";
  const onVercel = isVercelHostname(hostname);
  if (!raw && import.meta.env.MODE !== "development") {
    console.warn("[api] VITE_API_URL not set; using default", {
      fallback: DEFAULT_API_BASE_URL,
    });
  }
  if (onVercel && v !== "/api") {
    if (import.meta.env.VITE_UI_DEBUG === "true") {
      console.debug("[api] Forcing /api on Vercel", {
        provided: v,
        fallback: "/api",
      });
    }
    return "/api";
  }

  // URL absoluta
  if (/^https?:\/\//i.test(v)) {

  // URL absoluta
  if (/^https?:\/\//i.test(v)) {
    if (onVercel) {
      if (import.meta.env.VITE_UI_DEBUG === "true") {
        console.debug("[api] Override absolute baseUrl on Vercel", {
          provided: v,
          origin,
          fallback: "/api",
        });
      }
      return resolveWithOrigin("/api");
    }
    return v.replace(/\/$/, "");
  }

  // Path relativo: "/api"
  if (v.startsWith("/")) {
    return v.replace(/\/$/, "");
  }

  console.warn("[api] Invalid VITE_API_URL, fallback:", v);
    return resolveWithOrigin(v);
  }

  console.warn("[api] Invalid VITE_API_BASE_URL, fallback:", v);
  if (/^https?:\/\//i.test(DEFAULT_API_BASE_URL)) {
    return DEFAULT_API_BASE_URL.replace(/\/$/, "");
  }
  const fallbackPath = DEFAULT_API_BASE_URL.startsWith("/")
    ? DEFAULT_API_BASE_URL
    : `/${DEFAULT_API_BASE_URL}`;
  const resolved = fallbackPath.replace(/\/$/, "");
  if (import.meta.env.VITE_UI_DEBUG === "true" && isBrowser) {
    console.debug("[api] resolved baseUrl", { resolved });
  }
  return resolved;
  return resolveWithOrigin(fallbackPath);
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
