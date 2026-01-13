import { describe, expect, it } from "vitest";

import { resolveApiBaseFromEnv } from "./endpoints";

describe("resolveApiBaseFromEnv", () => {
  it("forces /api in production when override is absolute", () => {
    const resolved = resolveApiBaseFromEnv({
      VITE_API_BASE_URL: "https://eventsec-backend.onrender.com",
      MODE: "production",
      PROD: true,
    });

    expect(resolved).toBe("/api");
  });

  it("allows relative override in production", () => {
    const resolved = resolveApiBaseFromEnv({
      VITE_API_BASE_URL: "/api",
      MODE: "production",
      PROD: true,
    });

    expect(resolved).toBe("/api");
  });

  it("uses absolute override in development", () => {
    const resolved = resolveApiBaseFromEnv({
      VITE_API_BASE_URL: "http://localhost:8000",
      MODE: "development",
      PROD: false,
    });

    expect(resolved).toBe("http://localhost:8000");
  });
});
