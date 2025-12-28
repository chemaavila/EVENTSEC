import { ArcLayer, LineLayer, ScatterplotLayer } from "@deck.gl/layers";
import { TripsLayer } from "@deck.gl/geo-layers";
import type { AttackEvent } from "./types";
import { buildPath } from "./path";
import type { HeatBucket } from "./ws_types";

const clamp01 = (value: number) => Math.max(0, Math.min(1, value));
type RGBAColor = [number, number, number, number];

export function makeLayers(args: {
  events: AttackEvent[];
  heat: HeatBucket[];
  nowMs: number;
  enabled: Record<string, boolean>;
  majorOnly: boolean;
  minSeverity: number;
  onHover: (info: any) => void;
}) {
  const { events, heat, nowMs, enabled, majorOnly, minSeverity, onHover } = args;

  const live = events
    .filter((evt) => enabled[evt.attack_type])
    .filter(
      (evt) =>
        evt.src?.geo?.lon != null &&
        evt.src?.geo?.lat != null &&
        evt.dst?.geo?.lon != null &&
        evt.dst?.geo?.lat != null
    )
    .filter((evt) => !majorOnly || evt.severity >= 7)
    .filter((evt) => evt.severity >= minSeverity)
    .map((evt) => {
      const tsMs = Date.parse(evt.ts);
      const expMs = Date.parse(evt.expires_at);
      const ttlMs = Math.max(1, evt.ttl_ms || 1);
      const remaining = expMs - nowMs;
      const life = clamp01(remaining / ttlMs);
      const age = nowMs - tsMs;
      return { evt, timestamp: tsMs, age, life };
    })
    .filter((item) => item.life > 0);

  const MAX_VISIBLE = 1800;
  const visible = live.length > MAX_VISIBLE ? live.slice(live.length - MAX_VISIBLE) : live;

  const arcColor = (severity: number, alpha: number): RGBAColor => {
    const t = clamp01((severity - 1) / 9);
    const r = Math.round(40 + 200 * t);
    const g = Math.round(190 - 80 * t);
    const b = Math.round(220 - 160 * t);
    return [r, g, b, Math.round(255 * alpha)];
  };

  const arcs = new ArcLayer({
    id: "suspicious-arcs",
    data: visible,
    pickable: true,
    getSourcePosition: (item: any) => [item.evt.src.geo.lon, item.evt.src.geo.lat],
    getTargetPosition: (item: any) => [item.evt.dst.geo.lon, item.evt.dst.geo.lat],
    getWidth: (item: any) => 1 + Math.floor(item.evt.severity / 2),
    getSourceColor: (item: any) => arcColor(item.evt.severity, 0.75 * item.life),
    getTargetColor: (item: any) => arcColor(item.evt.severity, 0.95 * item.life),
    onHover,
    updateTriggers: { getSourceColor: nowMs, getTargetColor: nowMs },
  });

  const tripData = visible.map((item: any) => {
    const src: [number, number] = [item.evt.src.geo.lon, item.evt.src.geo.lat];
    const dst: [number, number] = [item.evt.dst.geo.lon, item.evt.dst.geo.lat];
    const path = buildPath(src, dst, 28);
    const start = item.timestamp;
    const travelMs = 1200 + (10 - item.evt.severity) * 120;
    const step = travelMs / (path.length - 1);
    const timestamps = path.map((_, index) => start + index * step);
    return { ...item, path, timestamps, start, travelMs };
  });

  const trips = new TripsLayer({
    id: "event-trips",
    data: tripData,
    getPath: (item: any) => item.path,
    getTimestamps: (item: any) => item.timestamps,
    currentTime: nowMs,
    trailLength: 800,
    widthMinPixels: 2,
    getColor: (item: any) => arcColor(item.evt.severity, item.life),
    opacity: 0.9,
    pickable: false,
    updateTriggers: { currentTime: nowMs, getColor: nowMs },
  });

  const pulsesSrc = visible
    .slice(-260)
    .map((item: any) => {
      const impactT = item.timestamp + (1200 + (10 - item.evt.severity) * 120);
      const impactAge = nowMs - impactT;
      const pulseLife = 1 - clamp01(impactAge / 900);
      const radius = 12000 + (1 - pulseLife) * 55000;
      return { ...item, impactAge, pulseLife, radius };
    })
    .filter((item: any) => item.impactAge >= 0 && item.impactAge <= 900);

  const pulses = new ScatterplotLayer({
    id: "impact-pulses",
    data: pulsesSrc,
    getPosition: (item: any) => [item.evt.dst.geo.lon, item.evt.dst.geo.lat],
    getRadius: (item: any) => item.radius,
    radiusUnits: "meters",
    getFillColor: (item: any) => arcColor(item.evt.severity, 0.1 * item.pulseLife),
    getLineColor: (item: any) => arcColor(item.evt.severity, 0.35 * item.pulseLife),
    lineWidthUnits: "pixels",
    getLineWidth: 1.5,
    stroked: true,
    filled: true,
    pickable: false,
    updateTriggers: { getRadius: nowMs, getFillColor: nowMs, getLineColor: nowMs },
  });

  const markers = new ScatterplotLayer({
    id: "final-markers",
    data: visible.slice(-500),
    getPosition: (item: any) => [item.evt.dst.geo.lon, item.evt.dst.geo.lat],
    getRadius: (item: any) => 5000 + item.evt.severity * 2200,
    radiusUnits: "meters",
    getFillColor: (item: any) => arcColor(item.evt.severity, 0.12 * item.life),
    pickable: false,
    updateTriggers: { getFillColor: nowMs },
  });

  // Holographic lat/lon grid (subtle, premium)
  const gridLines: { source: [number, number]; target: [number, number]; strength: number }[] = [];
  for (let lon = -180; lon <= 180; lon += 20) {
    gridLines.push({ source: [lon, -70], target: [lon, 70], strength: lon % 40 === 0 ? 1 : 0.6 });
  }
  for (let lat = -60; lat <= 60; lat += 20) {
    gridLines.push({ source: [-180, lat], target: [180, lat], strength: lat % 40 === 0 ? 1 : 0.6 });
  }

  const grid = new LineLayer({
    id: "holo-grid",
    data: gridLines,
    getSourcePosition: (d: any) => d.source,
    getTargetPosition: (d: any) => d.target,
    getColor: (d: any) => [0, 229, 255, Math.round(55 * d.strength)],
    getWidth: (d: any) => (d.strength > 0.9 ? 1.2 : 0.9),
    widthUnits: "pixels",
    pickable: false,
  });

  // Heat buckets (server authoritative). Render as soft additive dots at bucket centers.
  const heatPts = (heat || []).map((b) => ({
    lon: b.lon_bin * 5 + 2.5,
    lat: b.lat_bin * 5 + 2.5,
    count: b.count,
    sev: b.severity_sum,
  }));

  const heatLayer = new ScatterplotLayer({
    id: "heat",
    data: heatPts,
    getPosition: (d: any) => [d.lon, d.lat],
    getRadius: (d: any) => 18_000 + Math.min(120_000, d.count * 6_500),
    radiusUnits: "meters",
    getFillColor: (d: any) => [124, 58, 237, Math.min(160, 18 + d.count * 4)],
    opacity: 0.55,
    stroked: false,
    pickable: false,
  });

  return [grid, heatLayer, arcs, trips, pulses, markers];
}

