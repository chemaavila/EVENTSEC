import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { DeckGL } from "@deck.gl/react";
import { Map } from "react-map-gl/maplibre";
import "maplibre-gl/dist/maplibre-gl.css";
import { makeLayers } from "./layers";
import { useThreatMapStore } from "./useThreatMapStore";
import { neonMapStyle } from "./neonMapStyle";
import { connectThreatWs } from "./ws";
import type { ThreatWsMessage } from "./ws_types";

const INITIAL_VIEW_STATE = {
  longitude: 6,
  latitude: 24,
  zoom: 1.35,
  pitch: 18,
  bearing: 0,
};

export default function ThreatMapCanvas() {
  const [viewState, setViewState] = useState(INITIAL_VIEW_STATE);
  const events = useThreatMapStore((state) => state.events);
  const agg = useThreatMapStore((state) => state.agg);
  const enabled = useThreatMapStore((state) => state.enabled);
  const majorOnly = useThreatMapStore((state) => state.majorOnly);
  const minSeverity = useThreatMapStore((state) => state.minSeverity);
  const setTooltip = useThreatMapStore((state) => state.setTooltip);
  const tooltip = useThreatMapStore((state) => state.tooltip);
  const upsertEvent = useThreatMapStore((state) => state.upsertEvent);
  const setAgg = useThreatMapStore((state) => state.setAgg);
  const noteHeartbeat = useThreatMapStore((state) => state.noteHeartbeat);
  const setLiveState = useThreatMapStore((state) => state.setLiveState);
  const setStreamMode = useThreatMapStore((state) => state.setStreamMode);
  const windowKey = useThreatMapStore((state) => state.windowKey);
  const countryFilter = useThreatMapStore((state) => state.countryFilter);
  const lastHeartbeatTs = useThreatMapStore((state) => state.lastHeartbeatTs);
  const [nowMs, setNowMs] = useState(Date.now());
  const [viewQuery, setViewQuery] = useState("");
  const wsRef = useRef<ReturnType<typeof connectThreatWs> | null>(null);

  useEffect(() => {
    let raf = 0;
    const tick = () => {
      setNowMs(Date.now());
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);

  useEffect(() => {
    // STALE detection driven strictly by server hb cadence; never synthesize events.
    const h = globalThis.setInterval(() => {
      if (!lastHeartbeatTs) return;
      const age = Date.now() - lastHeartbeatTs;
      if (age > 10_000) {
        setLiveState("STALE");
      } else {
        setLiveState("LIVE");
      }
    }, 1000);
    return () => globalThis.clearInterval(h);
  }, [lastHeartbeatTs, setLiveState]);

  useEffect(() => {
    // STRICT REAL-TIME: connect to backend WS and ingest only live events/aggregates.
    const wsUrl = (import.meta as any).env?.VITE_THREATMAP_WS_URL || "ws://localhost:8000/ws/threatmap";
    const client = connectThreatWs({
      url: wsUrl,
      onStatus: (s) => setLiveState(s),
      onMessage: (msg: ThreatWsMessage) => {
        if (msg.type === "hb") {
          noteHeartbeat();
          return;
        }
        if (msg.type === "mode") {
          setStreamMode(msg.mode);
          return;
        }
        if (msg.type === "event") {
          upsertEvent(msg.payload);
          return;
        }
        if (msg.type === "agg") {
          setAgg(msg.payload);
        }
      },
    });
    wsRef.current = client;

    // Periodically send client telemetry for backpressure.
    const telemHandle = globalThis.setInterval(() => {
      client.send({
        type: "client_telemetry",
        render_fps: 60, // best-effort; renderer FPS sampling can be added later
        queue_len: 0,
        dropped_events: 0,
      });
      client.send({
        type: "set_filters",
        window: windowKey,
        min_severity: minSeverity,
        major_only: majorOnly,
        types: Object.entries(enabled)
          .filter(([, v]) => v)
          .map(([k]) => k),
        country: countryFilter || null,
      });
    }, 1500);

    return () => {
      globalThis.clearInterval(telemHandle);
      client.close();
      wsRef.current = null;
    };
  }, [countryFilter, enabled, majorOnly, minSeverity, noteHeartbeat, setAgg, setLiveState, setStreamMode, upsertEvent, windowKey]);

  const handleHover = useCallback(
    (info: any) => {
      if (!info?.object) {
        setTooltip(null);
        return;
      }
      const event = info.object.evt ?? info.object.event ?? info.object;
      if (event) {
        setTooltip({ x: info.x, y: info.y, event });
      }
    },
    [setTooltip]
  );

  const layers = useMemo(
    () =>
      makeLayers({
        events,
        heat: agg?.heat ?? [],
        nowMs,
        enabled,
        majorOnly,
        minSeverity,
        onHover: handleHover,
      }),
    [events, agg, enabled, majorOnly, minSeverity, nowMs, handleHover]
  );

  const changeZoom = (delta: number) => {
    setViewState((prev) => ({ ...prev, zoom: Math.min(5, Math.max(0.8, prev.zoom + delta)) }));
  };

  const handleViewStateChange = (params: any) => {
    setViewState(params.viewState);
  };

  return (
    <div className="map-canvas">
      <DeckGL
        viewState={viewState}
        controller={{ inertia: 300, scrollZoom: true }}
        onViewStateChange={handleViewStateChange}
        layers={layers}
      >
        <Map mapStyle={neonMapStyle} attributionControl={false} />
      </DeckGL>
      <div className="map-gradient" aria-hidden="true" />
      <div className="map-search">
        <input
          type="text"
          placeholder="Search region, IP, or coordinates"
          value={viewQuery}
          onChange={(event) => setViewQuery(event.target.value)}
          aria-label="Search threat map"
        />
      </div>
      <div className="map-controls">
        <button type="button" className="btn btn-sm btn-ghost" onClick={() => changeZoom(0.5)}>
          +
        </button>
        <button type="button" className="btn btn-sm btn-ghost" onClick={() => changeZoom(-0.5)}>
          –
        </button>
      </div>
      {tooltip?.event && (
        <div className="map-tooltip" style={{ left: tooltip.x + 12, top: tooltip.y + 12 }}>
          <div className="k">Type</div>
          <div className="v">{tooltip.event.attack_type}</div>
          <div className="k">Severity</div>
          <div className="v">{tooltip.event.severity} / 10</div>
          <div className="k">Confidence</div>
          <div className="v">{Math.round((tooltip.event.confidence ?? 0) * 100)}%</div>
          <div className="k">Source</div>
          <div className="v">{tooltip.event.source}</div>
          <div className="k">Destination</div>
          <div className="v">
            {tooltip.event.dst?.geo?.country || "Unknown"} {tooltip.event.dst?.geo?.city ? `• ${tooltip.event.dst.geo.city}` : ""}
          </div>
        </div>
      )}
    </div>
  );
}

