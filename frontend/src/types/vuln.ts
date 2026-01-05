import type { RiskLabel, SoftwareComponent } from "./inventory";

export interface VulnerabilityRecord {
  id: number;
  source: string;
  cve_id?: string | null;
  osv_id?: string | null;
  title?: string | null;
  summary?: string | null;
  cvss_score?: number | null;
  cvss_vector?: string | null;
  epss_score?: number | null;
  kev: boolean;
  published_at?: string | null;
  modified_at?: string | null;
}

export interface AssetVulnerability {
  id: number;
  tenant_id: string;
  asset_id: number;
  software_component_id: number;
  vulnerability_id: number;
  status: string;
  risk_label: RiskLabel;
  risk_score: number;
  confidence: number;
  first_seen_at: string;
  last_seen_at: string;
  last_notified_at?: string | null;
  notified_risk_label?: RiskLabel | null;
  vulnerability?: VulnerabilityRecord;
  software_component?: SoftwareComponent;
}

export interface AssetVulnerabilityListResponse {
  items: AssetVulnerability[];
  total: number;
}

export interface GlobalVulnerabilityRecord {
  asset_id: number;
  asset_name?: string | null;
  finding: AssetVulnerability;
}
