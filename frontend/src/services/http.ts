export type ApiErrorKind = "network" | "server" | "parse";

export interface ApiError extends Error {
  status?: number;
  kind?: ApiErrorKind;
  requestId?: string;
  bodySnippet?: string;
}

export type ApiFetchOptions<TBody> = {
  baseUrl: string;
  path: string;
  method?: string;
  body?: TBody;
  query?: Record<string, string | number | boolean | undefined>;
  signal?: AbortSignal;
  debugLabel?: string;
};

const debugEnabled = (import.meta.env.VITE_UI_DEBUG ?? "false") === "true";
const accessTokenKey = "eventsec_access_token";

function getStoredAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(accessTokenKey);
  } catch (err) {
    return null;
  }
}

function buildHeaders(method: string, hasBody: boolean): HeadersInit {
  const headers: Record<string, string> = {
    Accept: "application/json",
  };
  if (hasBody && method !== "GET") {
    headers["Content-Type"] = "application/json";
  }
  const token = getStoredAccessToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

function createRequestId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `req-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function normalizePath(path: string): string {
  return path.startsWith("/") ? path : `/${path}`;
}

function buildApiUrl(baseUrl: string, path: string): URL {
  const normalizedPath = normalizePath(path);
  const trimmedBase = baseUrl.replace(/\/$/, "");

  if (/^https?:\/\//i.test(trimmedBase)) {
    return new URL(`${trimmedBase}${normalizedPath}`);
  }

  if (trimmedBase.startsWith("/")) {
    const origin =
      typeof window !== "undefined" && window.location?.origin
        ? window.location.origin
        : "http://localhost";
    return new URL(`${trimmedBase}${normalizedPath}`, origin);
  }

  const fallbackBase =
    typeof window !== "undefined" && window.location?.origin
      ? window.location.origin
      : "http://localhost";
  return new URL(`${trimmedBase}${normalizedPath}`, fallbackBase);
}

export function toQueryParams<T extends object>(
  obj: T
): Record<string, string | number | boolean | undefined> {
  return Object.entries(obj as Record<string, unknown>).reduce<
    Record<string, string | number | boolean | undefined>
  >((acc, [key, value]) => {
    if (value === undefined || value === null) {
      acc[key] = undefined;
    } else if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
      acc[key] = value;
    } else {
      acc[key] = String(value);
    }
    return acc;
  }, {});
}

export async function handleResponse<T>(res: Response, requestId: string): Promise<T> {
  if (res.status === 204 || res.status === 205) {
    return null as T;
  }

  const contentType = res.headers.get("content-type") ?? "";
  const isJson = contentType.includes("application/json");
  const text = await res.text().catch(() => "");
  const hasBody = text.trim().length > 0;

  if (!res.ok) {
    let errorMessage = `API error ${res.status}`;
    const bodySnippet = text.slice(0, 500);
    if (hasBody && isJson) {
      try {
        const json = JSON.parse(text);
        errorMessage = json.detail || json.message || errorMessage;
      } catch (err) {
        errorMessage = `${errorMessage} (invalid JSON body)`;
      }
    } else if (hasBody) {
      errorMessage = text;
    }
    const error = new Error(errorMessage) as ApiError;
    error.status = res.status;
    error.kind = "server";
    error.requestId = requestId;
    error.bodySnippet = bodySnippet;
    throw error;
  }

  if (!hasBody) {
    return null as T;
  }

  if (isJson) {
    try {
      return JSON.parse(text) as T;
    } catch (err) {
      const error = new Error("Failed to parse JSON response") as ApiError;
      error.kind = "parse";
      error.requestId = requestId;
      error.bodySnippet = text.slice(0, 500);
      throw error;
    }
  }

  return text as T;
}

export async function apiFetch<TResponse, TBody = unknown>({
  baseUrl,
  path,
  method = "GET",
  body,
  query,
  signal,
  debugLabel,
}: ApiFetchOptions<TBody>): Promise<TResponse> {
  const url = buildApiUrl(baseUrl, path);
  if (query) {
    Object.entries(query).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        url.searchParams.set(key, String(value));
      }
    });
  }

  const requestId = createRequestId();
  const headers = buildHeaders(method, body !== undefined);
  const start = performance.now();

  try {
    if (debugEnabled && debugLabel === "login") {
      console.debug("[api] login url", { url: url.toString() });
    }
    const res = await fetch(url.toString(), {
      method,
      headers: {
        ...headers,
        "X-Request-Id": requestId,
      },
      credentials: "include",
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal,
    });
    const durationMs = performance.now() - start;
    if (debugEnabled) {
      console.debug("[api] response", {
        requestId,
        method,
        url: url.toString(),
        status: res.status,
        durationMs: Math.round(durationMs),
      });
    }
    return await handleResponse<TResponse>(res, requestId);
  } catch (err) {
    const durationMs = performance.now() - start;
    if (debugEnabled) {
      console.debug("[api] error", {
        requestId,
        method,
        url: url.toString(),
        durationMs: Math.round(durationMs),
        error: err,
      });
    }
    if (err instanceof Error) {
      const apiError = err as ApiError;
      apiError.kind = apiError.kind ?? "network";
      apiError.requestId = apiError.requestId ?? requestId;
      throw apiError;
    }
    throw err;
  }
}
