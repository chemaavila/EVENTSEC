import { useCallback, useEffect, useMemo, useState } from "react";
import type { EdrEvent } from "../services/api";
import { clearEdrEvents, listEdrEvents } from "../services/api";

const EdrPage = () => {
  const [events, setEvents] = useState<EdrEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadEvents = useCallback(async () => {
    try {
      setLoading(true);
      const data = await listEdrEvents();
      setEvents(data);
      setError(null);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unexpected error while loading EDR events"
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadEvents().catch((err) => console.error(err));
  }, [loadEvents]);

  const clearEvents = useCallback(async () => {
    try {
      setLoading(true);
      await clearEdrEvents();
      setEvents([]);
      setError(null);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unexpected error while clearing EDR events"
      );
    } finally {
      setLoading(false);
    }
  }, []);

  const openEventDetailWindow = (event: EdrEvent) => {
    const detailWindow = window.open("", "_blank", "width=720,height=900,resizable=yes,scrollbars=yes");
    if (!detailWindow) return;
    const prettyJson = JSON.stringify(event, null, 2);
    detailWindow.document.write(`
      <!doctype html>
      <html>
        <head>
          <title>EDR Event Detail</title>
          <style>
            body {
              font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
              background: #050713;
              color: #e2e8f0;
              margin: 0;
              padding: 1.5rem;
            }
            h1 { margin-bottom: 0.25rem; }
            h2 { margin-top: 1.5rem; }
            .meta { color: #94a3b8; margin-bottom: 1rem; }
            table { width: 100%; border-collapse: collapse; margin-bottom: 1rem; }
            td {
              padding: 0.35rem 0.5rem;
              border-bottom: 1px solid rgba(148, 163, 184, 0.3);
              vertical-align: top;
            }
            td:first-child { width: 35%; font-weight: 600; color: #cbd5f5; }
            pre {
              background: #0b1120;
              padding: 1rem;
              border-radius: 0.75rem;
              overflow: auto;
              border: 1px solid rgba(148, 163, 184, 0.25);
              color: #f8fafc;
            }
          </style>
        </head>
        <body>
          <h1>${event.action} – ${event.process_name}</h1>
          <div class="meta">${new Date(event.timestamp).toLocaleString()}</div>
          <table>
            <tr><td>Hostname</td><td>${event.hostname}</td></tr>
            <tr><td>Username</td><td>${event.username}</td></tr>
            <tr><td>Event type</td><td>${event.event_type}</td></tr>
            <tr><td>Severity</td><td>${event.severity}</td></tr>
          </table>
          <h2>Raw event payload</h2>
          <pre>${prettyJson}</pre>
        </body>
      </html>
    `);
    detailWindow.document.close();
  };

  const endpoints = useMemo(() => {
    const endpointMap = new Map<string, EdrEvent[]>();
    events.forEach((event) => {
      const existing = endpointMap.get(event.hostname) || [];
      endpointMap.set(event.hostname, [...existing, event]);
    });
    return Array.from(endpointMap.entries()).map(([hostname, hostEvents]) => {
      const severities = hostEvents.map((e) => e.severity);
      const maxSeverity =
        severities.includes("critical")
          ? "critical"
          : severities.includes("high")
          ? "high"
          : severities.includes("medium")
          ? "medium"
          : "low";
      return {
        hostname,
        events: hostEvents,
        severity: maxSeverity,
        eventCount: hostEvents.length,
      };
    });
  }, [events]);

  return (
    <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">EDR overview</div>
          <div className="page-subtitle">
            Logical view of endpoints and current detection posture.
          </div>
        </div>
        <div className="stack-horizontal">
          <button
            type="button"
            className="btn btn-ghost"
            onClick={() => loadEvents().catch((err) => console.error(err))}
          >
            Refresh
          </button>
          <button
            type="button"
            className="btn btn-danger"
            onClick={() => clearEvents().catch((err) => console.error(err))}
          >
            Delete events
          </button>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Endpoints</div>
              <div className="card-subtitle">
                {endpoints.length > 0
                  ? `${endpoints.length} endpoint(s) detected`
                  : "No endpoints detected"}
              </div>
            </div>
          </div>
          <div className="stack-vertical">
            {loading && <div className="muted">Loading endpoints…</div>}
            {error && (
              <div className="muted">
                Failed to load endpoints:
                {" "}
                {error}
              </div>
            )}
            {!loading && !error && endpoints.length === 0 && (
              <div className="muted">No endpoints detected yet.</div>
            )}
            {!loading &&
              !error &&
              endpoints.map((endpoint) => (
                <div key={endpoint.hostname} className="alert-row">
                  <div className="alert-row-main">
                    <div className="alert-row-title">{endpoint.hostname}</div>
                    <div className="alert-row-meta">
                      <span className="tag">
                        {endpoint.eventCount}
                        {" "}
                        events
                      </span>
                      <span className="tag">
                        {new Set(endpoint.events.map((e) => e.username)).size}
                        {" "}
                        users
                      </span>
                    </div>
                  </div>
                  <span
                    className={[
                      "severity-pill",
                      `severity-${endpoint.severity}`,
                    ].join(" ")}
                  >
                    {endpoint.severity === "critical" || endpoint.severity === "high"
                      ? "Alert"
                      : endpoint.severity === "medium"
                      ? "Suspicious"
                      : "Healthy"}
                  </span>
                </div>
              ))}
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Recent EDR events</div>
              <div className="card-subtitle">
                Latest endpoint detection and response events.
              </div>
            </div>
          </div>
          <div className="stack-vertical">
            {loading && <div className="muted">Loading events…</div>}
            {error && (
              <div className="muted">
                Failed to load events:
                {" "}
                {error}
              </div>
            )}
            {!loading && !error && events.length === 0 && (
              <div className="muted">No EDR events yet.</div>
            )}
            {!loading &&
              !error &&
              events.slice(0, 10).map((event, idx) => (
                <button
                  key={`${event.timestamp}-${idx}`}
                  type="button"
                  className="alert-row alert-row-button"
                  onClick={() => openEventDetailWindow(event)}
                >
                  <div className="alert-row-main">
                    <div className="alert-row-title">
                      {event.action}
                      {" "}
                      -
                      {" "}
                      {event.process_name}
                    </div>
                    <div className="alert-row-meta">
                      <span className="tag">{event.hostname}</span>
                      <span className="tag">{event.username}</span>
                      <span className="tag">{event.event_type}</span>
                      <span
                        className={[
                          "severity-pill",
                          `severity-${event.severity}`,
                        ].join(" ")}
                      >
                        {event.severity.toUpperCase()}
                      </span>
                    </div>
                    <div className="muted" style={{ fontSize: "0.875rem", marginTop: "0.25rem" }}>
                      {new Date(event.timestamp).toLocaleString()}
                    </div>
                  </div>
                </button>
              ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EdrPage;
