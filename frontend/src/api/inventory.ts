import { API_BASE_URL } from "../config/endpoints";
import { apiFetch } from "../services/http";
import type {
  AssetInventorySummary,
  InventoryAssetDetail,
  AssetRiskSummary,
  InventoryIngestResponse,
} from "../types/inventory";

export async function fetchAssetsWithRisk(): Promise<AssetInventorySummary[]> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/api/inventory/assets",
  });
}

export async function fetchAssetDetail(
  assetId: number
): Promise<InventoryAssetDetail> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: `/api/inventory/assets/${assetId}`,
  });
}

export async function ingestAssetSoftware(
  assetId: number,
  payload: {
    collected_at?: string;
    items: Array<{
      name: string;
      version: string;
      vendor?: string | null;
      source?: string | null;
      purl?: string | null;
      cpe?: string | null;
      raw?: Record<string, unknown> | null;
    }>;
  }
): Promise<InventoryIngestResponse> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: `/api/inventory/assets/${assetId}/software`,
    method: "POST",
    body: payload,
  });
}

export function summarizeRisk(summary: AssetRiskSummary): string {
  const total =
    summary.critical_count +
    summary.high_count +
    summary.medium_count +
    summary.low_count;
  return `${total} findings`;
}
