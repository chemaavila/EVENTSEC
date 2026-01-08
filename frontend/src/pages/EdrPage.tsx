import { useCallback, useEffect, useMemo, useState } from "react";
import { EmptyState } from "../components/common/EmptyState";
import { ErrorState } from "../components/common/ErrorState";
import { EventDetailDrawer } from "../components/common/EventDetailDrawer";
import { LoadingState } from "../components/common/LoadingState";
import type { Agent, EdrEvent } from "../services/api";
import { clearEdrEvents, listAgents, listEdrEvents } from "../services/api";

const ONLINE_THRESHOLD_MS = 5 * 60 * 1000;

const EdrPage = () => {
  const [events, setEvents] = useState<EdrEvent[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<EdrEvent | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  const loadData = useCallback(async (options?: { silent?: boolean }) => {
    const silent = options?.silent ?? false;
    try {
      if (silent) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      const [eventsData, agentData] = await Promise.all([
        listEdrEvents(),
        listAgents().catch(() => []),
      ]);
      setEvents(eventsData);
      setAgents(agentData);
      setError(null);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unexpected error while loading EDR events"
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadData().catch((err) => console.error(err));
    const interval = window.setInterval(() => {
      loadData({ silent: true }).catch((err) => console.error(err));
    }, 5000);
    return () => window.clearInterval(interval);
  }, [loadData]);

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

  const selectedFields = useMemo(() => {
    if (!selectedEvent) return [];
    return [
      { label: "Timestamp", value: new Date(selectedEvent.timestamp).toLocaleString() },
      { label: "Hostname", value: selectedEvent.hostname || "—" },
      { label: "Username", value: selectedEvent.username || "—" },
      { label: "Event type", value: selectedEvent.event_type || "—" },
      { label: "Severity", value: selectedEvent.severity || "—" },
      { label: "Action", value: selectedEvent.action || "—" },
      { label: "Process", value: selectedEvent.process_name || "—" },
    ];
  }, [selectedEvent]);

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

  const connectedAgents = useMemo(() => {
    const now = Date.now();
    return agents.filter((agent) => {
      const lastSeen = agent.last_seen || agent.last_heartbeat || "";
      const lastSeenTs = lastSeen ? new Date(lastSeen).getTime() : 0;
      const isRecent = lastSeenTs > 0 && now - lastSeenTs <= ONLINE_THRESHOLD_MS;
      return agent.status === "online" || isRecent;
    });
  }, [agents]);

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
          {lastUpdated && <span className="muted small">Updated {lastUpdated}</span>}
          <button
            type="button"
            className="btn btn-ghost"
            onClick={() => loadData().catch((err) => console.error(err))}
            disabled={loading || refreshing}
          >
            {loading || refreshing ? "Refreshing…" : "Refresh"}
          </button>
          <button
            type="button"
            className="btn btn-danger"
            onClick={() => clearEvents().catch((err) => console.error(err))}
            disabled={loading}
          >
            Delete events
          </button>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Connected agents</div>
              <div className="card-subtitle">
                {connectedAgents.length > 0
                  ? `${connectedAgents.length} agent(s) online`
                  : "No connected agents detected"}
              </div>
            </div>
          </div>
          <div className="stack-vertical">
            {loading && <div className="muted">Loading agents…</div>}
            {!loading && connectedAgents.length === 0 && (
              <div className="muted">
                Agents appear when they report heartbeat telemetry. Verify agent enrollment and connectivity.
              </div>
            )}
            {connectedAgents.map((agent) => (
              <div key={agent.id} className="alert-row">
                <div className="alert-row-main">
                  <div className="alert-row-title">{agent.name}</div>
                  <div className="alert-row-meta">
                    <span className="tag">{agent.os}</span>
                    <span className="tag">{agent.ip_address}</span>
                  </div>
                  <div className="muted small">Last seen: {agent.last_seen ? new Date(agent.last_seen).toLocaleString() : "—"}</div>
                </div>
                <span className="status-pill status-in-progress">
                  <span className="status-pill-dot" />
                  Online
                </span>
              </div>
            ))}
          </div>
        </div>

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
      </div>

      <div className="card" style={{ marginTop: "1.5rem" }}>
        <div className="card-header">
          <div>
            <div className="card-title">Recent EDR events</div>
            <div className="card-subtitle">
              Latest endpoint detection and response events.
            </div>
          </div>
        </div>
        <div className="stack-vertical">
          {loading && <LoadingState message="Loading events…" />}
          {error && (
            <ErrorState
              message="Failed to load events."
              details={error}
              onRetry={() => loadData()}
            />
          )}
          {!loading && !error && events.length === 0 && (
            <EmptyState
              title="No EDR events yet"
              message="Endpoint telemetry will appear here once ingested."
            />
          )}
          {!loading &&
            !error &&
            events.slice(0, 10).map((event, idx) => (
              <button
                key={`${event.timestamp}-${idx}`}
                type="button"
                className="alert-row alert-row-button"
                data-testid={`edr-event-row-${idx}`}
                onClick={() => setSelectedEvent(event)}
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
                  <div className="muted" style={{ fontSize: "var(--text-sm)", marginTop: "0.25rem" }}>
                    {new Date(event.timestamp).toLocaleString()}
                  </div>
                </div>
              </button>
            ))}
        </div>
      </div>
      <EventDetailDrawer
        title={selectedEvent ? `${selectedEvent.action} — ${selectedEvent.process_name}` : "EDR Event"}
        subtitle={selectedEvent ? new Date(selectedEvent.timestamp).toLocaleString() : undefined}
        fields={selectedFields}
        rawJson={selectedEvent ?? {}}
        isOpen={Boolean(selectedEvent)}
        onClose={() => setSelectedEvent(null)}
      />
    </div>
  );
};

export default EdrPage;
