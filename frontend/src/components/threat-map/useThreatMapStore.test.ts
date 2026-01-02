import { describe, expect, it } from "vitest";
import { deriveLiveState } from "./useThreatMapStore";

describe("deriveLiveState", () => {
  it("returns OFFLINE when transport is CLOSED", () => {
    expect(deriveLiveState("CLOSED", "LIVE")).toBe("OFFLINE");
  });

  it("returns CONNECTING when transport is CONNECTING", () => {
    expect(deriveLiveState("CONNECTING", "WAITING")).toBe("CONNECTING");
  });

  it("returns WAITING when open without heartbeat", () => {
    expect(deriveLiveState("OPEN", "WAITING")).toBe("WAITING");
  });

  it("returns LIVE when stream is live", () => {
    expect(deriveLiveState("OPEN", "LIVE")).toBe("LIVE");
  });

  it("returns STALE when stream is stale", () => {
    expect(deriveLiveState("OPEN", "STALE")).toBe("STALE");
  });
});
