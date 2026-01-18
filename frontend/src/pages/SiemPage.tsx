import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { EventDetailDrawer } from "../components/common/EventDetailDrawer";
import type { SiemEvent } from "../services/api";
import { listSiemEvents } from "../services/api";
import { API_BASE_URL } from "../config/endpoints";

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
const MAX_LIVE_EVENTS = 2000;
const LIVE_RETRY_BASE_MS = 1500;
const LIVE_RETRY_MAX_MS = 10000;

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
  const [liveEnabled, setLiveEnabled] = useState(true);
  const [liveStatus, setLiveStatus] = useState<"connecting" | "connected" | "reconnecting" | "offline">(
    "connecting"
  );
  const [liveError, setLiveError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimerRef = useRef<number | null>(null);
  const retryDelayRef = useRef(LIVE_RETRY_BASE_MS);
  const seenEventIdsRef = useRef<Set<string>>(new Set());

  const loadEvents = useCallback(async (options?: LoadOptions) => {
    const silent = options?.silent ?? false;
    try {
      if (silent) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      const data = await listSiemEvents({
        q: kql || undefined,
        time_range: timeRange,
        size: 200,
      });
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
  }, [kql, timeRange]);

  useEffect(() => {
    loadEvents().catch((err) => console.error(err));
    if (liveEnabled) {
      return undefined;
    }
    const interval = window.setInterval(() => {
      loadEvents({ silent: true }).catch((err) => console.error(err));
    }, 5000);
    return () => window.clearInterval(interval);
  }, [loadEvents, liveEnabled]);

  useEffect(() => {
    if (!liveEnabled) {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      if (reconnectTimerRef.current) {
        window.clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      setLiveStatus("offline");
      return undefined;
    }

    const connect = () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      setLiveStatus("connecting");
      setLiveError(null);

      const params = new URLSearchParams();
      if (kql.trim()) {
        params.set("q", kql.trim());
      }
      const streamUrl = `${API_BASE_URL}/siem/stream${params.toString() ? `?${params}` : ""}`;
      const source = new EventSource(streamUrl, { withCredentials: true });
      eventSourceRef.current = source;

      source.onopen = () => {
        setLiveStatus("connected");
        retryDelayRef.current = LIVE_RETRY_BASE_MS;
      };

      source.onmessage = (event) => {
        if (!event.data) return;
        try {
          const parsed = JSON.parse(event.data) as SiemEvent & { raw?: Record<string, unknown> };
          const rawId =
            typeof parsed.raw?.event_id === "string" || typeof parsed.raw?.event_id === "number"
              ? String(parsed.raw?.event_id)
              : `${parsed.timestamp}-${parsed.message}`;
          if (seenEventIdsRef.current.has(rawId)) {
            return;
          }
          seenEventIdsRef.current.add(rawId);
          if (seenEventIdsRef.current.size > MAX_LIVE_EVENTS) {
            const iterator = seenEventIdsRef.current.values();
            const first = iterator.next().value as string | undefined;
            if (first) {
              seenEventIdsRef.current.delete(first);
            }
          }
          setEvents((prev) => [parsed, ...prev].slice(0, MAX_LIVE_EVENTS));
          setSourceFilters((prev) => ({
            ...prev,
            [parsed.source]: prev[parsed.source] ?? true,
          }));
          setLastUpdated(new Date().toLocaleTimeString());
        } catch (err) {
          console.error("Failed to parse SSE payload", err);
        }
      };

      source.addEventListener("ping", () => {
        setLiveStatus("connected");
      });

      source.onerror = () => {
        setLiveStatus("reconnecting");
        setLiveError("Live stream disconnected. Reconnecting…");
        source.close();
        const retryDelay = retryDelayRef.current;
        retryDelayRef.current = Math.min(retryDelayRef.current * 2, LIVE_RETRY_MAX_MS);
        reconnectTimerRef.current = window.setTimeout(connect, retryDelay);
      };
    };

    connect();

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      if (reconnectTimerRef.current) {
        window.clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
    };
  }, [kql, liveEnabled]);

  const clearEvents = useCallback(async () => {
    setEvents([]);
    setSourceFilters({});
    setError(null);
    setLastUpdated(new Date().toLocaleTimeString());
  }, []);

  const toggleSource = (source: string) => {
    setSourceFilters((prev) => ({
      ...prev,
      [source]: prev[source] === false,
    }));
  };

  const filteredEvents = useMemo(() => {
    return events.filter((event) => {
      const sourceEnabled = sourceFilters[event.source] !== false;
      return sourceEnabled;
    });
  }, [events, sourceFilters]);

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
            <div className="siem-live-status">
              <span className={`siem-live-dot ${liveStatus}`} />
              <span className="muted small">
                {liveEnabled ? `Live ${liveStatus}` : "Live paused"}
              </span>
            </div>
            {liveError && (
              <span className="muted small" style={{ color: "var(--palette-f87171)" }}>
                {liveError}
              </span>
            )}
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
              className="btn btn-ghost"
              onClick={() => setLiveEnabled((prev) => !prev)}
            >
              {liveEnabled ? "Pause Live" : "Resume Live"}
            </button>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => clearEvents().catch((err) => console.error(err))}
              disabled={loading}
            >
              Clear view
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
