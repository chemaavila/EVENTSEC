import { API_BASE_URL } from "../config/endpoints";
import { apiFetch } from "./http";

export type IncidentStatus =
  | "new"
  | "triage"
  | "in_progress"
  | "contained"
  | "resolved"
  | "closed";

export type IncidentSeverity = "low" | "medium" | "high" | "critical";

export interface IncidentItem {
  id: number;
  incident_id: number;
  kind: string;
  ref_id: string;
  created_at: string;
}

export interface Incident {
  id: number;
  tenant_id?: string | null;
  title: string;
  description?: string | null;
  severity: IncidentSeverity;
  status: IncidentStatus;
  assigned_to?: number | null;
  tags: string[];
  created_by?: number | null;
  created_at: string;
  updated_at: string;
  items: IncidentItem[];
}

export interface IncidentCreatePayload {
  title: string;
  description?: string | null;
  severity?: IncidentSeverity;
  status?: IncidentStatus;
  assigned_to?: number | null;
  tags?: string[];
  items?: Array<{ kind: string; ref_id: string }>;
}

export interface IncidentUpdatePayload {
  title?: string;
  description?: string | null;
  severity?: IncidentSeverity;
  status?: IncidentStatus;
  assigned_to?: number | null;
  tags?: string[];
}

export async function listIncidents(): Promise<Incident[]> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/incidents",
  });
}

export async function getIncident(incidentId: string | number): Promise<Incident> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: `/incidents/${incidentId}`,
  });
}

export async function createIncident(
  payload: IncidentCreatePayload
): Promise<Incident> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/incidents",
    method: "POST",
    body: payload,
  });
}

export async function updateIncident(
  incidentId: string | number,
  payload: IncidentUpdatePayload
): Promise<Incident> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: `/incidents/${incidentId}`,
    method: "PATCH",
    body: payload,
  });
}

export async function attachIncidentItem(
  incidentId: string | number,
  payload: { kind: string; ref_id: string }
): Promise<IncidentItem> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: `/incidents/${incidentId}/items`,
    method: "POST",
    body: payload,
  });
}

export async function createIncidentFromAlert(
  alertId: number
): Promise<Incident> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: `/incidents/from-alert/${alertId}`,
    method: "POST",
  });
}

export async function createIncidentFromNetworkEvent(
  eventId: string
): Promise<Incident> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: `/incidents/from-network-event/${eventId}`,
    method: "POST",
  });
}
