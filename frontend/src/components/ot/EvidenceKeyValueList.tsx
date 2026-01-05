import React from "react";
import type { OtEvidenceKV } from "../../types/ot";

const EvidenceKeyValueList: React.FC<{ items: OtEvidenceKV[] }> = ({ items }) => {
  const handleCopy = async (value: string) => {
    try {
      await navigator.clipboard.writeText(value);
    } catch (error) {
      console.error("Failed to copy value", error);
    }
  };

  return (
    <ul className="evidence-list">
      {items.map((item) => (
        <li key={item.key} className="evidence-list-item">
          <span className="evidence-key">{item.key}</span>
          <span className="evidence-value">{item.value}</span>
          <button type="button" className="btn btn-ghost btn-sm" onClick={() => handleCopy(item.value)}>
            Copy
          </button>
        </li>
      ))}
    </ul>
  );
};

export default EvidenceKeyValueList;
