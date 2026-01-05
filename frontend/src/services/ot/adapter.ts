import type {
  OtAsset,
  OtCommunication,
  OtDetection,
  OtPcapJob,
  OtSensor,
  OtSeverity,
  OtProtocol,
  OtAssetType,
  OtCriticality,
  OtDetectionStatus,
  OtDirection,
  PaginatedResponse,
  TimeRange,
} from "../../types/ot";

export interface OtOverviewResponse {
  kpis: {
    sensorsOnline: number;
    sensorsTotal: number;
    assets24h: number;
    assets7d: number;
    openDetectionsBySeverity: Record<OtSeverity, number>;
    newItToOt24h: number;
  };
  topDetections: OtDetection[];
  recentChanges: Array<{
    id: string;
    ts: string;
    type: "new_asset" | "new_protocol" | "new_path";
    message: string;
    site?: string;
    zone?: string;
  }>;
  topProtocols7d?: Array<{ protocol: OtProtocol; count: number }>;
}

export interface OtAdapter {
  getOtOverview(): Promise<OtOverviewResponse>;
  listOtAssets(params: {
    q?: string;
    site?: string;
    zone?: string;
    type?: OtAssetType;
    criticality?: OtCriticality;
    lastSeen?: TimeRange;
    page?: number;
    pageSize?: number;
  }): Promise<PaginatedResponse<OtAsset>>;
  getOtAsset(assetId: string): Promise<{
    asset: OtAsset;
    relatedDetections: OtDetection[];
    topCommunications: Array<{ peerIp: string; peerAssetId?: string; protocol: OtProtocol; count: number }>;
  }>;
  listOtCommunications(params: {
    q?: string;
    protocol?: OtProtocol;
    direction?: OtDirection;
    timeRange?: TimeRange;
    page?: number;
    pageSize?: number;
  }): Promise<PaginatedResponse<OtCommunication>>;
  listOtDetections(params: {
    q?: string;
    status?: OtDetectionStatus;
    severity?: OtSeverity;
    techniqueId?: string;
    timeRange?: TimeRange;
    sensorId?: string;
    assetId?: string;
    pcapJobId?: string;
    page?: number;
    pageSize?: number;
  }): Promise<PaginatedResponse<OtDetection>>;
  getOtDetection(id: string): Promise<OtDetection>;
  listOtSensors(): Promise<OtSensor[]>;
  getOtSensor(id: string): Promise<OtSensor>;
  createPcapJob(file: File): Promise<OtPcapJob>;
  listPcapJobs(): Promise<OtPcapJob[]>;
  getPcapJob(id: string): Promise<OtPcapJob>;
}
