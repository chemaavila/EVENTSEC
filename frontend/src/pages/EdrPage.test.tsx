import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import EdrPage from "./EdrPage";

const mockListEdrEvents = vi.fn();

vi.mock("../services/api", async () => {
  const actual = await vi.importActual<typeof import("../services/api")>("../services/api");
  return {
    ...actual,
    listEdrEvents: () => mockListEdrEvents(),
  };
});

describe("EdrPage", () => {
  it("opens drawer on event click without window.open", async () => {
    const openSpy = vi.spyOn(window, "open");
    mockListEdrEvents.mockResolvedValueOnce([
      {
        timestamp: new Date().toISOString(),
        hostname: "endpoint-1",
        username: "analyst",
        event_type: "process",
        process_name: "powershell.exe",
        action: "blocked",
        severity: "critical",
        details: { command: "Invoke-WebRequest" },
      },
    ]);

    render(<EdrPage />);

    const row = await screen.findByTestId("edr-event-row-0");
    fireEvent.click(row);

    expect(await screen.findByTestId("event-drawer-title")).toHaveTextContent(
      "blocked — powershell.exe"
    );
    expect(openSpy).not.toHaveBeenCalled();
  });

  it("clears the view without deleting history", async () => {
    mockListEdrEvents.mockResolvedValueOnce([
      {
        timestamp: new Date().toISOString(),
        hostname: "endpoint-1",
        username: "analyst",
        event_type: "process",
        process_name: "powershell.exe",
        action: "blocked",
        severity: "critical",
        details: { command: "Invoke-WebRequest" },
      },
    ]);

    render(<EdrPage />);

    expect(await screen.findByTestId("edr-event-row-0")).toBeInTheDocument();

    const clearButton = await screen.findByRole("button", { name: "Clear view" });
    fireEvent.click(clearButton);

    expect(screen.queryByTestId("edr-event-row-0")).toBeNull();
  });
});
