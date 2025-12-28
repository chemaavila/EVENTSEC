import type { AttackEvent } from "./types";

export type HeatBucket = {
  lat_bin: number;
  lon_bin: number;
  count: number;
  severity_sum: number;
};

export type Aggregates = {
  window: string;
  server_ts: string;
  seq: number;

  count: number;
  eps: number;
  top_sources: [string, number][];
  top_targets: [string, number][];
  top_types: [string, number][];
  by_severity: [number, number][];
  heat: HeatBucket[];
};

export type ThreatWsMessage =
  | { type: "hb"; server_ts: string; seq: number }
  | { type: "mode"; server_ts: string; mode: "raw" | "hybrid" | "agg_only"; reason: string }
  | { type: "event"; server_ts: string; seq: number; payload: AttackEvent }
  | { type: "agg"; server_ts: string; seq: number; payload: Aggregates };


