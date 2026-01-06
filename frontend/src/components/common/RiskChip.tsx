import type { RiskLabel } from "../../types/inventory";

type RiskChipProps = {
  label?: RiskLabel | null;
  counts?: Partial<Record<RiskLabel, number>>;
};

const RISK_ORDER: RiskLabel[] = ["CRITICAL", "HIGH", "MEDIUM", "LOW"];

const RiskChip = ({ label, counts }: RiskChipProps) => {
  const resolvedLabel = label ?? "LOW";
  const countLabel = counts
    ? RISK_ORDER.map((risk) => `${risk[0]}:${counts[risk] ?? 0}`).join(" ")
    : null;
  return (
    <span className={`badge risk-chip risk-${resolvedLabel.toLowerCase()}`}>
      {resolvedLabel}
      {countLabel ? <span className="risk-chip-counts">{countLabel}</span> : null}
    </span>
  );
};

export default RiskChip;
