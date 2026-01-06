import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import AssetsPage from "./AssetsPage";

const mockListOtAssets = vi.fn();
const mockGetOtAsset = vi.fn();

vi.mock("../../services/ot", () => ({
  default: {
    listOtAssets: (params: unknown) => mockListOtAssets(params),
    getOtAsset: (id: string) => mockGetOtAsset(id),
  },
}));

describe("AssetsPage", () => {
  it("applies debounced search filters", async () => {
    vi.useFakeTimers();
    mockListOtAssets.mockResolvedValue({
      items: [],
      page: 1,
      pageSize: 8,
      total: 0,
    });

    render(
      <MemoryRouter initialEntries={["/ot/assets"]}>
        <AssetsPage />
      </MemoryRouter>
    );

    const input = await screen.findByLabelText(/search/i);
    fireEvent.change(input, { target: { value: "PLC" } });

    await vi.advanceTimersByTimeAsync(500);

    await waitFor(() => {
      expect(mockListOtAssets).toHaveBeenLastCalledWith(
        expect.objectContaining({ q: "PLC" })
      );
    });

    vi.useRealTimers();
  });
});
