import { describe, expect, it } from "vitest";
import { resolveWsUrl } from "./endpoints";

describe("resolveWsUrl", () => {
  it("derives ws from http API base", async () => {
    expect(
      resolveWsUrl("/ws/threatmap", {
        apiBaseUrl: "http://api.example.com:8000",
      })
    ).toBe("ws://api.example.com:8000/ws/threatmap");
  });

  it("derives wss from https API base", async () => {
    expect(
      resolveWsUrl("/ws/threatmap", {
        apiBaseUrl: "https://api.example.com",
      })
    ).toBe("wss://api.example.com/ws/threatmap");
  });

  it("uses override when VITE_THREATMAP_WS_URL is set", async () => {
    expect(
      resolveWsUrl("/ws/threatmap", {
        apiBaseUrl: "https://api.example.com",
        wsOverride: "wss://stream.example.com/ws/threatmap",
      })
    ).toBe("wss://stream.example.com/ws/threatmap");
  });
});
