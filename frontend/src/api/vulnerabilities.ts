import { API_BASE_URL } from "../config/endpoints";
import { apiFetch } from "../services/http";
import type {
  AssetVulnerabilityListResponse,
  GlobalVulnerabilityRecord,
} from "../types/vuln";

export async function fetchAssetVulns(
  assetId: number,
  filters: {
    status?: string;
    min_risk?: string;
    kev?: boolean;
    search?: string;
    limit?: number;
    offset?: number;
  } = {}
): Promise<AssetVulnerabilityListResponse> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: `/api/inventory/assets/${assetId}/vulnerabilities`,
    query: filters,
  });
}

export async function fetchGlobalVulns(filters: {
  min_risk?: string;
  kev?: boolean;
  epss_min?: number;
  cve_id?: string;
  software_name?: string;
} = {}): Promise<GlobalVulnerabilityRecord[]> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/api/vulnerabilities",
    query: filters,
  });
}

export async function updateFindingStatus(
  assetId: number,
  findingId: number,
  status: string
): Promise<unknown> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: `/api/inventory/assets/${assetId}/vulnerabilities/${findingId}/status`,
    method: "POST",
    body: { status },
  });
}
