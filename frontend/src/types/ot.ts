export type OtSensorStatus = "online" | "offline" | "degraded";
export type OtIngestMethod = "http" | "beats" | "file";

export type OtAssetType = "PLC" | "HMI" | "RTU" | "Server" | "Switch" | "Unknown";
export type OtCriticality = "low" | "med" | "high";

export type OtProtocol = "Modbus" | "DNP3" | "BACnet" | "S7" | "OPCUA" | "Unknown";
export type OtDirection = "IT->OT" | "OT->OT" | "OT->IT";

export type OtSeverity = "low" | "med" | "high" | "critical";
export type OtDetectionStatus = "open" | "in_progress" | "closed";

export type OtPcapJobStatus = "queued" | "running" | "done" | "failed";

export interface OtSensor {
  id: string;
  name: string;
  site: string;
  zone: string;
  status: OtSensorStatus;
  lastSeen: string;
  version: string;
  capabilities: { zeek: boolean; icsnpp: boolean; acid: boolean; suricata?: boolean };
  ingest: { method: OtIngestMethod; endpoint?: string };
}

export interface OtAsset {
  id: string;
  name: string;
  ip: string;
  mac?: string;
  vendor?: string;
  model?: string;
  firmware?: string;
  assetType: OtAssetType;
  site: string;
  zone: string;
  criticality: OtCriticality;
  firstSeen: string;
  lastSeen: string;
  tags: string[];
}

export interface OtCommunication {
  id: string;
  ts: string;
  srcIp: string;
  dstIp: string;
  srcAssetId?: string;
  dstAssetId?: string;
  protocol: OtProtocol;
  port: number;
  direction: OtDirection;
  summary: string;
  bytes?: number;
  packets?: number;
}

export interface OtTechnique {
  framework: "MITRE_ICS";
  tactic?: string;
  techniqueId?: string;
  techniqueName?: string;
}

export interface OtEvidenceKV {
  key: string;
  value: string;
}

export interface OtDetection {
  id: string;
  ts: string;
  severity: OtSeverity;
  status: OtDetectionStatus;
  title: string;
  description: string;
  sensorId: string;
  assetIds: string[];
  technique?: OtTechnique;
  evidence: OtEvidenceKV[];
  pcapJobId?: string;
}

export interface OtPcapJob {
  id: string;
  filename: string;
  uploadedAt: string;
  status: OtPcapJobStatus;
  stats: {
    flows: number;
    protocols: Record<string, number>;
    detections: number;
    assetsDiscovered: number;
  };
  error?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  page: number;
  pageSize: number;
  total: number;
}

export interface TimeRange {
  from?: string;
  to?: string;
  preset?: "24h" | "7d" | "30d";
}
