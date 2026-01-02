import { create } from "zustand";
import type { AttackEvent, AttackType } from "./types";
import type { Aggregates } from "./ws_types";

type TooltipState = {
  x: number;
  y: number;
  event: AttackEvent;
};

type LiveState = "LIVE" | "STALE" | "OFFLINE" | "CONNECTING" | "WAITING";
type TransportState = "CONNECTING" | "OPEN" | "CLOSED";
type StreamState = "WAITING" | "LIVE" | "STALE";
type StreamMode = "raw" | "hybrid" | "agg_only";

type StoreState = {
  events: AttackEvent[];
  agg: Aggregates | null;
  liveState: LiveState;
  transportState: TransportState;
  streamState: StreamState;
  streamMode: StreamMode;
  lastServerHeartbeatTs: number | null;
  lastEventTs: number | null;

  windowKey: "5m" | "15m" | "1h";
  countryFilter: string;

  enabled: Record<AttackType, boolean>;
  majorOnly: boolean;
  minSeverity: number;
  tooltip: TooltipState | null;

  upsertEvent: (evt: AttackEvent) => void;
  setAgg: (agg: Aggregates) => void;
  noteHeartbeat: (serverTs?: string) => void;
  setTransportState: (s: TransportState) => void;
  setStreamState: (s: StreamState) => void;
  setLiveState: (s: LiveState) => void;
  setStreamMode: (m: StreamMode) => void;

  setWindowKey: (w: StoreState["windowKey"]) => void;
  setCountryFilter: (q: string) => void;

  setTooltip: (tooltip: TooltipState | null) => void;
  toggleType: (type: AttackType) => void;
  setMajorOnly: (value: boolean) => void;
  setMinSeverity: (value: number) => void;
};

const MAX_EVENTS = 6000;

const DEFAULT_ENABLED: Record<AttackType, boolean> = {
  Web: true,
  DDoS: true,
  Intrusion: true,
  Scanner: true,
  Anonymizer: true,
  Bot: true,
  Malware: true,
  Phishing: true,
  DNS: true,
  Email: true,
};

export const deriveLiveState = (transport: TransportState, stream: StreamState): LiveState => {
  if (transport === "CLOSED") return "OFFLINE";
  if (transport === "CONNECTING") return "CONNECTING";
  if (stream === "LIVE") return "LIVE";
  if (stream === "STALE") return "STALE";
  return "WAITING";
};

export const useThreatMapStore = create<StoreState>((set, get) => ({
  events: [],
  agg: null,
  liveState: "CONNECTING",
  transportState: "CONNECTING",
  streamState: "WAITING",
  streamMode: "raw",
  lastServerHeartbeatTs: null,
  lastEventTs: null,

  windowKey: "5m",
  countryFilter: "",

  enabled: DEFAULT_ENABLED,
  majorOnly: false,
  minSeverity: 3,
  tooltip: null,

  upsertEvent: (evt) => {
    const current = get().events;
    const idx = current.findIndex((e) => e.id === evt.id);
    const next = idx >= 0 ? [...current.slice(0, idx), evt, ...current.slice(idx + 1)] : [...current, evt];
    const trimmed = next.length > MAX_EVENTS ? next.slice(next.length - MAX_EVENTS) : next;
    set({ events: trimmed, lastEventTs: Date.now() });
  },
  setAgg: (agg) => set({ agg }),
  noteHeartbeat: (serverTs) => {
    const serverMs = serverTs ? Date.parse(serverTs) : NaN;
    set({ lastServerHeartbeatTs: Number.isFinite(serverMs) ? serverMs : Date.now() });
  },
  setTransportState: (transportState) => {
    const streamState = get().streamState;
    set({
      transportState,
      liveState: deriveLiveState(transportState, streamState),
    });
  },
  setStreamState: (streamState) => {
    const transportState = get().transportState;
    set({
      streamState,
      liveState: deriveLiveState(transportState, streamState),
    });
  },
  setLiveState: (liveState) => set({ liveState }),
  setStreamMode: (streamMode) => set({ streamMode }),

  setWindowKey: (windowKey) => set({ windowKey }),
  setCountryFilter: (countryFilter) => set({ countryFilter }),

  setTooltip: (tooltip) => set({ tooltip }),
  toggleType: (type) => set((state) => ({ enabled: { ...state.enabled, [type]: !state.enabled[type] } })),
  setMajorOnly: (value) => set({ majorOnly: value }),
  setMinSeverity: (value) => set({ minSeverity: value }),
}));
