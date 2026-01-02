import { API_BASE_URL } from "../config/endpoints";
import { apiFetch } from "./http";

export type AlertStatus = "open" | "in_progress" | "closed";
export type AlertSeverity = "low" | "medium" | "high" | "critical";

export interface Alert {
  id: number;
  title: string;
  description: string;
  source: string;
  category: string;
  severity: AlertSeverity;
  status: AlertStatus;
  url?: string | null;
  sender?: string | null;
  username?: string | null;
  hostname?: string | null;
  conclusion?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AlertCreatePayload {
  title: string;
  description: string;
  source: string;
  category: string;
  severity: AlertSeverity;
  url?: string | null;
  sender?: string | null;
  username?: string | null;
  hostname?: string | null;
}

export interface AlertEscalationPayload {
  escalated_to: number;
  reason?: string;
}

export interface Handover {
  id: number;
  shift_start: string;
  shift_end: string;
  analyst: string;
  notes: string;
  alerts_summary: string;
  created_at: string;
}

export interface Workplan {
  id: number;
  title: string;
  description: string;
  alert_id?: number | null;
  assigned_to?: number | null;
  created_by: number;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface WorkplanCreatePayload {
  title: string;
  description: string;
  alert_id?: number | null;
  assigned_to?: number | null;
}

export interface WorkplanUpdatePayload {
  title?: string;
  description?: string;
  alert_id?: number | null;
  assigned_to?: number | null;
  status?: string;
}

export interface WarRoomNote {
  id: number;
  alert_id?: number | null;
  content: string;
  created_by: number;
  attachments: string[];
  created_at: string;
}

export interface WarRoomNoteCreatePayload {
  alert_id?: number | null;
  content: string;
  attachments?: string[];
}


export interface UserProfile {
  id: number;
  full_name: string;
  role: string;
  email: string;
  avatar_url?: string | null;
  timezone: string;
  team?: string | null;
  manager?: string | null;
  computer?: string | null;
  mobile_phone?: string | null;
}

export interface EndpointProcess {
  name: string;
  pid: number;
  user: string;
  cpu: number;
  ram: number;
}

export interface Agent {
  id: number;
  name: string;
  os: string;
  ip_address: string;
  version?: string | null;
  tags: string[];
  status: string;
  last_heartbeat?: string | null;
  last_seen?: string | null;
  last_ip?: string | null;
}

export interface Endpoint {
  id: number;
  agent_id?: number | null;
  hostname: string;
  display_name: string;
  status: string;
  agent_status: string;
  agent_version: string;
  ip_address: string;
  owner: string;
  os: string;
  os_version: string;
  cpu_model: string;
  ram_gb: number;
  disk_gb: number;
  resource_usage: Record<string, number>;
  last_seen: string;
  location: string;
  processes: EndpointProcess[];
  alerts_open: number;
  tags: string[];
}

export interface InventorySnapshot {
  id: number;
  agent_id: number;
  category: string;
  data: Record<string, unknown>;
  collected_at: string;
}

export interface InventoryOverview {
  agent_id: number;
  categories: Record<string, InventorySnapshot[]>;
}

export interface SandboxIOC {
  type: string;
  value: string;
  description?: string;
}

export interface SandboxEndpointMatch {
  id: number;
  hostname: string;
  status: string;
  ip_address: string;
  last_seen: string;
  location: string;
}

export interface SandboxAnalysisResult {
  id: number;
  type: string;
  value: string;
  filename?: string | null;
  verdict: string;
  threat_type?: string | null;
  status: string;
  progress: number;
  file_hash?: string | null;
  iocs: SandboxIOC[];
  endpoints: SandboxEndpointMatch[];
  vt_results?: Record<string, unknown>;
  osint_results?: Record<string, unknown>;
  yara_matches: YaraMatch[];
  created_at: string;
}

export interface YaraMatch {
  rule_id: string;
  rule_name: string;
  source: string;
  description?: string | null;
  tags: string[];
}

export interface YaraRule extends YaraMatch {
  author?: string | null;
  reference?: string | null;
  rule: string;
}

export interface UserCreatePayload {
  full_name: string;
  role: string;
  email: string;
  password: string;
  team?: string | null;
  manager?: string | null;
  computer?: string | null;
  mobile_phone?: string | null;
  timezone?: string;
}

export interface UserUpdatePayload {
  full_name?: string;
  role?: string;
  email?: string;
  team?: string | null;
  manager?: string | null;
  computer?: string | null;
  mobile_phone?: string | null;
  timezone?: string;
}

export interface SandboxAnalysisPayload {
  type: string;
  value: string;
  filename?: string;
  metadata?: Record<string, unknown>;
}

export interface Indicator {
  id: number;
  type: string;
  value: string;
  description?: string | null;
  severity: AlertSeverity;
  source: string;
  tags: string[];
  status: "active" | "retired";
  created_at: string;
  updated_at: string;
}

export interface IndicatorCreatePayload {
  type: string;
  value: string;
  description?: string;
  severity?: AlertSeverity;
  source?: string;
  tags?: string[];
}

export interface IndicatorUpdatePayload extends Partial<IndicatorCreatePayload> {
  status?: "active" | "retired";
}

export interface BiocRule {
  id: number;
  name: string;
  description: string;
  platform: string;
  tactic: string;
  technique?: string;
  detection_logic: string;
  severity: AlertSeverity;
  status: "enabled" | "disabled";
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface BiocRulePayload {
  name: string;
  description: string;
  platform: string;
  tactic: string;
  technique?: string;
  detection_logic: string;
  severity?: AlertSeverity;
  tags?: string[];
}

export interface BiocRuleUpdatePayload extends Partial<BiocRulePayload> {
  status?: "enabled" | "disabled";
}

export interface AnalyticsRule {
  id: number;
  name: string;
  description: string;
  datasource: string;
  severity: AlertSeverity;
  status: "enabled" | "disabled";
  query: string;
  owner: string;
  created_at: string;
  updated_at: string;
}

export interface AnalyticsRulePayload {
  name: string;
  description: string;
  datasource: string;
  severity?: AlertSeverity;
  query: string;
  owner: string;
}

export interface AnalyticsRuleUpdatePayload
  extends Partial<AnalyticsRulePayload> {
  status?: "enabled" | "disabled";
}

export interface NetworkEvent {
  id: number;
  hostname: string;
  username: string;
  url: string;
  verdict: "allowed" | "blocked" | "malicious";
  category: string;
  description: string;
  severity: AlertSeverity;
  created_at: string;
}

export interface IndexedEvent {
  event_id?: number;
  agent_id?: number;
  event_type?: string;
  severity?: string;
  category?: string;
  timestamp?: string;
  message?: string;
  details?: Record<string, unknown>;
}

export interface KqlQueryPayload {
  query: string;
  limit?: number;
}

export interface KqlQueryResponse {
  query: string;
  index: string;
  took_ms: number;
  total: number;
  hits: Array<Record<string, unknown>>;
  fields?: string[];
}

export interface SearchEventsParams {
  query?: string;
  severity?: string;
  size?: number;
}

export interface NetworkEventCreatePayload {
  hostname: string;
  username: string;
  url: string;
  verdict?: "allowed" | "blocked" | "malicious";
  category?: string;
  description?: string;
  severity?: AlertSeverity;
}

export interface EndpointAction {
  id: number;
  endpoint_id: number;
  action_type: "isolate" | "release" | "reboot" | "command";
  parameters: Record<string, unknown>;
  status: "pending" | "completed" | "failed";
  requested_by?: number | null;
  requested_at: string;
  completed_at?: string | null;
  output?: string | null;
}

export interface EndpointActionCreatePayload {
  action_type: EndpointAction["action_type"];
  parameters?: Record<string, unknown>;
}

export interface HandoverCreatePayload {
  shift_start: string;
  shift_end: string;
  analyst: string;
  notes: string;
  alerts_summary: string;
  send_email?: boolean;
  recipient_emails?: string[];
}

export async function login(email: string, password: string): Promise<{ access_token: string; user: UserProfile }> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/auth/login",
    method: "POST",
    body: { email, password },
  });
}

export async function logout(): Promise<void> {
  await apiFetch({
    baseUrl: API_BASE_URL,
    path: "/auth/logout",
    method: "POST",
  });
}

export async function listAlerts(): Promise<Alert[]> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/alerts",
  });
}

export async function getAlert(alertId: number): Promise<Alert> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: `/alerts/${alertId}`,
  });
}

export async function createAlert(
  payload: AlertCreatePayload
): Promise<Alert> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/alerts",
    method: "POST",
    body: payload,
  });
}

export async function blockUrl(alertId: number, url: string): Promise<void> {
  await apiFetch({
    baseUrl: API_BASE_URL,
    path: `/alerts/${alertId}/block-url`,
    method: "POST",
    query: { url },
  });
}

export async function unblockUrl(alertId: number, url: string): Promise<void> {
  await apiFetch({
    baseUrl: API_BASE_URL,
    path: `/alerts/${alertId}/unblock-url`,
    method: "POST",
    query: { url },
  });
}

export async function blockSender(alertId: number, sender: string): Promise<void> {
  await apiFetch({
    baseUrl: API_BASE_URL,
    path: `/alerts/${alertId}/block-sender`,
    method: "POST",
    query: { sender },
  });
}

export async function unblockSender(alertId: number, sender: string): Promise<void> {
  await apiFetch({
    baseUrl: API_BASE_URL,
    path: `/alerts/${alertId}/unblock-sender`,
    method: "POST",
    query: { sender },
  });
}

export async function revokeUserSession(alertId: number, username: string): Promise<void> {
  await apiFetch({
    baseUrl: API_BASE_URL,
    path: `/alerts/${alertId}/revoke-session`,
    method: "POST",
    query: { username },
  });
}

export async function isolateDevice(alertId: number, hostname: string): Promise<void> {
  await apiFetch({
    baseUrl: API_BASE_URL,
    path: `/alerts/${alertId}/isolate-device`,
    method: "POST",
    query: { hostname },
  });
}

export async function getMyProfile(): Promise<UserProfile> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/me",
  });
}

export async function listEndpoints(): Promise<Endpoint[]> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/endpoints",
  });
}

export async function listAgents(): Promise<Agent[]> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/agents",
  });
}

export async function getEndpoint(endpointId: number): Promise<Endpoint> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: `/endpoints/${endpointId}`,
  });
}

export async function getInventoryOverview(
  agentId: number,
  category?: string
): Promise<InventoryOverview> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: `/inventory/${agentId}`,
    query: category ? { category } : undefined,
  });
}

export async function listSandboxAnalyses(): Promise<SandboxAnalysisResult[]> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/sandbox/analyses",
  });
}

export async function analyzeSandbox(
  payload: SandboxAnalysisPayload
): Promise<SandboxAnalysisResult> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/sandbox/analyze",
    method: "POST",
    body: payload,
  });
}

export async function listUsers(): Promise<UserProfile[]> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/users",
  });
}

export async function createUser(payload: UserCreatePayload): Promise<UserProfile> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/users",
    method: "POST",
    body: payload,
  });
}

export async function updateUser(
  userId: number,
  payload: UserUpdatePayload
): Promise<UserProfile> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: `/users/${userId}`,
    method: "PATCH",
    body: payload,
  });
}

export async function listHandovers(): Promise<Handover[]> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/handover",
  });
}

export async function createHandover(
  payload: HandoverCreatePayload
): Promise<Handover> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/handover",
    method: "POST",
    body: payload,
  });
}

export async function listWorkplans(): Promise<Workplan[]> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/workplans",
  });
}

export async function createWorkplan(
  payload: WorkplanCreatePayload
): Promise<Workplan> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/workplans",
    method: "POST",
    body: payload,
  });
}

export async function updateWorkplan(
  workplanId: number,
  payload: WorkplanUpdatePayload
): Promise<Workplan> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: `/workplans/${workplanId}`,
    method: "PATCH",
    body: payload,
  });
}

export async function listWarRoomNotes(alertId?: number): Promise<WarRoomNote[]> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/warroom/notes",
    query: alertId ? { alert_id: alertId } : undefined,
  });
}

export async function createWarRoomNote(
  payload: WarRoomNoteCreatePayload
): Promise<WarRoomNote> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/warroom/notes",
    method: "POST",
    body: payload,
  });
}

export async function listIndicators(): Promise<Indicator[]> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/indicators",
  });
}

export async function createIndicator(
  payload: IndicatorCreatePayload
): Promise<Indicator> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/indicators",
    method: "POST",
    body: payload,
  });
}

export async function updateIndicator(
  indicatorId: number,
  payload: IndicatorUpdatePayload
): Promise<Indicator> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: `/indicators/${indicatorId}`,
    method: "PATCH",
    body: payload,
  });
}

export async function listBiocRules(): Promise<BiocRule[]> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/biocs",
  });
}

export async function createBiocRule(
  payload: BiocRulePayload
): Promise<BiocRule> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/biocs",
    method: "POST",
    body: payload,
  });
}

export async function updateBiocRule(
  ruleId: number,
  payload: BiocRuleUpdatePayload
): Promise<BiocRule> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: `/biocs/${ruleId}`,
    method: "PATCH",
    body: payload,
  });
}

export async function listAnalyticsRules(): Promise<AnalyticsRule[]> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/analytics/rules",
  });
}

export async function getAnalyticsRule(ruleId: number): Promise<AnalyticsRule> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: `/analytics/rules/${ruleId}`,
  });
}

export async function createAnalyticsRule(
  payload: AnalyticsRulePayload
): Promise<AnalyticsRule> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/analytics/rules",
    method: "POST",
    body: payload,
  });
}

export async function updateAnalyticsRule(
  ruleId: number,
  payload: AnalyticsRuleUpdatePayload
): Promise<AnalyticsRule> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: `/analytics/rules/${ruleId}`,
    method: "PATCH",
    body: payload,
  });
}

export async function listYaraRules(): Promise<YaraRule[]> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/yara/rules",
  });
}

export async function listNetworkEvents(): Promise<NetworkEvent[]> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/network/events",
  });
}

export async function createNetworkEvent(
  payload: NetworkEventCreatePayload
): Promise<NetworkEvent> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/network/events",
    method: "POST",
    body: payload,
  });
}

export async function searchEvents(
  params: SearchEventsParams = {}
): Promise<IndexedEvent[]> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/events",
    query: {
      query: params.query,
      severity: params.severity,
      size: params.size,
    },
  });
}

export async function runKqlQuery(payload: KqlQueryPayload): Promise<KqlQueryResponse> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/search/kql",
    method: "POST",
    body: payload,
  });
}

export async function listEndpointActions(
  endpointId: number
): Promise<EndpointAction[]> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: `/endpoints/${endpointId}/actions`,
  });
}

export async function createEndpointAction(
  endpointId: number,
  payload: EndpointActionCreatePayload
): Promise<EndpointAction> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: `/endpoints/${endpointId}/actions`,
    method: "POST",
    body: payload,
  });
}

export async function updateAlert(
  alertId: number,
  payload: Partial<{ status: AlertStatus; assigned_to: number | null; conclusion: string | null }>
): Promise<Alert> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: `/alerts/${alertId}`,
    method: "PATCH",
    body: payload,
  });
}

export async function escalateAlert(
  alertId: number,
  payload: AlertEscalationPayload
): Promise<void> {
  await apiFetch({
    baseUrl: API_BASE_URL,
    path: `/alerts/${alertId}/escalate`,
    method: "POST",
    body: { alert_id: alertId, ...payload },
  });
}

export async function deleteAlert(alertId: number): Promise<void> {
  await apiFetch({
    baseUrl: API_BASE_URL,
    path: `/alerts/${alertId}`,
    method: "DELETE",
  });
}

// SIEM Events
export interface SiemEvent {
  timestamp: string;
  host: string;
  source: string;
  category: string;
  severity: string;
  message: string;
  raw: Record<string, unknown>;
}

export interface SiemEventCreatePayload {
  timestamp: string;
  host: string;
  source: string;
  category: string;
  severity: string;
  message: string;
  raw?: Record<string, unknown>;
}

export async function listSiemEvents(): Promise<SiemEvent[]> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/siem/events",
  });
}

export async function clearSiemEvents(): Promise<{ deleted: number }> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/siem/events",
    method: "DELETE",
  });
}

export async function createSiemEvent(
  payload: SiemEventCreatePayload
): Promise<SiemEvent> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/siem/events",
    method: "POST",
    body: payload,
  });
}

// EDR Events
export interface EdrEvent {
  timestamp: string;
  hostname: string;
  username: string;
  event_type: string;
  process_name: string;
  action: string;
  severity: string;
  details: Record<string, unknown>;
}

export interface EdrEventCreatePayload {
  timestamp: string;
  hostname: string;
  username: string;
  event_type: string;
  process_name: string;
  action: string;
  severity: string;
  details?: Record<string, unknown>;
}

export async function listEdrEvents(): Promise<EdrEvent[]> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/edr/events",
  });
}

export async function clearEdrEvents(): Promise<{ deleted: number }> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/edr/events",
    method: "DELETE",
  });
}

export async function createEdrEvent(
  payload: EdrEventCreatePayload
): Promise<EdrEvent> {
  return apiFetch({
    baseUrl: API_BASE_URL,
    path: "/edr/events",
    method: "POST",
    body: payload,
  });
}
