import { describe, expect, it, vi } from "vitest";

const loadEndpoints = async (env: Record<string, string | undefined>) => {
  vi.resetModules();
  Object.defineProperty(import.meta, "env", {
    value: env,
    writable: true,
    configurable: true,
  });
  return import("./endpoints");
};

describe("resolveWsUrl", () => {
  it("derives ws from http API base", async () => {
    const mod = await loadEndpoints({ VITE_API_BASE_URL: "http://api.example.com:8000" });
    expect(mod.resolveWsUrl("/ws/threatmap")).toBe("ws://api.example.com:8000/ws/threatmap");
  });

  it("derives wss from https API base", async () => {
    const mod = await loadEndpoints({ VITE_API_BASE_URL: "https://api.example.com" });
    expect(mod.resolveWsUrl("/ws/threatmap")).toBe("wss://api.example.com/ws/threatmap");
  });

  it("uses override when VITE_THREATMAP_WS_URL is set", async () => {
    const mod = await loadEndpoints({
      VITE_API_BASE_URL: "https://api.example.com",
      VITE_THREATMAP_WS_URL: "wss://stream.example.com/ws/threatmap",
    });
    expect(mod.resolveWsUrl("/ws/threatmap")).toBe("wss://stream.example.com/ws/threatmap");
  });
});
