import type { VercelRequest, VercelResponse } from "@vercel/node";

const BACKEND_BASE_URL =
  process.env.BACKEND_BASE_URL ||
  process.env.API_BASE_URL ||
  process.env.BACKEND_URL;

function toStringArray(v: unknown): string[] {
  if (Array.isArray(v)) return v.filter((x): x is string => typeof x === "string");
  if (typeof v === "string") return [v];
  return [];
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (!BACKEND_BASE_URL) {
    res
      .status(500)
      .json({ error: "Missing BACKEND_BASE_URL (or API_BASE_URL/BACKEND_URL) in Vercel env vars" });
    return;
  }

  const pathParts = toStringArray(req.query.path);
  const base = BACKEND_BASE_URL.endsWith("/") ? BACKEND_BASE_URL : `${BACKEND_BASE_URL}/`;
  const upstreamUrl = new URL(pathParts.join("/"), base);

  // forward query params except "path"
  for (const [k, v] of Object.entries(req.query)) {
    if (k === "path") continue;
    if (Array.isArray(v)) v.forEach((vv) => typeof vv === "string" && upstreamUrl.searchParams.append(k, vv));
    else if (typeof v === "string") upstreamUrl.searchParams.set(k, v);
  }

  const headers = new Headers();
  for (const [k, v] of Object.entries(req.headers)) {
    if (v == null) continue;
    if (Array.isArray(v)) headers.set(k, v.join(","));
    else headers.set(k, v);
  }
  headers.delete("host");

  const method = (req.method || "GET").toUpperCase();
  const hasBody = !["GET", "HEAD"].includes(method);

  let body: BodyInit | undefined;
  if (hasBody && req.body != null) {
    if (typeof req.body === "string") {
      body = req.body;
    } else {
      body = JSON.stringify(req.body);
      if (!headers.has("content-type")) headers.set("content-type", "application/json");
    }
  }

  const upstreamResp = await fetch(upstreamUrl.toString(), {
    method,
    headers,
    body: hasBody ? body : undefined,
    redirect: "manual",
  });

  res.status(upstreamResp.status);

  upstreamResp.headers.forEach((value, key) => {
    const k = key.toLowerCase();
    if (k === "transfer-encoding") return;
    res.setHeader(key, value);
  });

  const buf = Buffer.from(await upstreamResp.arrayBuffer());
  res.send(buf);
}
