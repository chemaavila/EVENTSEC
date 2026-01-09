const DEFAULT_API_BASE_URL = "http://localhost:8000";

export function resolveApiBase(): string {
  const rawValue = (import.meta.env.VITE_API_BASE_URL ?? "").trim();
  if (!rawValue) {
    return DEFAULT_API_BASE_URL;
  }

  if (/^https?:\/\//i.test(rawValue)) {
    return rawValue.replace(/\/$/, "");
  }

  console.warn(
    "[api] Invalid VITE_API_BASE_URL value, falling back to default",
    rawValue
  );
  return DEFAULT_API_BASE_URL;
}

export const API_BASE_URL = resolveApiBase().replace(/\/$/, "");

type ResolveWsOptions = {
  apiBaseUrl?: string;
  wsOverride?: string;
};

export function resolveWsUrl(path: string, options: ResolveWsOptions = {}): string {
  const rawOverride =
    (options.wsOverride ?? import.meta.env.VITE_THREATMAP_WS_URL ?? "").trim();
  if (rawOverride) {
    return rawOverride;
  }

  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const baseUrl =
    options.apiBaseUrl?.replace(/\/$/, "") || API_BASE_URL || DEFAULT_API_BASE_URL;

  try {
    const url = new URL(baseUrl);
    url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
    url.pathname = normalizedPath;
    url.search = "";
    url.hash = "";
    return url.toString();
  } catch (err) {
    console.warn("[ws] Failed to resolve WS URL, using fallback", err);
    const fallback = baseUrl.replace(/^http/i, "ws");
    return `${fallback.replace(/\/$/, "")}${normalizedPath}`;
  }
}

export const EMAIL_PROTECT_BASE_URL = (() => {
  const rawValue = (import.meta.env.VITE_EMAIL_PROTECT_BASE_URL ?? "").trim();
  if (rawValue) {
    return rawValue.replace(/\/$/, "");
  }
  if (typeof window !== "undefined" && window.location) {
    const { protocol, hostname } = window.location;
    return `${protocol}//${hostname}:8100`;
  }
  return "http://localhost:8100";
})();
