function defaultApiBase(): string {
  if (typeof window !== "undefined" && window.location) {
    const { protocol, hostname } = window.location;
    return `${protocol}//${hostname}:8000`;
  }
  return "http://localhost:8000";
}

export function resolveApiBase(): string {
  const rawValue = (import.meta.env.VITE_API_BASE_URL ?? "").trim();
  const fallback = defaultApiBase();

  if (!rawValue) {
    return fallback;
  }

  if (/^https?:\/\//i.test(rawValue)) {
    return rawValue;
  }

  if (typeof window !== "undefined" && rawValue.startsWith("//")) {
    return `${window.location.protocol}${rawValue}`;
  }

  try {
    const base = typeof window !== "undefined" ? window.location.origin : fallback;
    const resolved = new URL(rawValue, base);
    return resolved.origin + resolved.pathname.replace(/\/$/, "");
  } catch (err) {
    console.warn(
      "[api] Invalid VITE_API_BASE_URL value, falling back to default",
      rawValue,
      err
    );
    return fallback;
  }
}

export const API_BASE_URL = resolveApiBase().replace(/\/$/, "");

export function resolveWsUrl(path: string): string {
  const rawOverride = (import.meta.env.VITE_THREATMAP_WS_URL ?? "").trim();
  if (rawOverride) {
    return rawOverride;
  }

  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const baseUrl = API_BASE_URL || defaultApiBase();

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
