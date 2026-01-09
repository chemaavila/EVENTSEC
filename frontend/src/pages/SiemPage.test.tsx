import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import SiemPage from "./SiemPage";

const mockListSiemEvents = vi.fn();

vi.mock("../services/api", async () => {
  const actual = await vi.importActual<typeof import("../services/api")>("../services/api");
  return {
    ...actual,
    listSiemEvents: () => mockListSiemEvents(),
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

    const row = await screen.findByTestId("siem-event-row-0");
    fireEvent.click(row);

    expect(await screen.findByTestId("event-drawer-title")).toHaveTextContent(
      "Suspicious login"
    );
    expect(openSpy).not.toHaveBeenCalled();
  });

  it("clears the view without deleting history", async () => {
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

    expect(await screen.findByTestId("siem-event-row-0")).toBeInTheDocument();

    const clearButton = await screen.findByRole("button", { name: "Clear view" });
    fireEvent.click(clearButton);

    expect(screen.queryByTestId("siem-event-row-0")).toBeNull();
  });
});
