import type { OtAdapter, OtOverviewResponse } from "./adapter";
import type {
  OtCriticality,
  OtDetection,
  OtDetectionStatus,
  OtDirection,
  OtPcapJob,
  OtProtocol,
  OtSeverity,
  PaginatedResponse,
  TimeRange,
} from "../../types/ot";
import {
  otAssets,
  otCommunications,
  otDetections,
  otPcapJobs,
  otSensors,
  severityCounts,
  topProtocols7d,
} from "../../mocks/otMockData";

const sleep = (ms: number) => new Promise((resolve) => globalThis.setTimeout(resolve, ms));

const baseTime = Date.now();
const minutesAgo = (minutes: number) => new Date(baseTime - minutes * 60_000).toISOString();
const hoursAgo = (hours: number) => new Date(baseTime - hours * 3_600_000).toISOString();

const normalize = (value: string) => value.trim().toLowerCase();

const matchesQuery = (value: string, query?: string) => {
  if (!query) return true;
  return normalize(value).includes(normalize(query));
};

const matchesArrayQuery = (values: Array<string | undefined>, query?: string) => {
  if (!query) return true;
  return values.some((value) => value && matchesQuery(value, query));
};

const withinTimeRange = (ts: string, range?: TimeRange) => {
  if (!range) return true;
  const timestamp = new Date(ts).getTime();
  if (Number.isNaN(timestamp)) return false;

  if (range.preset) {
    const now = baseTime;
    const msByPreset: Record<NonNullable<TimeRange["preset"]>, number> = {
      "24h": 86_400_000,
      "7d": 7 * 86_400_000,
      "30d": 30 * 86_400_000,
    };
    return timestamp >= now - msByPreset[range.preset];
  }

  const from = range.from ? new Date(range.from).getTime() : undefined;
  const to = range.to ? new Date(range.to).getTime() : undefined;
  if (from !== undefined && timestamp < from) return false;
  if (to !== undefined && timestamp > to) return false;
  return true;
};

const paginate = <T,>(items: T[], page = 1, pageSize = 10): PaginatedResponse<T> => {
  const normalizedPage = Math.max(1, page);
  const normalizedSize = Math.max(1, pageSize);
  const start = (normalizedPage - 1) * normalizedSize;
  const end = start + normalizedSize;
  return {
    items: items.slice(start, end),
    page: normalizedPage,
    pageSize: normalizedSize,
    total: items.length,
  };
};

const assetMap = new Map(otAssets.map((asset) => [asset.id, asset]));
const sensorMap = new Map(otSensors.map((sensor) => [sensor.id, sensor]));

let pcapJobsStore: OtPcapJob[] = [...otPcapJobs];

const createJobId = () => `pcap-${Date.now().toString(36)}`;

const defaultLatency = 320;

const maybeThrowError = (query?: string) => {
  if (query && normalize(query) === "__error__") {
    throw new Error("Simulated OT mock error");
  }
};

const listAssets = (params: {
  q?: string;
  site?: string;
  zone?: string;
  type?: string;
  criticality?: OtCriticality;
  lastSeen?: TimeRange;
}) => {
  return otAssets.filter((asset) => {
    if (params.site && asset.site !== params.site) return false;
    if (params.zone && asset.zone !== params.zone) return false;
    if (params.type && asset.assetType !== params.type) return false;
    if (params.criticality && asset.criticality !== params.criticality) return false;
    if (!withinTimeRange(asset.lastSeen, params.lastSeen)) return false;
    return matchesArrayQuery(
      [asset.name, asset.ip, asset.vendor, asset.model, ...asset.tags],
      params.q
    );
  });
};

const listCommunications = (params: {
  q?: string;
  protocol?: OtProtocol;
  direction?: OtDirection;
  timeRange?: TimeRange;
}) => {
  return otCommunications.filter((comm) => {
    if (params.protocol && comm.protocol !== params.protocol) return false;
    if (params.direction && comm.direction !== params.direction) return false;
    if (!withinTimeRange(comm.ts, params.timeRange)) return false;
    const srcAsset = comm.srcAssetId ? assetMap.get(comm.srcAssetId) : undefined;
    const dstAsset = comm.dstAssetId ? assetMap.get(comm.dstAssetId) : undefined;
    return matchesArrayQuery(
      [
        comm.srcIp,
        comm.dstIp,
        comm.summary,
        srcAsset?.name,
        dstAsset?.name,
        comm.protocol,
      ],
      params.q
    );
  });
};

const listDetections = (params: {
  q?: string;
  status?: OtDetectionStatus;
  severity?: OtSeverity;
  techniqueId?: string;
  timeRange?: TimeRange;
  sensorId?: string;
  assetId?: string;
  pcapJobId?: string;
}) => {
  return otDetections.filter((det) => {
    if (params.status && det.status !== params.status) return false;
    if (params.severity && det.severity !== params.severity) return false;
    if (params.sensorId && det.sensorId !== params.sensorId) return false;
    if (params.assetId && !det.assetIds.includes(params.assetId)) return false;
    if (params.pcapJobId && det.pcapJobId !== params.pcapJobId) return false;
    if (params.techniqueId && det.technique?.techniqueId !== params.techniqueId) return false;
    if (!withinTimeRange(det.ts, params.timeRange)) return false;
    return matchesArrayQuery([det.title, det.description, det.technique?.techniqueName], params.q);
  });
};

export function createMockAdapter(): OtAdapter {
  return {
    async getOtOverview(): Promise<OtOverviewResponse> {
      await sleep(defaultLatency);
      const sensorsOnline = otSensors.filter((sensor) => sensor.status === "online").length;
      const sensorsTotal = otSensors.length;
      const assets24h = otAssets.filter((asset) => withinTimeRange(asset.lastSeen, { preset: "24h" })).length;
      const assets7d = otAssets.filter((asset) => withinTimeRange(asset.lastSeen, { preset: "7d" })).length;
      const openDetections = otDetections.filter((det) => det.status !== "closed");
      const newItToOt24h = otCommunications.filter(
        (comm) => comm.direction === "IT->OT" && withinTimeRange(comm.ts, { preset: "24h" })
      ).length;

      return {
        kpis: {
          sensorsOnline,
          sensorsTotal,
          assets24h,
          assets7d,
          openDetectionsBySeverity: severityCounts(openDetections),
          newItToOt24h,
        },
        topDetections: [...otDetections]
          .sort((a, b) => new Date(b.ts).getTime() - new Date(a.ts).getTime())
          .slice(0, 10),
        recentChanges: [
          {
            id: "change-1",
            ts: minutesAgo(4),
            type: "new_asset",
            message: "New asset PLC-002 discovered",
            site: "HQ",
            zone: "Level 1",
          },
          {
            id: "change-2",
            ts: minutesAgo(22),
            type: "new_protocol",
            message: "New protocol observed: OPC UA",
            site: "HQ",
            zone: "Level 3",
          },
          {
            id: "change-3",
            ts: hoursAgo(1),
            type: "new_path",
            message: "New IT → OT communication path detected",
            site: "Plant West",
            zone: "Cell 3",
          },
        ],
        topProtocols7d: topProtocols7d.map((entry) => ({
          protocol: entry.protocol,
          count: entry.count,
        })),
      };
    },

    async listOtAssets(params) {
      maybeThrowError(params.q);
      await sleep(defaultLatency);
      const filtered = listAssets(params).sort(
        (a, b) => new Date(b.lastSeen).getTime() - new Date(a.lastSeen).getTime()
      );
      return paginate(filtered, params.page, params.pageSize ?? 10);
    },

    async getOtAsset(assetId: string) {
      await sleep(defaultLatency);
      const asset = assetMap.get(assetId);
      if (!asset) throw new Error("Asset not found");

      const relatedDetections = otDetections.filter((det) => det.assetIds.includes(assetId));

      const communications = otCommunications.filter(
        (comm) => comm.srcAssetId === assetId || comm.dstAssetId === assetId
      );

      const peerCounts = new Map<
        string,
        { peerAssetId?: string; peerIp: string; protocol: OtProtocol; count: number }
      >();
      communications.forEach((comm) => {
        const peerAssetId = comm.srcAssetId === assetId ? comm.dstAssetId : comm.srcAssetId;
        const peerIp = comm.srcAssetId === assetId ? comm.dstIp : comm.srcIp;
        const key = `${peerIp}-${comm.protocol}`;
        const existing =
          peerCounts.get(key) ?? {
            peerAssetId,
            peerIp,
            protocol: comm.protocol,
            count: 0,
          };
        peerCounts.set(key, { ...existing, count: existing.count + 1 });
      });

      const topCommunications = Array.from(peerCounts.values()).map((data) => ({
        peerIp: data.peerIp,
        peerAssetId: data.peerAssetId,
        protocol: data.protocol,
        count: data.count,
      }));

      return { asset, relatedDetections, topCommunications };
    },

    async listOtCommunications(params) {
      maybeThrowError(params.q);
      await sleep(defaultLatency);
      const filtered = listCommunications(params).sort(
        (a, b) => new Date(b.ts).getTime() - new Date(a.ts).getTime()
      );
      return paginate(filtered, params.page, params.pageSize ?? 10);
    },

    async listOtDetections(params) {
      maybeThrowError(params.q);
      await sleep(defaultLatency);
      const filtered = listDetections(params).sort(
        (a, b) => new Date(b.ts).getTime() - new Date(a.ts).getTime()
      );
      return paginate(filtered, params.page, params.pageSize ?? 10);
    },

    async getOtDetection(id: string): Promise<OtDetection> {
      await sleep(defaultLatency);
      const detection = otDetections.find((det) => det.id === id);
      if (!detection) throw new Error("Detection not found");
      return detection;
    },

    async listOtSensors() {
      await sleep(defaultLatency);
      return [...otSensors];
    },

    async getOtSensor(id: string) {
      await sleep(defaultLatency);
      const sensor = sensorMap.get(id);
      if (!sensor) throw new Error("Sensor not found");
      return sensor;
    },

    async createPcapJob(file: File) {
      await sleep(defaultLatency);
      const created: OtPcapJob = {
        id: createJobId(),
        filename: file.name,
        uploadedAt: new Date(baseTime).toISOString(),
        status: "queued",
        stats: {
          flows: 0,
          protocols: {},
          detections: 0,
          assetsDiscovered: 0,
        },
      };

      pcapJobsStore = [created, ...pcapJobsStore];

      globalThis.setTimeout(() => {
        pcapJobsStore = pcapJobsStore.map((job) =>
          job.id === created.id
            ? { ...job, status: "running" }
            : job
        );
      }, 500);

      globalThis.setTimeout(() => {
        pcapJobsStore = pcapJobsStore.map((job) =>
          job.id === created.id
            ? {
                ...job,
                status: "done",
                stats: {
                  flows: 920,
                  protocols: { Modbus: 180, DNP3: 70, OPCUA: 40 },
                  detections: 2,
                  assetsDiscovered: 12,
                },
              }
            : job
        );
      }, 1400);

      return created;
    },

    async listPcapJobs() {
      await sleep(defaultLatency);
      return [...pcapJobsStore].sort(
        (a, b) => new Date(b.uploadedAt).getTime() - new Date(a.uploadedAt).getTime()
      );
    },

    async getPcapJob(id: string) {
      await sleep(defaultLatency);
      const job = pcapJobsStore.find((entry) => entry.id === id);
      if (!job) throw new Error("PCAP job not found");
      return job;
    },
  };
}
