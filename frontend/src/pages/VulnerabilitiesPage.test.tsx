import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import VulnerabilitiesPage from "./VulnerabilitiesPage";
import { FeatureFlagsProvider } from "../contexts/FeatureFlagsContext";

const mockFetchGlobalVulns = vi.fn();

vi.mock("../api/vulnerabilities", () => ({
  fetchGlobalVulns: () => mockFetchGlobalVulns(),
}));

describe("VulnerabilitiesPage", () => {
  it("shows disabled state when vuln intel is off", () => {
    render(
      <FeatureFlagsProvider
        initialFlags={{ vulnIntel: false }}
        disableFetch
      >
        <VulnerabilitiesPage />
      </FeatureFlagsProvider>
    );

    expect(
      screen.getByText("Vulnerability intelligence disabled")
    ).toBeInTheDocument();
    expect(mockFetchGlobalVulns).not.toHaveBeenCalled();
  });
});
