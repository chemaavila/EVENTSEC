type LocationLike = Pick<Location, "protocol" | "hostname" | "origin">;

function defaultApiBase(location?: LocationLike): string {
  const target = location ?? (typeof window !== "undefined" ? window.location : undefined);
  if (target) {
    const { protocol, hostname } = target;
    return `${protocol}//${hostname}:8000`;
  }
  return "http://localhost:8000";
}

export function resolveApiBase(location?: LocationLike): string {
  const rawValue = (import.meta.env.VITE_API_BASE_URL ?? "").trim();
  const resolvedLocation =
    location ?? (typeof window !== "undefined" ? window.location : undefined);
  const fallback = defaultApiBase(resolvedLocation);

  if (!rawValue) {
    return fallback;
  }

  if (/^https?:\/\//i.test(rawValue)) {
    return rawValue;
  }

  if (resolvedLocation && rawValue.startsWith("//")) {
    return `${resolvedLocation.protocol}${rawValue}`;
  }

  try {
    const base = resolvedLocation?.origin ?? fallback;
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

type ResolveWsOptions = {
  apiBaseUrl?: string;
  wsOverride?: string;
  location?: LocationLike;
};

export function resolveWsUrl(path: string, options: ResolveWsOptions = {}): string {
  const rawOverride =
    (options.wsOverride ?? import.meta.env.VITE_THREATMAP_WS_URL ?? "").trim();
  if (rawOverride) {
    return rawOverride;
  }

  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const baseUrl =
    options.apiBaseUrl?.replace(/\/$/, "") ||
    API_BASE_URL ||
    defaultApiBase(options.location);

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
