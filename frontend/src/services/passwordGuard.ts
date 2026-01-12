import { API_BASE_URL } from "../config/endpoints";
import { apiFetch, toQueryParams } from "./http";
import type { Alert, AlertSeverity, AlertStatus } from "./api";

export type PasswordGuardAction =
  | "DETECTED"
  | "USER_APPROVED_ROTATION"
  | "USER_DENIED_ROTATION"
  | "ROTATED";

export interface PasswordGuardEvent {
  id: number;
  tenant_id: string;
  host_id: string;
  user: string;
  entry_id: string;
  entry_label: string;
  exposure_count: number;
  action: PasswordGuardAction;
  timestamp: string;
  client_version: string;
  alert_id?: number | null;
  created_at: string;
  updated_at: string;
}

export interface PasswordGuardAlert {
  alert: Alert & {
    status: AlertStatus;
    severity: AlertSeverity;
  };
  event?: PasswordGuardEvent | null;
}

export interface PasswordGuardEventFilters {
  tenant_id?: string;
  host_id?: string;
  user?: string;
  action?: PasswordGuardAction;
  from?: string;
  to?: string;
}

export async function listPasswordGuardEvents(
  filters: PasswordGuardEventFilters = {},
): Promise<PasswordGuardEvent[]> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/api/v1/password-guard/events",
    query: toQueryParams(filters),
  });
}

export async function listPasswordGuardAlerts(
  filters: PasswordGuardEventFilters = {},
): Promise<PasswordGuardAlert[]> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/api/v1/password-guard/alerts",
    query: toQueryParams(filters),
  });
}
