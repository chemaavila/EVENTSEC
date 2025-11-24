import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import type { Alert, NetworkEvent, IndexedEvent } from "../services/api";
import { listAlerts, listNetworkEvents, searchEvents } from "../services/api";

const DashboardPage = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [networkEvents, setNetworkEvents] = useState<NetworkEvent[]>([]);
  const [selectedEvent, setSelectedEvent] = useState<NetworkEvent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [indexedEvents, setIndexedEvents] = useState<IndexedEvent[]>([]);
  const [searchError, setSearchError] = useState<string | null>(null);

  useEffect(() => {
    const run = async () => {
      try {
        const [alertsData, networkData] = await Promise.all([
          listAlerts(),
          listNetworkEvents(),
        ]);
        setAlerts(alertsData);
        setNetworkEvents(networkData);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Unexpected error while loading alerts"
        );
      } finally {
        setLoading(false);
      }
    };
    run();
  }, []);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await searchEvents({ size: 25 });
        setIndexedEvents(data);
        setSearchError(null);
      } catch (err) {
        setSearchError(err instanceof Error ? err.message : "Failed to query OpenSearch");
      }
    };
    const interval = setInterval(load, 60_000);
    return () => clearInterval(interval);
  }, []);

  const stats = useMemo(() => {
    const total = alerts.length;
    const open = alerts.filter((a) => a.status === "open").length;
    const inProgress = alerts.filter((a) => a.status === "in_progress").length;
    const closed = alerts.filter((a) => a.status === "closed").length;

    const bySeverity = alerts.reduce(
      (acc, alert) => {
        acc[alert.severity] = (acc[alert.severity] ?? 0) + 1;
        return acc;
      },
      {} as Record<string, number>
    );

    return { total, open, inProgress, closed, bySeverity };
  }, [alerts]);

  return (
    <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">SOC overview</div>
          <div className="page-subtitle">
            High-level view of alerts and detection posture for the current shift.
          </div>
        </div>
        <div className="stack-horizontal">
          <div className="pill">
            <span className="pill-dot" />
            Realtime telemetry
          </div>
        </div>
      </div>

      <div className="grid-3">
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Open alerts</div>
              <div className="card-subtitle">Currently assigned to the team</div>
            </div>
          </div>
          <div className="card-value">{stats.open}</div>
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">In progress</div>
              <div className="card-subtitle">Being actively investigated</div>
            </div>
          </div>
          <div className="card-value">{stats.inProgress}</div>
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Closed last 24h</div>
              <div className="card-subtitle">
                Total alerts with final decision in the last 24 hours
              </div>
            </div>
          </div>
          <div className="card-value">{stats.closed}</div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Alerts by severity</div>
              <div className="card-subtitle">Current distribution</div>
            </div>
          </div>
          <div className="stack-horizontal" style={{ gap: "2rem", alignItems: "center" }}>
            <div className="donut-wrapper">
              <div
                className="donut-chart"
                style={{
                  background: (() => {
                    const palette: Record<string, string> = {
                      critical: "#ef4444",
                      high: "#f97316",
                      medium: "#eab308",
                      low: "#22c55e",
                    };
                    const order: Array<keyof typeof palette> = ["critical", "high", "medium", "low"];
                    let cursor = 0;
                    const gradientParts = order.map((sev) => {
                      const count = stats.bySeverity[sev] ?? 0;
                      const slice = stats.total === 0 ? 0 : (count / stats.total) * 100;
                      const start = cursor;
                      const end = cursor + slice;
                      cursor = end;
                      return `${palette[sev]} ${start}% ${end}%`;
                    });
                    return `conic-gradient(${gradientParts.join(",") || "#1f2937 0 100%"})`;
                  })(),
                }}
              >
                <div className="donut-center">
                  <div className="donut-value">{stats.total}</div>
                  <div className="muted small">Alerts</div>
                </div>
              </div>
            </div>
            <div className="stack-vertical">
              {(["critical", "high", "medium", "low"] as const).map((sev) => (
                <div key={sev} className="stack-horizontal" style={{ justifyContent: "space-between", width: "160px" }}>
                  <span className={`severity-pill severity-${sev}`}>{sev.toUpperCase()}</span>
                  <span>{stats.bySeverity[sev] ?? 0}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Activity</div>
              <div className="card-subtitle">Simple feed of latest alerts</div>
            </div>
          </div>
          <div className="stack-vertical">
            {loading && <div className="muted">Loading alerts…</div>}
            {error && (
              <div className="muted">
                Failed to load alerts:
                {" "}
                {error}
              </div>
            )}
            {!loading && !error && alerts.length === 0 && (
              <div className="muted">No alerts yet.</div>
            )}
            {!loading &&
              !error &&
              alerts.slice(0, 5).map((alert) => (
                <div key={alert.id} className="alert-row">
                  <div className="alert-row-main">
                    <div className="alert-row-title">{alert.title}</div>
                    <div className="alert-row-meta">
                      <span className="tag">{alert.source}</span>
                      <span className="tag">{alert.category}</span>
                      <span
                        className={[
                          "severity-pill",
                          `severity-${alert.severity}`,
                        ].join(" ")}
                      >
                        {alert.severity.toUpperCase()}
                      </span>
                    </div>
                  </div>
                  <div
                    className={[
                      "status-pill",
                      alert.status === "in_progress"
                        ? "status-in-progress"
                        : alert.status === "closed"
                        ? "status-closed"
                        : "",
                    ].join(" ")}
                  >
                    <span className="status-pill-dot" />
                    {alert.status.replace("_", " ")}
                  </div>
                </div>
              ))}
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">Network telemetry</div>
            <div className="card-subtitle">Recent phishing clicks / blocked sessions.</div>
          </div>
        </div>
        {networkEvents.length === 0 ? (
          <div className="muted">No network events captured.</div>
        ) : (
          <div className="stack-vertical">
            {networkEvents.slice(0, 5).map((event) => (
              <button
                key={event.id}
                type="button"
                className="alert-row"
                onClick={() => setSelectedEvent(event)}
              >
                <div className="alert-row-main">
                  <div className="alert-row-title">
                    {event.hostname}
                    {" "}
                    attempted
                    {" "}
                    {event.url}
                  </div>
                  <div className="alert-row-meta">
                    <span className="tag">{event.category}</span>
                    <span className="tag">{event.username}</span>
                  </div>
                </div>
                <span className={`severity-pill severity-${event.severity}`}>
                  {event.verdict.toUpperCase()}
                </span>
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">OpenSearch event feed</div>
            <div className="card-subtitle">
              Indexed telemetry from agents, log collector and network capture.
            </div>
          </div>
          <Link to="/events" className="btn btn-ghost btn-sm">
            View explorer
          </Link>
        </div>
        {searchError && (
          <div className="muted" style={{ color: "#f87171" }}>
            {searchError}
          </div>
        )}
        {!searchError && indexedEvents.length === 0 && (
          <div className="muted">No indexed events yet.</div>
        )}
        <div className="stack-vertical">
          {indexedEvents.slice(0, 5).map((event) => (
            <div key={`${event.event_id}-${event.timestamp}`} className="alert-row">
              <div className="alert-row-main">
                <div className="alert-row-title">
                  {event.event_type ?? "event"}
                  {" "}
                  &mdash;
                  {" "}
                  {event.category ?? "uncategorized"}
                </div>
                <div className="alert-row-meta">
                  <span className="tag">
                    {new Date(event.timestamp ?? "").toLocaleTimeString() || "—"}
                  </span>
                  {event.agent_id && <span className="tag">Agent #{event.agent_id}</span>}
                </div>
              </div>
              <span className={`severity-pill severity-${(event.severity ?? "low").toLowerCase()}`}>
                {(event.severity ?? "unknown").toUpperCase()}
              </span>
            </div>
          ))}
        </div>
      </div>

      {selectedEvent && (
        <div className="modal-backdrop" onClick={() => setSelectedEvent(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <div className="modal-title">Network event</div>
                <div className="modal-subtitle">
                  {new Date(selectedEvent.created_at).toLocaleString()}
                </div>
              </div>
              <button
                type="button"
                className="modal-close-btn"
                onClick={() => setSelectedEvent(null)}
              >
                &times;
              </button>
            </div>
            <div className="modal-body">
              <div className="field-group">
                <div className="field-label">Hostname</div>
                <div>{selectedEvent.hostname}</div>
              </div>
              <div className="field-group">
                <div className="field-label">User</div>
                <div>{selectedEvent.username}</div>
              </div>
              <div className="field-group">
                <div className="field-label">URL</div>
                <div>{selectedEvent.url}</div>
              </div>
              <div className="field-group">
                <div className="field-label">Description</div>
                <div>{selectedEvent.description}</div>
              </div>
              <div className="stack-horizontal" style={{ justifyContent: "flex-end" }}>
                <button type="button" className="btn btn-sm" onClick={() => setSelectedEvent(null)}>
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DashboardPage;
