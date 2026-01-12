import type { VercelRequest, VercelResponse } from "@vercel/node";

const HOP_BY_HOP_HEADERS = new Set([
  "connection",
  "host",
  "content-length",
  "transfer-encoding",
]);

function collectHeaders(req: VercelRequest): Headers {
  const headers = new Headers();
  for (const [key, value] of Object.entries(req.headers)) {
    const lowerKey = key.toLowerCase();
    if (HOP_BY_HOP_HEADERS.has(lowerKey)) continue;
    if (lowerKey.startsWith("x-vercel-")) continue;
    if (typeof value === "undefined") continue;
    if (Array.isArray(value)) {
      for (const entry of value) {
        headers.append(key, entry);
      }
    } else {
      headers.set(key, value);
    }
  }

  const forwardedHost =
    req.headers["x-forwarded-host"] ?? req.headers["host"] ?? "";
  if (typeof forwardedHost === "string" && forwardedHost) {
    headers.set("x-forwarded-host", forwardedHost);
  }
  headers.set("x-forwarded-proto", "https");

  return headers;
}

async function readRawBody(req: VercelRequest): Promise<Buffer | undefined> {
  if (req.method === "GET" || req.method === "HEAD") return undefined;
  return new Promise((resolve, reject) => {
    const chunks: Buffer[] = [];
    req.on("data", (chunk) => {
      chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
    });
    req.on("end", () => {
      resolve(chunks.length ? Buffer.concat(chunks) : undefined);
    });
    req.on("error", reject);
  });
}

function buildTargetUrl(req: VercelRequest, baseUrl: string): string {
  const pathParts = Array.isArray(req.query.path)
    ? req.query.path
    : req.query.path
    ? [req.query.path]
    : [];
  const normalizedBase = baseUrl.replace(/\/$/, "");
  const normalizedPath = pathParts.map((part) => String(part)).join("/");
  const url = new URL(`${normalizedBase}/${normalizedPath}`.replace(/\/+$/, ""));
  for (const [key, value] of Object.entries(req.query)) {
    if (key === "path" || typeof value === "undefined") continue;
    if (Array.isArray(value)) {
      for (const entry of value) {
        url.searchParams.append(key, entry);
      }
    } else {
      url.searchParams.append(key, String(value));
    }
  }
  return url.toString();
}

export const config = {
  api: {
    bodyParser: false,
  },
};

export default async function handler(
  req: VercelRequest,
  res: VercelResponse
): Promise<void> {
  if (req.method === "OPTIONS") {
    res.setHeader("Allow", "GET,POST,PUT,PATCH,DELETE,OPTIONS,HEAD");
    res.status(204).end();
    return;
  }

  const baseUrl = process.env.RENDER_BACKEND_URL?.trim();
  if (!baseUrl) {
    res.status(500).json({ error: "RENDER_BACKEND_URL is not set" });
    return;
  }

  const targetUrl = buildTargetUrl(req, baseUrl);
  const headers = collectHeaders(req);
  const body = await readRawBody(req);

  const upstreamResponse = await fetch(targetUrl, {
    method: req.method,
    headers,
    body,
    redirect: "manual",
  });

  const setCookies =
    typeof upstreamResponse.headers.getSetCookie === "function"
      ? upstreamResponse.headers.getSetCookie()
      : undefined;

  upstreamResponse.headers.forEach((value, key) => {
    if (key.toLowerCase() === "set-cookie") return;
    res.setHeader(key, value);
  });

  if (setCookies && setCookies.length > 0) {
    res.setHeader("set-cookie", setCookies);
  } else {
    const fallbackCookie = upstreamResponse.headers.get("set-cookie");
    if (fallbackCookie) {
      res.setHeader("set-cookie", fallbackCookie);
    }
  }

  res.status(upstreamResponse.status);
  const responseBuffer = Buffer.from(await upstreamResponse.arrayBuffer());
  res.send(responseBuffer);
}
