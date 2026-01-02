import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import SiemPage from "./SiemPage";

const mockListSiemEvents = vi.fn();
const mockClearSiemEvents = vi.fn();

vi.mock("../services/api", async () => {
  const actual = await vi.importActual<typeof import("../services/api")>("../services/api");
  return {
    ...actual,
    listSiemEvents: () => mockListSiemEvents(),
    clearSiemEvents: () => mockClearSiemEvents(),
  };
});

describe("SiemPage", () => {
  it("opens drawer on event click without window.open", async () => {
    const openSpy = vi.spyOn(window, "open");
    mockListSiemEvents.mockResolvedValueOnce([
      {
        timestamp: new Date().toISOString(),
        host: "host-1",
        source: "edr",
        category: "auth",
        severity: "high",
        message: "Suspicious login",
        raw: { ip: "10.0.0.1" },
      },
    ]);

    render(<SiemPage />);

    const row = await screen.findByText("Suspicious login");
    fireEvent.click(row);

    expect(await screen.findByText("Suspicious login")).toBeInTheDocument();
    expect(openSpy).not.toHaveBeenCalled();
  });
});
