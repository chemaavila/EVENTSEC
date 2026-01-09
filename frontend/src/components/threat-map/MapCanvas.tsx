import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { DeckGL } from "@deck.gl/react";
import { Map } from "react-map-gl/maplibre";
import "maplibre-gl/dist/maplibre-gl.css";
import { makeLayers } from "./layers";
import { useThreatMapStore } from "./useThreatMapStore";
import { buildNeonMapStyle } from "./neonMapStyle";
import { API_BASE_URL, resolveWsUrl } from "../../config/endpoints";
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
  const transportState = useThreatMapStore((state) => state.transportState);
  const streamState = useThreatMapStore((state) => state.streamState);
  const setTransportState = useThreatMapStore((state) => state.setTransportState);
  const setStreamState = useThreatMapStore((state) => state.setStreamState);
  const setStreamMode = useThreatMapStore((state) => state.setStreamMode);
  const windowKey = useThreatMapStore((state) => state.windowKey);
  const countryFilter = useThreatMapStore((state) => state.countryFilter);
  const lastServerHeartbeatTs = useThreatMapStore((state) => state.lastServerHeartbeatTs);
  const [nowMs, setNowMs] = useState(Date.now());
  const [viewQuery, setViewQuery] = useState("");
  const wsRef = useRef<ReturnType<typeof connectThreatWs> | null>(null);
  const invalidMessageCount = useRef(0);

  const staleThresholdMs = useMemo(() => {
    const raw = Number.parseInt(import.meta.env.VITE_THREATMAP_STALE_MS ?? "", 10);
    return Number.isFinite(raw) ? raw : 10_000;
  }, []);

  const debugEnabled = useMemo(
    () => (import.meta.env.VITE_UI_DEBUG ?? "false") === "true",
    []
  );

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
      if (transportState !== "OPEN") return;
      if (!lastServerHeartbeatTs) {
        if (streamState !== "WAITING") {
          setStreamState("WAITING");
        }
        return;
      }
      const age = Date.now() - lastServerHeartbeatTs;
      if (age > staleThresholdMs) {
        if (streamState !== "STALE") {
          setStreamState("STALE");
        }
      } else if (streamState !== "LIVE") {
        setStreamState("LIVE");
      }
    }, 1000);
    return () => globalThis.clearInterval(h);
  }, [lastServerHeartbeatTs, setStreamState, staleThresholdMs, streamState, transportState]);

  useEffect(() => {
    let cancelled = false;
    const fetchPoints = async () => {
      try {
        const response = await fetch(
          `${API_BASE_URL}/threatmap/points?window=${encodeURIComponent(windowKey)}&size=200`
        );
        if (!response.ok) return;
        const data = await response.json();
        if (cancelled || !Array.isArray(data)) return;
        data.forEach((evt) => upsertEvent(evt));
      } catch (err) {
        if (debugEnabled) {
          console.debug("[threat-map] points fetch failed", err);
        }
      }
    };
    fetchPoints();
    const handle = globalThis.setInterval(fetchPoints, 15_000);
    return () => {
      cancelled = true;
      globalThis.clearInterval(handle);
    };
  }, [debugEnabled, upsertEvent, windowKey]);

  const isThreatWsMessage = (msg: unknown): msg is ThreatWsMessage => {
    if (!msg || typeof msg !== "object") return false;
    const type = (msg as { type?: string }).type;
    return type === "hb" || type === "mode" || type === "event" || type === "agg";
  };

  useEffect(() => {
    // STRICT REAL-TIME: connect to backend WS and ingest only live events/aggregates.
    const wsUrl = resolveWsUrl("/ws/threatmap");
    const client = connectThreatWs({
      url: wsUrl,
      onTransportState: (s) => setTransportState(s),
      onMessage: (msg) => {
        if (!isThreatWsMessage(msg)) {
          invalidMessageCount.current += 1;
          if (debugEnabled) {
            console.debug("[threat-map] invalid message", {
              count: invalidMessageCount.current,
              msg,
            });
          }
          return;
        }
        if (msg.type === "hb") {
          noteHeartbeat(msg.server_ts);
          setStreamState("LIVE");
          return;
        }
        if (msg.type === "mode") {
          setStreamMode(msg.mode);
          return;
        }
        if (msg.type === "event") {
          noteHeartbeat(msg.server_ts);
          setStreamState("LIVE");
          upsertEvent(msg.payload);
          return;
        }
        if (msg.type === "agg") {
          noteHeartbeat(msg.server_ts);
          setStreamState("LIVE");
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
  }, [countryFilter, debugEnabled, enabled, majorOnly, minSeverity, noteHeartbeat, setAgg, setStreamMode, setStreamState, setTransportState, upsertEvent, windowKey]);

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

  const mapStyle = useMemo(() => {
    const rootStyles = getComputedStyle(document.documentElement);
    const background =
      rootStyles.getPropertyValue("--palette-050814").trim() ||
      rootStyles.getPropertyValue("--bg-0").trim();
    return buildNeonMapStyle(background);
  }, []);

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
        <Map mapStyle={mapStyle} attributionControl={false} />
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
