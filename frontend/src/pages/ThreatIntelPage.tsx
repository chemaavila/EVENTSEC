import { useMemo } from "react";
import ThreatMapCanvas from "../components/threat-map/MapCanvas";
import { useThreatMapStore } from "../components/threat-map/useThreatMapStore";

const ThreatIntelPage = () => {
  const agg = useThreatMapStore((s) => s.agg);
  const liveState = useThreatMapStore((s) => s.liveState);
  const transportState = useThreatMapStore((s) => s.transportState);
  const streamState = useThreatMapStore((s) => s.streamState);
  const streamMode = useThreatMapStore((s) => s.streamMode);
  const lastEventTs = useThreatMapStore((s) => s.lastEventTs);
  const windowKey = useThreatMapStore((s) => s.windowKey);
  const setWindowKey = useThreatMapStore((s) => s.setWindowKey);
  const countryFilter = useThreatMapStore((s) => s.countryFilter);
  const setCountryFilter = useThreatMapStore((s) => s.setCountryFilter);
  const events = useThreatMapStore((s) => s.events);

  const kpiTotal = agg ? String(agg.count) : "—";
  const kpiEps = agg ? agg.eps.toFixed(2) : "—";
  const kpiTopType = agg?.top_types?.[0]?.[0] ?? "—";
  const kpiTopTarget = agg?.top_targets?.[0]?.[0] ?? "—";

  const feed = useMemo(() => {
    // show newest first; no fake data
    return [...events].sort((a, b) => Date.parse(b.ts) - Date.parse(a.ts)).slice(0, 60);
  }, [events]);

  const noLiveTelemetry = (agg?.count ?? 0) === 0 && feed.length === 0 && liveState === "LIVE";

  const streamStatusText = useMemo(() => {
    if (transportState === "CLOSED") return "Offline";
    if (transportState === "CONNECTING") return "Connecting…";
    if (streamState === "WAITING") return "Waiting for heartbeat…";
    if (streamState === "STALE") return "Stale telemetry";
    return "Live";
  }, [streamState, transportState]);

  return (
    <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">NEON Threat Map ULTRA</div>
          <div className="page-subtitle">
            Live-only streaming telemetry • State: <strong>{streamStatusText}</strong> • Stream: <strong>{streamMode}</strong>
            {lastEventTs ? <span className="muted"> • Last event: {new Date(lastEventTs).toLocaleTimeString()}</span> : null}
          </div>
        </div>
        <div className="stack-horizontal">
          <button type="button" className={`btn btn-sm ${windowKey === "5m" ? "btn-primary" : "btn-ghost"}`} onClick={() => setWindowKey("5m")}>
            5m
          </button>
          <button type="button" className={`btn btn-sm ${windowKey === "15m" ? "btn-primary" : "btn-ghost"}`} onClick={() => setWindowKey("15m")}>
            15m
          </button>
          <button type="button" className={`btn btn-sm ${windowKey === "1h" ? "btn-primary" : "btn-ghost"}`} onClick={() => setWindowKey("1h")}>
            1h
          </button>
        </div>
      </div>

      <div className="grid-4">
        <div className="card condensed-card">
          <div className="muted small">Events ({windowKey})</div>
          <div className="kpi-value">{kpiTotal}</div>
          <div className="muted small">Server-authoritative</div>
        </div>
        <div className="card condensed-card">
          <div className="muted small">Events/sec</div>
          <div className="kpi-value">{kpiEps}</div>
          <div className="muted small">Derived from live stream</div>
        </div>
        <div className="card condensed-card">
          <div className="muted small">Top Type</div>
          <div className="kpi-value">{kpiTopType}</div>
          <div className="muted small">From agg</div>
        </div>
        <div className="card condensed-card">
          <div className="muted small">Top Target</div>
          <div className="kpi-value">{kpiTopTarget}</div>
          <div className="muted small">From agg</div>
        </div>
      </div>

      <div className="card map-card">
        <div className="map-view">
          <ThreatMapCanvas />
          {noLiveTelemetry ? (
            <div className="map-empty">
              <div className="map-empty-title">NO LIVE TELEMETRY</div>
              <div className="map-empty-sub">
                This view is live-only. Send events via <code>/ingest</code> or run a legal connector/sensor.
              </div>
            </div>
          ) : null}
        </div>
        <div className="map-side-panels">
          <div className="mini-card">
            <div className="card-title">Filters</div>
            <div className="filters row" style={{ marginTop: 12 }}>
              <input
                className="field-control"
                type="text"
                placeholder="Filter by destination country (e.g., US, Germany)"
                value={countryFilter}
                onChange={(e) => setCountryFilter(e.target.value)}
              />
            </div>
            <div className="muted small" style={{ marginTop: 10 }}>
              KPIs & heatmap are server-authoritative. No synthetic defaults are shown.
            </div>
          </div>
          <div className="mini-card">
            <div className="card-title">Top Sources</div>
            {agg?.top_sources?.length ? (
              agg.top_sources.slice(0, 6).map(([k, v]) => (
                <div key={k} className="campaign-row">
                  <div>
                    <strong>{k}</strong>
                    <div className="muted small">{v} events</div>
                  </div>
                </div>
              ))
            ) : (
              <div className="muted small">—</div>
            )}
          </div>
          <div className="mini-card">
            <div className="card-title">Top Targets</div>
            {agg?.top_targets?.length ? (
              agg.top_targets.slice(0, 6).map(([k, v]) => (
                <div key={k} className="campaign-row">
                  <div>
                    <strong>{k}</strong>
                    <div className="muted small">{v} events</div>
                  </div>
                </div>
              ))
            ) : (
              <div className="muted small">—</div>
            )}
          </div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Live Event Feed</div>
              <div className="muted small">Strict live-only stream (no placeholders)</div>
            </div>
          </div>
          <table className="table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Type</th>
                <th>Src</th>
                <th>Dst</th>
                <th>Sev</th>
                <th>Conf</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              {feed.length ? (
                feed.map((e) => (
                  <tr key={e.id}>
                    <td className="muted small">{new Date(e.ts).toLocaleTimeString()}</td>
                    <td>{e.attack_type}</td>
                    <td className="muted small">{e.src?.geo?.country || e.src?.ip || "unknown"}</td>
                    <td className="muted small">{e.dst?.geo?.country || e.dst?.ip || "unknown"}</td>
                    <td>{e.severity}</td>
                    <td>{Math.round((e.confidence || 0) * 100)}%</td>
                    <td className="muted small">{e.source}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="muted small">
                    {liveState === "LIVE" ? "No events in current window." : "Waiting for live telemetry..."}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="card tactics-card">
          <div className="card-title">Top Types</div>
          {agg?.top_types?.length ? (
            agg.top_types.slice(0, 8).map(([label, value]) => (
              <div key={label} className="tactic-row">
                <div className="tactic-label">
                  {label}
                  <span className="muted small">{value}</span>
                </div>
                <div className="tactic-bar">
                  <div style={{ width: `${Math.min(100, (value / Math.max(1, agg.count)) * 100)}%`, background: "#00E5FF" }} />
                </div>
              </div>
            ))
          ) : (
            <div className="muted small">—</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ThreatIntelPage;
