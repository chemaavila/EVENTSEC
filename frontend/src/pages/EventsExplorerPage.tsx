import { useEffect, useMemo, useState } from "react";
import type { IndexedEvent } from "../services/api";
import { searchEvents } from "../services/api";

const severityOptions = ["", "low", "medium", "high", "critical"];

const formatTimestamp = (value?: string) => {
  if (!value) return "—";
  return new Date(value).toLocaleString();
};

const EventsExplorerPage = () => {
  const [query, setQuery] = useState("*");
  const [severity, setSeverity] = useState("");
  const [size, setSize] = useState(100);
  const [events, setEvents] = useState<IndexedEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<IndexedEvent | null>(null);

  const loadEvents = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await searchEvents({
        query: query.trim(),
        severity: severity || undefined,
        size,
      });
      setEvents(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to query events");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEvents();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const summary = useMemo(
    () =>
      events.reduce((acc, item) => {
        const sev = (item.severity ?? "unknown").toLowerCase();
        acc[sev] = (acc[sev] ?? 0) + 1;
        return acc;
      }, {} as Record<string, number>),
    [events]
  );

  const extractEventMessage = (event: IndexedEvent) => {
    if (!event.details || typeof event.details !== "object") return undefined;
    const detailMessage = (event.details as Record<string, unknown>)["message"];
    return typeof detailMessage === "string" ? detailMessage : undefined;
  };

  return (
    <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">Events explorer</div>
          <div className="page-subtitle">
            Live telemetry indexed in OpenSearch. Use Lucene / WQL syntax to hunt.
          </div>
        </div>
        <div className="stack-horizontal">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={loadEvents}
            disabled={loading}
          >
            Refresh
          </button>
        </div>
      </div>

      <div className="card">
        <form
          className="stack-vertical"
          onSubmit={(event) => {
            event.preventDefault();
            loadEvents();
          }}
        >
          <div className="field-grid">
            <label className="field">
              <span className="field-label">Query (Lucene / WQL)</span>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder='Example: event_type:"logcollector" AND severity:high'
              />
            </label>
            <label className="field">
              <span className="field-label">Severity</span>
              <select value={severity} onChange={(e) => setSeverity(e.target.value)}>
                {severityOptions.map((option) => (
                  <option key={option || "any"} value={option}>
                    {option ? option.toUpperCase() : "Any"}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span className="field-label">Result size</span>
              <input
                type="number"
                min={10}
                max={500}
                step={10}
                value={size}
                onChange={(e) => setSize(Number(e.target.value))}
              />
            </label>
          </div>
          <div className="stack-horizontal" style={{ justifyContent: "flex-end" }}>
            <button type="submit" className="btn" disabled={loading}>
              {loading ? "Querying…" : "Run query"}
            </button>
          </div>
        </form>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Events retrieved</div>
              <div className="card-subtitle">Showing latest matches</div>
            </div>
            <div className="card-value">{events.length}</div>
          </div>
          <div className="stack-vertical muted">
            {["critical", "high", "medium", "low", "unknown"].map((sev) => (
              <div
                key={sev}
                className="stack-horizontal"
                style={{ justifyContent: "space-between" }}
              >
                <span className={`severity-pill severity-${sev.replace("unknown", "low")}`}>
                  {sev.toUpperCase()}
                </span>
                <span>{summary[sev] ?? 0}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Tips</div>
              <div className="card-subtitle">Supported syntax helpers</div>
            </div>
          </div>
          <ul className="list">
            <li>Use wildcards: hostname:eventsec* AND severity:high</li>
            <li>Filter by module: event_type:logcollector OR event_type:network</li>
            <li>Free text search across message/details using standard Lucene syntax.</li>
          </ul>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">Event timeline</div>
            <div className="card-subtitle">Click an entry for full JSON</div>
          </div>
        </div>
        {error && (
          <div className="muted" style={{ color: "var(--palette-f87171)" }}>
            {error}
          </div>
        )}
        {!loading && events.length === 0 && !error && (
          <div className="muted">No events for this query.</div>
        )}
        <div className="table scrollable">
          <div className="table-row table-header">
            <div>Timestamp</div>
            <div>Type</div>
            <div>Category</div>
            <div>Severity</div>
            <div>Message</div>
          </div>
          {events.map((event) => (
            <button
              type="button"
              key={`${event.event_id}-${event.timestamp}-${event.category}`}
              className="table-row"
              onClick={() => setSelectedEvent(event)}
            >
              <div>{formatTimestamp(event.timestamp)}</div>
              <div>{event.event_type ?? "—"}</div>
              <div>{event.category ?? "—"}</div>
              <div>
                <span className={`severity-pill severity-${(event.severity ?? "low").toLowerCase()}`}>
                  {(event.severity ?? "unknown").toUpperCase()}
                </span>
              </div>
              <div className="truncate">{event.message ?? extractEventMessage(event) ?? "—"}</div>
            </button>
          ))}
        </div>
      </div>

      {selectedEvent && (
        <div className="modal-backdrop" onClick={() => setSelectedEvent(null)}>
          <div className="modal-content modal-wide" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <div className="modal-title">Event detail</div>
                <div className="modal-subtitle">{formatTimestamp(selectedEvent.timestamp)}</div>
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
              <div className="field-grid">
                <div>
                  <div className="field-label">Type</div>
                  <div>{selectedEvent.event_type ?? "—"}</div>
                </div>
                <div>
                  <div className="field-label">Category</div>
                  <div>{selectedEvent.category ?? "—"}</div>
                </div>
                <div>
                  <div className="field-label">Severity</div>
                  <div>{selectedEvent.severity ?? "—"}</div>
                </div>
                <div>
                  <div className="field-label">Agent</div>
                  <div>{selectedEvent.agent_id ?? "—"}</div>
                </div>
              </div>
              <div className="field">
                <span className="field-label">JSON payload</span>
                <pre className="code-block">
{JSON.stringify(selectedEvent.details ?? selectedEvent, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EventsExplorerPage;

