import React from "react";
import type { OtSensor } from "../../types/ot";

const capabilityLabels: Array<keyof OtSensor["capabilities"]> = [
  "zeek",
  "icsnpp",
  "acid",
  "suricata",
];

const CapabilityBadges: React.FC<{ capabilities: OtSensor["capabilities"] }> = ({
  capabilities,
}) => {
  const entries = capabilityLabels.filter((key) => capabilities[key]);
  return (
    <div className="capability-badges">
      {entries.length === 0 ? (
        <span className="muted">None</span>
      ) : (
        entries.map((key) => (
          <span key={key} className="badge capability-badge">
            {key.toUpperCase()}
          </span>
        ))
      )}
    </div>
  );
};

export default CapabilityBadges;
