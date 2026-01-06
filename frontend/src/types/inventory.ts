export type RiskLabel = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";

export interface AssetRiskSummary {
  asset_id: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  top_risk_label?: RiskLabel | null;
  last_scan_at?: string | null;
}

export interface SoftwareComponent {
  id: number;
  tenant_id: string;
  asset_id: number;
  name: string;
  version: string;
  vendor?: string | null;
  source?: string | null;
  purl?: string | null;
  cpe?: string | null;
  collected_at: string;
  last_seen_at: string;
}

export interface AssetInventorySummary {
  asset: {
    id: number;
    name: string;
    os: string;
    ip_address: string;
    status: string;
    last_seen?: string | null;
  };
  risk: AssetRiskSummary;
}

export interface InventoryAssetDetail {
  asset: AssetInventorySummary["asset"];
  software: SoftwareComponent[];
  risk: AssetRiskSummary;
}

export interface InventoryIngestResponse {
  inserted: number;
  updated: number;
  asset_risk: AssetRiskSummary;
}
