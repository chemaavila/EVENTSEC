import { API_BASE_URL } from "../config/endpoints";
import { apiFetch } from "./http";

export interface ResponseAction {
  id: number;
  tenant_id?: string | null;
  action_type: string;
  target: string;
  ttl_minutes?: number | null;
  status: string;
  requested_by?: number | null;
  created_at: string;
  updated_at: string;
  details?: Record<string, unknown>;
}

export interface ResponseActionCreatePayload {
  action_type: string;
  target: string;
  ttl_minutes?: number | null;
  status?: string;
  details?: Record<string, unknown>;
}

export interface ResponseActionUpdatePayload {
  status?: string;
  details?: Record<string, unknown>;
}

export async function listResponseActions(): Promise<ResponseAction[]> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/actions",
  });
}

export async function createResponseAction(
  payload: ResponseActionCreatePayload
): Promise<ResponseAction> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/actions",
    method: "POST",
    body: payload,
  });
}

export async function updateResponseAction(
  actionId: number,
  payload: ResponseActionUpdatePayload
): Promise<ResponseAction> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: `/actions/${actionId}`,
    method: "PATCH",
    body: payload,
  });
}
