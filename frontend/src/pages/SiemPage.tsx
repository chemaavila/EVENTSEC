import { useCallback, useEffect, useMemo, useState } from "react";
import { EventDetailDrawer } from "../components/common/EventDetailDrawer";
import type { SiemEvent } from "../services/api";
import { clearSiemEvents, listSiemEvents } from "../services/api";

type TimeRangeKey = "24h" | "1h" | "15m";

type LoadOptions = {
  silent?: boolean;
};

const TIME_RANGES: Record<TimeRangeKey, number> = {
  "24h": 24 * 60 * 60 * 1000,
  "1h": 60 * 60 * 1000,
  "15m": 15 * 60 * 1000,
};

const severityOrder: Array<SiemEvent["severity"]> = ["critical", "high", "medium", "low"];

const SiemPage = () => {
  const [events, setEvents] = useState<SiemEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [kql, setKql] = useState("");
  const [timeRange, setTimeRange] = useState<TimeRangeKey>("24h");
  const [sourceFilters, setSourceFilters] = useState<Record<string, boolean>>({});
  const [selectedEvent, setSelectedEvent] = useState<SiemEvent | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  const loadEvents = useCallback(async (options?: LoadOptions) => {
    const silent = options?.silent ?? false;
    try {
      if (silent) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      const data = await listSiemEvents();
      setEvents(data);
      setSourceFilters((prev) => {
        const map = { ...prev };
        data.forEach((event) => {
          if (!(event.source in map)) {
            map[event.source] = true;
          }
        });
        return map;
      });
      setError(null);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unexpected error while loading SIEM events"
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadEvents().catch((err) => console.error(err));
    const interval = window.setInterval(() => {
      loadEvents({ silent: true }).catch((err) => console.error(err));
    }, 5000);
    return () => window.clearInterval(interval);
  }, [loadEvents]);

  const clearEvents = useCallback(async () => {
    try {
      setLoading(true);
      await clearSiemEvents();
      setEvents([]);
      setSourceFilters({});
      setError(null);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unexpected error while clearing SIEM events"
      );
    } finally {
      setLoading(false);
    }
  }, []);

  const toggleSource = (source: string) => {
    setSourceFilters((prev) => ({
      ...prev,
      [source]: prev[source] === false,
    }));
  };

  const matchesKql = (event: SiemEvent, query: string) => {
    const trimmed = query.trim();
    if (!trimmed) return true;
    const terms = trimmed.split(/\s+(?:AND\s+)?/i).filter(Boolean);
    return terms.every((term) => {
      const [rawField, ...rest] = term.split(":");
      if (rest.length > 0) {
        const value = rest.join(":").toLowerCase();
        const field = rawField.toLowerCase();
        const lookup = (event as unknown as Record<string, unknown>)[field];
        const fieldValue = lookup ?? (field === "message" ? event.message : undefined);
        return fieldValue
          ? String(fieldValue).toLowerCase().includes(value)
          : false;
      }
      const normalizedTerm = term.toLowerCase();
      return (
        event.message?.toLowerCase().includes(normalizedTerm) ||
        event.source?.toLowerCase().includes(normalizedTerm) ||
        event.host?.toLowerCase().includes(normalizedTerm)
      );
    });
  };

  const filteredEvents = useMemo(() => {
    const now = Date.now();
    return events.filter((event) => {
      const timestamp = new Date(event.timestamp).getTime();
      const withinRange = now - timestamp <= TIME_RANGES[timeRange];
      const sourceEnabled = sourceFilters[event.source] !== false;
      const kqlMatch = matchesKql(event, kql);
      return withinRange && sourceEnabled && kqlMatch;
    });
  }, [events, kql, sourceFilters, timeRange]);

  const severityStats = useMemo(() => {
    const counts: Record<string, number> = {};
    severityOrder.forEach((sev) => {
      counts[sev] = filteredEvents.filter((event) => event.severity === sev).length;
    });
    return counts;
  }, [filteredEvents]);

  const epsValue = useMemo(() => {
    const now = Date.now();
    const last60 = filteredEvents.filter(
      (event) => now - new Date(event.timestamp).getTime() <= 60 * 1000
    );
    return Math.max(last60.length * 10, 120);
  }, [filteredEvents]);

  const uniqueSources = useMemo(() => {
    const set = new Set(events.map((e) => e.source));
    return Array.from(set);
  }, [events]);

  const selectedFields = useMemo(() => {
    if (!selectedEvent) return [];
    return [
      { label: "Timestamp", value: new Date(selectedEvent.timestamp).toLocaleString() },
      { label: "Host", value: selectedEvent.host || "—" },
      { label: "Source", value: selectedEvent.source || "—" },
      { label: "Category", value: selectedEvent.category || "—" },
      { label: "Severity", value: selectedEvent.severity || "—" },
    ];
  }, [selectedEvent]);

  return (
    <div className="siem-root">
      <div className="siem-panel">
        <div className="siem-profile">
          <div className="siem-avatar">SA</div>
          <div>
            <div className="siem-profile-name">SOC Analyst</div>
            <div className="siem-profile-email">analyst@eventsec.local</div>
          </div>
        </div>
        <div className="siem-panel-section">
          <div className="siem-panel-title">Filters</div>
          <div className="siem-panel-subtitle">Data Sources</div>
          <div className="siem-checkbox-list">
            {uniqueSources.length === 0 && (
              <div className="muted small">No sources detected</div>
            )}
            {uniqueSources.map((source) => (
              <label key={source} className="siem-checkbox">
                <input
                  type="checkbox"
                  checked={sourceFilters[source] !== false}
                  onChange={() => toggleSource(source)}
                />
                <span>{source}</span>
              </label>
            ))}
          </div>
        </div>
      </div>
      <div className="siem-content">
        <div className="siem-toolbar">
          <input
            className="siem-search"
            placeholder="Search logs with KQL…"
            value={kql}
            onChange={(e) => setKql(e.target.value)}
          />
          <div className="siem-toolbar-right">
            {lastUpdated && <span className="muted small">Updated {lastUpdated}</span>}
            <span className="muted small">Live updates every 5s</span>
            <select
              className="siem-range"
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value as TimeRangeKey)}
            >
              <option value="24h">Last 24 hours</option>
              <option value="1h">Last 1 hour</option>
              <option value="15m">Last 15 minutes</option>
            </select>
            <button type="button" className="btn btn-ghost" onClick={() => setKql("")}> 
              Clear
            </button>
            <button
              type="button"
              className="btn"
              onClick={() => loadEvents().catch((err) => console.error(err))}
              disabled={loading || refreshing}
            >
              {loading || refreshing ? "Refreshing…" : "Run Query"}
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

        <div className="siem-metrics">
          {severityOrder.map((sev) => (
            <div key={sev} className="siem-metric-card">
              <div className="siem-metric-label">{sev.charAt(0).toUpperCase() + sev.slice(1)}</div>
              <div className="siem-metric-value">{severityStats[sev] ?? 0}</div>
            </div>
          ))}
        </div>

        <div className="siem-grid">
          <div className="siem-card large">
            <div className="siem-card-header">
              <div>
                <div className="siem-card-title">Live Events Per Second (EPS)</div>
                <div className="siem-card-subtitle">Last 60 seconds</div>
              </div>
            </div>
            <div className="siem-eps-value">
              {epsValue.toLocaleString()}
              <span className="positive">+5.2%</span>
            </div>
            <div className="siem-sparkline">
              <div className="sparkline-track">
                {Array.from({ length: 20 }).map((_, idx) => {
                  const height = 20 + Math.abs(Math.sin(idx + filteredEvents.length)) * 60;
                  return (
                    <span key={idx} style={{ height: `${height}%` }} className="sparkline-bar" />
                  );
                })}
              </div>
            </div>
          </div>
          <div className="siem-card">
            <div className="siem-card-header">
              <div>
                <div className="siem-card-title">Global Threat Activity</div>
                <div className="siem-card-subtitle">300×300 placeholder</div>
              </div>
            </div>
            <div className="siem-placeholder">300×300</div>
          </div>
        </div>

        <div className="siem-grid two">
          <div className="siem-card">
            <div className="siem-card-header">
              <div>
                <div className="siem-card-title">Top Log Sources by Volume</div>
                <div className="siem-card-subtitle">Based on filtered events</div>
              </div>
            </div>
            <div className="siem-chart">
              {uniqueSources.length === 0 && <div className="muted small">No sources available</div>}
              {uniqueSources.map((source) => (
                <div key={source} className="siem-bar">
                  <span>{source}</span>
                  <div className="siem-bar-track">
                    <div
                      className="siem-bar-fill"
                      style={{ width: `${Math.min(100, filteredEvents.length * 5)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="siem-card">
            <div className="siem-card-header">
              <div>
                <div className="siem-card-title">Critical Alerts</div>
                <div className="siem-card-subtitle">Highest severity in current range</div>
              </div>
            </div>
            <div className="siem-table">
              {filteredEvents
                .filter((event) => event.severity === "critical")
                .slice(0, 5)
                .map((event, idx) => (
                  <button
                    type="button"
                    key={`${event.timestamp}-${idx}`}
                    className="siem-table-row"
                    onClick={() => setSelectedEvent(event)}
                  >
                    <span>{new Date(event.timestamp).toLocaleString()}</span>
                    <span>{event.message}</span>
                    <span className="tag critical">Critical</span>
                  </button>
                ))}
              {filteredEvents.filter((event) => event.severity === "critical").length === 0 && (
                <div className="muted small" style={{ padding: "0.75rem" }}>
                  No critical alerts in the selected range.
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="siem-card">
          <div className="siem-card-header">
            <div>
              <div className="siem-card-title">Events over time</div>
              <div className="siem-card-subtitle">Filtered logs (max 50 rows)</div>
            </div>
            <div className="siem-card-actions">
              {(loading || refreshing) && <span className="muted small">Refreshing…</span>}
              {error && (
                <span className="muted small" style={{ color: "var(--palette-f87171)" }}>
                  {error}
                </span>
              )}
            </div>
          </div>
          <div className="siem-table siem-table-body">
            <div className="siem-table-head">
              <span>Timestamp</span>
              <span>Host</span>
              <span>Severity</span>
              <span>Message</span>
            </div>
            {filteredEvents.slice(0, 50).map((event, idx) => (
              <button
                type="button"
                key={`${event.timestamp}-${idx}-table`}
                className="siem-table-row"
                data-testid={`siem-event-row-${idx}`}
                onClick={() => setSelectedEvent(event)}
              >
                <span>{new Date(event.timestamp).toLocaleString()}</span>
                <span>{event.host || "—"}</span>
                <span>
                  <span className={`tag severity-${event.severity}`}>{event.severity}</span>
                </span>
                <span>{event.message}</span>
              </button>
            ))}
            {!loading && filteredEvents.length === 0 && (
              <div className="muted small" style={{ padding: "1rem" }}>
                No events match the current filters.
              </div>
            )}
          </div>
        </div>
      </div>
      <EventDetailDrawer
        title={selectedEvent?.message || "SIEM Event"}
        subtitle={selectedEvent ? new Date(selectedEvent.timestamp).toLocaleString() : undefined}
        fields={selectedFields}
        rawJson={selectedEvent ?? {}}
        isOpen={Boolean(selectedEvent)}
        onClose={() => setSelectedEvent(null)}
      />
    </div>
  );
};

export default SiemPage;
