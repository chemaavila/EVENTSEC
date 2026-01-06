import { describe, expect, it } from "vitest";
import { handleResponse } from "./http";

describe("handleResponse", () => {
  it("returns null on 204", async () => {
    const res = new Response(null, { status: 204, statusText: "No Content" });
    const result = await handleResponse(res, "req-1");
    expect(result).toBeNull();
  });

  it("returns null on 205", async () => {
    const res = new Response(null, { status: 205, statusText: "Reset Content" });
    const result = await handleResponse(res, "req-1b");
    expect(result).toBeNull();
  });

  it("parses JSON responses", async () => {
    const body = JSON.stringify({ ok: true });
    const res = new Response(body, {
      status: 200,
      headers: { "content-type": "application/json" },
    });
    const result = await handleResponse<{ ok: boolean }>(res, "req-2");
    expect(result).toEqual({ ok: true });
  });

  it("returns text when content-type is not JSON", async () => {
    const res = new Response("plain text", { status: 200 });
    const result = await handleResponse<string>(res, "req-3");
    expect(result).toBe("plain text");
  });

  it("throws with detail message for JSON errors", async () => {
    const res = new Response(JSON.stringify({ detail: "Bad request" }), {
      status: 400,
      headers: { "content-type": "application/json" },
    });
    await expect(handleResponse(res, "req-4")).rejects.toThrow("Bad request");
  });
});
