function defaultApiBase(): string {
  if (typeof window !== "undefined" && window.location) {
    const { protocol, hostname } = window.location;
    return `${protocol}//${hostname}:8000`;
  }
  return "http://localhost:8000";
}

function resolveApiBase(): string {
  const rawValue = (import.meta.env.VITE_API_BASE_URL ?? "").trim();
  const fallback = defaultApiBase();

  if (!rawValue) {
    return fallback;
  }

  if (/^https?:\/\//i.test(rawValue)) {
    return rawValue;
  }

  if (typeof window !== "undefined" && rawValue.startsWith("//")) {
    return `${window.location.protocol}${rawValue}`;
  }

  try {
    const base = typeof window !== "undefined" ? window.location.origin : fallback;
    const resolved = new URL(rawValue, base);
    return resolved.origin + resolved.pathname.replace(/\/$/, "");
  } catch (err) {
    console.warn(
      "[api] Invalid VITE_API_BASE_URL value, falling back to default",
      rawValue,
      err
    );
    return fallback;
  }
}

const API_BASE_URL = resolveApiBase().replace(/\/$/, "");

function getHeaders(): HeadersInit {
  return {
    "Content-Type": "application/json",
  };
}

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

export interface ApiError extends Error {
  status?: number;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorMessage = `API error ${res.status}`;
    try {
      const text = await res.text();
      if (text) {
        try {
          const json = JSON.parse(text);
          errorMessage = json.detail || json.message || text;
        } catch {
          errorMessage = text;
        }
      }
    } catch {
      errorMessage = `API error ${res.status}`;
    }
    const error = new Error(errorMessage) as ApiError;
    error.status = res.status;
    throw error;
  }
  return (await res.json()) as T;
}

export async function login(email: string, password: string): Promise<{ access_token: string; user: UserProfile }> {
  const res = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: getHeaders(),
    credentials: "include",
    body: JSON.stringify({ email, password }),
  });
  return handleResponse(res);
}

export async function logout(): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/auth/logout`, {
    method: "POST",
    headers: getHeaders(),
    credentials: "include",
  });
  await handleResponse(res);
}

export async function listAlerts(): Promise<Alert[]> {
  const res = await fetch(`${API_BASE_URL}/alerts`, {
    headers: getHeaders(),
    credentials: "include",
  });
  return handleResponse<Alert[]>(res);
}

export async function getAlert(alertId: number): Promise<Alert> {
  const res = await fetch(`${API_BASE_URL}/alerts/${alertId}`, {
    headers: getHeaders(),
    credentials: "include",
  });
  return handleResponse<Alert>(res);
}

export async function createAlert(
  payload: AlertCreatePayload
): Promise<Alert> {
  const res = await fetch(`${API_BASE_URL}/alerts`, {
    method: "POST",
    headers: getHeaders(),
    credentials: "include",
    body: JSON.stringify(payload),
  });
  return handleResponse<Alert>(res);
}

export async function blockUrl(alertId: number, url: string): Promise<void> {
  const res = await fetch(
    `${API_BASE_URL}/alerts/${alertId}/block-url?url=${encodeURIComponent(url)}`,
    {
      method: "POST",
      headers: getHeaders(),
      credentials: "include",
    }
  );
  await handleResponse(res);
}

export async function unblockUrl(alertId: number, url: string): Promise<void> {
  const res = await fetch(
    `${API_BASE_URL}/alerts/${alertId}/unblock-url?url=${encodeURIComponent(url)}`,
    {
      method: "POST",
      headers: getHeaders(),
      credentials: "include",
    }
  );
  await handleResponse(res);
}

export async function blockSender(alertId: number, sender: string): Promise<void> {
  const res = await fetch(
    `${API_BASE_URL}/alerts/${alertId}/block-sender?sender=${encodeURIComponent(sender)}`,
    {
      method: "POST",
      headers: getHeaders(),
      credentials: "include",
    }
  );
  await handleResponse(res);
}

export async function unblockSender(alertId: number, sender: string): Promise<void> {
  const res = await fetch(
    `${API_BASE_URL}/alerts/${alertId}/unblock-sender?sender=${encodeURIComponent(sender)}`,
    {
      method: "POST",
      headers: getHeaders(),
      credentials: "include",
    }
  );
  await handleResponse(res);
}

export async function revokeUserSession(alertId: number, username: string): Promise<void> {
  const res = await fetch(
    `${API_BASE_URL}/alerts/${alertId}/revoke-session?username=${encodeURIComponent(username)}`,
    {
      method: "POST",
      headers: getHeaders(),
      credentials: "include",
    }
  );
  await handleResponse(res);
}

export async function isolateDevice(alertId: number, hostname: string): Promise<void> {
  const res = await fetch(
    `${API_BASE_URL}/alerts/${alertId}/isolate-device?hostname=${encodeURIComponent(hostname)}`,
    {
      method: "POST",
      headers: getHeaders(),
      credentials: "include",
    }
  );
  await handleResponse(res);
}

export async function getMyProfile(): Promise<UserProfile> {
  const res = await fetch(`${API_BASE_URL}/me`, {
    headers: getHeaders(),
    credentials: "include",
  });
  return handleResponse<UserProfile>(res);
}

export async function listEndpoints(): Promise<Endpoint[]> {
  const res = await fetch(`${API_BASE_URL}/endpoints`, {
    headers: getHeaders(),
    credentials: "include",
  });
  return handleResponse<Endpoint[]>(res);
}

export async function listAgents(): Promise<Agent[]> {
  const res = await fetch(`${API_BASE_URL}/agents`, {
    headers: getHeaders(),
    credentials: "include",
  });
  return handleResponse<Agent[]>(res);
}

export async function getEndpoint(endpointId: number): Promise<Endpoint> {
  const res = await fetch(`${API_BASE_URL}/endpoints/${endpointId}`, {
    headers: getHeaders(),
    credentials: "include",
  });
  return handleResponse<Endpoint>(res);
}

export async function getInventoryOverview(
  endpointId: number,
  category?: string
): Promise<InventoryOverview> {
  const query = category ? `?category=${encodeURIComponent(category)}` : "";
  const res = await fetch(`${API_BASE_URL}/inventory/${endpointId}${query}`, {
    headers: getHeaders(),
    credentials: "include",
  });
  return handleResponse<InventoryOverview>(res);
}

export async function listSandboxAnalyses(): Promise<SandboxAnalysisResult[]> {
  const res = await fetch(`${API_BASE_URL}/sandbox/analyses`, {
    headers: getHeaders(),
    credentials: "include",
  });
  return handleResponse<SandboxAnalysisResult[]>(res);
}

export async function analyzeSandbox(
  payload: SandboxAnalysisPayload
): Promise<SandboxAnalysisResult> {
  const res = await fetch(`${API_BASE_URL}/sandbox/analyze`, {
    method: "POST",
    headers: getHeaders(),
    credentials: "include",
    body: JSON.stringify(payload),
  });
  return handleResponse<SandboxAnalysisResult>(res);
}

export async function listUsers(): Promise<UserProfile[]> {
  const res = await fetch(`${API_BASE_URL}/users`, {
    headers: getHeaders(),
    credentials: "include",
  });
  return handleResponse<UserProfile[]>(res);
}

export async function createUser(payload: UserCreatePayload): Promise<UserProfile> {
  const res = await fetch(`${API_BASE_URL}/users`, {
    method: "POST",
    headers: getHeaders(),
    credentials: "include",
    body: JSON.stringify(payload),
  });
  return handleResponse<UserProfile>(res);
}

export async function updateUser(
  userId: number,
  payload: UserUpdatePayload
): Promise<UserProfile> {
  const res = await fetch(`${API_BASE_URL}/users/${userId}`, {
    method: "PATCH",
    headers: getHeaders(),
    credentials: "include",
    body: JSON.stringify(payload),
  });
  return handleResponse<UserProfile>(res);
}

export async function listHandovers(): Promise<Handover[]> {
  const res = await fetch(`${API_BASE_URL}/handover`, {
    headers: getHeaders(),
    credentials: "include",
  });
  return handleResponse<Handover[]>(res);
}

export async function createHandover(
  payload: HandoverCreatePayload
): Promise<Handover> {
  const res = await fetch(`${API_BASE_URL}/handover`, {
    method: "POST",
    headers: getHeaders(),
    credentials: "include",
    body: JSON.stringify(payload),
  });
  return handleResponse<Handover>(res);
}

export async function listWorkplans(): Promise<Workplan[]> {
  const res = await fetch(`${API_BASE_URL}/workplans`, {
    headers: getHeaders(),
    credentials: "include",
  });
  return handleResponse<Workplan[]>(res);
}

export async function createWorkplan(
  payload: WorkplanCreatePayload
): Promise<Workplan> {
  const res = await fetch(`${API_BASE_URL}/workplans`, {
    method: "POST",
    headers: getHeaders(),
    credentials: "include",
    body: JSON.stringify(payload),
  });
  return handleResponse<Workplan>(res);
}

export async function updateWorkplan(
  workplanId: number,
  payload: WorkplanUpdatePayload
): Promise<Workplan> {
  const res = await fetch(`${API_BASE_URL}/workplans/${workplanId}`, {
    method: "PATCH",
    headers: getHeaders(),
    credentials: "include",
    body: JSON.stringify(payload),
  });
  return handleResponse<Workplan>(res);
}

export async function listWarRoomNotes(alertId?: number): Promise<WarRoomNote[]> {
  const query = alertId ? `?alert_id=${alertId}` : "";
  const res = await fetch(`${API_BASE_URL}/warroom/notes${query}`, {
    headers: getHeaders(),
    credentials: "include",
  });
  return handleResponse<WarRoomNote[]>(res);
}

export async function createWarRoomNote(
  payload: WarRoomNoteCreatePayload
): Promise<WarRoomNote> {
  const res = await fetch(`${API_BASE_URL}/warroom/notes`, {
    method: "POST",
    headers: getHeaders(),
    credentials: "include",
    body: JSON.stringify(payload),
  });
  return handleResponse<WarRoomNote>(res);
}

export async function listIndicators(): Promise<Indicator[]> {
  const res = await fetch(`${API_BASE_URL}/indicators`, {
    headers: getHeaders(),
    credentials: "include",
  });
  return handleResponse<Indicator[]>(res);
}

export async function createIndicator(
  payload: IndicatorCreatePayload
): Promise<Indicator> {
  const res = await fetch(`${API_BASE_URL}/indicators`, {
    method: "POST",
    headers: getHeaders(),
    credentials: "include",
    body: JSON.stringify(payload),
  });
  return handleResponse<Indicator>(res);
}

export async function updateIndicator(
  indicatorId: number,
  payload: IndicatorUpdatePayload
): Promise<Indicator> {
  const res = await fetch(`${API_BASE_URL}/indicators/${indicatorId}`, {
    method: "PATCH",
    headers: getHeaders(),
    credentials: "include",
    body: JSON.stringify(payload),
  });
  return handleResponse<Indicator>(res);
}

export async function listBiocRules(): Promise<BiocRule[]> {
  const res = await fetch(`${API_BASE_URL}/biocs`, {
    headers: getHeaders(),
    credentials: "include",
  });
  return handleResponse<BiocRule[]>(res);
}

export async function createBiocRule(
  payload: BiocRulePayload
): Promise<BiocRule> {
  const res = await fetch(`${API_BASE_URL}/biocs`, {
    method: "POST",
    headers: getHeaders(),
    credentials: "include",
    body: JSON.stringify(payload),
  });
  return handleResponse<BiocRule>(res);
}

export async function updateBiocRule(
  ruleId: number,
  payload: BiocRuleUpdatePayload
): Promise<BiocRule> {
  const res = await fetch(`${API_BASE_URL}/biocs/${ruleId}`, {
    method: "PATCH",
    headers: getHeaders(),
    credentials: "include",
    body: JSON.stringify(payload),
  });
  return handleResponse<BiocRule>(res);
}

export async function listAnalyticsRules(): Promise<AnalyticsRule[]> {
  const res = await fetch(`${API_BASE_URL}/analytics/rules`, {
    headers: getHeaders(),
    credentials: "include",
  });
  return handleResponse<AnalyticsRule[]>(res);
}

export async function getAnalyticsRule(ruleId: number): Promise<AnalyticsRule> {
  const res = await fetch(`${API_BASE_URL}/analytics/rules/${ruleId}`, {
    headers: getHeaders(),
    credentials: "include",
  });
  return handleResponse<AnalyticsRule>(res);
}

export async function createAnalyticsRule(
  payload: AnalyticsRulePayload
): Promise<AnalyticsRule> {
  const res = await fetch(`${API_BASE_URL}/analytics/rules`, {
    method: "POST",
    headers: getHeaders(),
    credentials: "include",
    body: JSON.stringify(payload),
  });
  return handleResponse<AnalyticsRule>(res);
}

export async function updateAnalyticsRule(
  ruleId: number,
  payload: AnalyticsRuleUpdatePayload
): Promise<AnalyticsRule> {
  const res = await fetch(`${API_BASE_URL}/analytics/rules/${ruleId}`, {
    method: "PATCH",
    headers: getHeaders(),
    credentials: "include",
    body: JSON.stringify(payload),
  });
  return handleResponse<AnalyticsRule>(res);
}

export async function listYaraRules(): Promise<YaraRule[]> {
  const res = await fetch(`${API_BASE_URL}/yara/rules`, {
    headers: getHeaders(),
    credentials: "include",
  });
  return handleResponse<YaraRule[]>(res);
}

export async function listNetworkEvents(): Promise<NetworkEvent[]> {
  const res = await fetch(`${API_BASE_URL}/network/events`, {
    headers: getHeaders(),
    credentials: "include",
  });
  return handleResponse<NetworkEvent[]>(res);
}

export async function createNetworkEvent(
  payload: NetworkEventCreatePayload
): Promise<NetworkEvent> {
  const res = await fetch(`${API_BASE_URL}/network/events`, {
    method: "POST",
    headers: getHeaders(),
    credentials: "include",
    body: JSON.stringify(payload),
  });
  return handleResponse<NetworkEvent>(res);
}

export async function searchEvents(
  params: SearchEventsParams = {}
): Promise<IndexedEvent[]> {
  const searchParams = new URLSearchParams();
  if (params.query) {
    searchParams.set("query", params.query);
  }
  if (params.severity) {
    searchParams.set("severity", params.severity);
  }
  if (params.size) {
    searchParams.set("size", params.size.toString());
  }
  const qs = searchParams.toString();
  const url = `${API_BASE_URL}/events${qs ? `?${qs}` : ""}`;
  const res = await fetch(url, {
    headers: getHeaders(),
    credentials: "include",
  });
  return handleResponse<IndexedEvent[]>(res);
}

export async function runKqlQuery(payload: KqlQueryPayload): Promise<KqlQueryResponse> {
  const res = await fetch(`${API_BASE_URL}/search/kql`, {
    method: "POST",
    headers: getHeaders(),
    credentials: "include",
    body: JSON.stringify(payload),
  });
  return handleResponse<KqlQueryResponse>(res);
}

export async function listEndpointActions(
  endpointId: number
): Promise<EndpointAction[]> {
  const res = await fetch(`${API_BASE_URL}/endpoints/${endpointId}/actions`, {
    headers: getHeaders(),
    credentials: "include",
  });
  return handleResponse<EndpointAction[]>(res);
}

export async function createEndpointAction(
  endpointId: number,
  payload: EndpointActionCreatePayload
): Promise<EndpointAction> {
  const res = await fetch(`${API_BASE_URL}/endpoints/${endpointId}/actions`, {
    method: "POST",
    headers: getHeaders(),
    credentials: "include",
    body: JSON.stringify(payload),
  });
  return handleResponse<EndpointAction>(res);
}

export async function updateAlert(
  alertId: number,
  payload: Partial<{ status: AlertStatus; assigned_to: number | null; conclusion: string | null }>
): Promise<Alert> {
  const res = await fetch(`${API_BASE_URL}/alerts/${alertId}`, {
    method: "PATCH",
    headers: getHeaders(),
    credentials: "include",
    body: JSON.stringify(payload),
  });
  return handleResponse<Alert>(res);
}

export async function escalateAlert(
  alertId: number,
  payload: AlertEscalationPayload
): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/alerts/${alertId}/escalate`, {
    method: "POST",
    headers: getHeaders(),
    credentials: "include",
    body: JSON.stringify({ alert_id: alertId, ...payload }),
  });
  await handleResponse(res);
}

export async function deleteAlert(alertId: number): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/alerts/${alertId}`, {
    method: "DELETE",
    headers: getHeaders(),
    credentials: "include",
  });
  await handleResponse(res);
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
  const res = await fetch(`${API_BASE_URL}/siem/events`, {
    headers: getHeaders(),
    credentials: "include",
  });
  return handleResponse<SiemEvent[]>(res);
}

export async function clearSiemEvents(): Promise<{ deleted: number }> {
  const res = await fetch(`${API_BASE_URL}/siem/events`, {
    method: "DELETE",
    headers: getHeaders(),
    credentials: "include",
  });
  return handleResponse<{ deleted: number }>(res);
}

export async function createSiemEvent(
  payload: SiemEventCreatePayload
): Promise<SiemEvent> {
  const res = await fetch(`${API_BASE_URL}/siem/events`, {
    method: "POST",
    headers: getHeaders(),
    credentials: "include",
    body: JSON.stringify(payload),
  });
  return handleResponse<SiemEvent>(res);
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
  const res = await fetch(`${API_BASE_URL}/edr/events`, {
    headers: getHeaders(),
    credentials: "include",
  });
  return handleResponse<EdrEvent[]>(res);
}

export async function clearEdrEvents(): Promise<{ deleted: number }> {
  const res = await fetch(`${API_BASE_URL}/edr/events`, {
    method: "DELETE",
    headers: getHeaders(),
    credentials: "include",
  });
  return handleResponse<{ deleted: number }>(res);
}

export async function createEdrEvent(
  payload: EdrEventCreatePayload
): Promise<EdrEvent> {
  const res = await fetch(`${API_BASE_URL}/edr/events`, {
    method: "POST",
    headers: getHeaders(),
    credentials: "include",
    body: JSON.stringify(payload),
  });
  return handleResponse<EdrEvent>(res);
}
