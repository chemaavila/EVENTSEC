import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import RiskChip from "./RiskChip";

describe("RiskChip", () => {
  it("renders label and counts", () => {
    const { container, getByText } = render(
      <RiskChip
        label="CRITICAL"
        counts={{ CRITICAL: 2, HIGH: 1, MEDIUM: 0, LOW: 3 }}
      />
    );
    expect(getByText("CRITICAL")).toBeInTheDocument();
    expect(container.firstChild).toMatchSnapshot();
  });
});
