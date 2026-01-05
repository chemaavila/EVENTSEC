import React from "react";
import type { OtDirection } from "../../types/ot";
import { directionLabel } from "../../lib/otFormat";

type DirectionPillProps = {
  direction: OtDirection;
  active?: boolean;
  onClick?: () => void;
};

const DirectionPill: React.FC<DirectionPillProps> = ({ direction, active, onClick }) => (
  <button
    type="button"
    className={`direction-pill${active ? " direction-pill-active" : ""}`}
    onClick={onClick}
    aria-pressed={active}
  >
    <span className="direction-pill-icon">↔</span>
    {directionLabel(direction)}
  </button>
);

export default DirectionPill;
