import { useEffect, useState } from "react";
import type { NetworkEvent } from "../../services/api";
import { listNetworkEvents } from "../../services/api";
import { createIncidentFromNetworkEvent } from "../../services/incidents";
import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import { useToast } from "../../components/common/ToastProvider";

const NetworkSecurityEventsPage = () => {
  const [events, setEvents] = useState<NetworkEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [source, setSource] = useState<string>("");
  const [eventType, setEventType] = useState<string>("");
  const [severity, setSeverity] = useState<string>("");
  const { pushToast } = useToast();

  const loadEvents = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listNetworkEvents({
        source: source || undefined,
        event_type: eventType || undefined,
        severity: severity ? Number(severity) : undefined,
        size: 200,
      });
      setEvents(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load events");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEvents();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleCreateIncident = async (eventId: string) => {
    try {
      await createIncidentFromNetworkEvent(eventId);
      pushToast({
        title: "Incident created",
        message: "Network event attached to new incident.",
        variant: "success",
      });
    } catch (err) {
      pushToast({
        title: "Failed to create incident",
        message: "Please try again.",
        details: err instanceof Error ? err.message : "Unknown error",
        variant: "error",
      });
    }
  };

  return (
    <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">Network Events</div>
          <div className="page-subtitle">
            Search Suricata/Zeek normalized events and triage quickly.
          </div>
        </div>
        <div className="stack-horizontal">
          <button type="button" className="btn btn-secondary" onClick={loadEvents}>
            Refresh
          </button>
        </div>
      </div>

      <div className="card">
        <form
          className="field-grid"
          onSubmit={(event) => {
            event.preventDefault();
            loadEvents();
          }}
        >
          <label className="field">
            <span className="field-label">Source</span>
            <input
              value={source}
              onChange={(e) => setSource(e.target.value)}
              placeholder="suricata | zeek"
            />
          </label>
          <label className="field">
            <span className="field-label">Event type</span>
            <input
              value={eventType}
              onChange={(e) => setEventType(e.target.value)}
              placeholder="alert, dns, http, conn..."
            />
          </label>
          <label className="field">
            <span className="field-label">Severity</span>
            <input
              type="number"
              min={0}
              max={10}
              value={severity}
              onChange={(e) => setSeverity(e.target.value)}
              placeholder="1-5"
            />
          </label>
          <div className="stack-horizontal" style={{ alignItems: "flex-end" }}>
            <button type="submit" className="btn" disabled={loading}>
              {loading ? "Searching…" : "Search"}
            </button>
          </div>
        </form>
      </div>

      {loading && <LoadingState message="Loading events…" />}
      {error && <ErrorState message={error} />}

      {!loading && !error && (
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Results</div>
              <div className="card-subtitle">{events.length} events</div>
            </div>
          </div>
          {events.length === 0 ? (
            <EmptyState message="No events match your filters." />
          ) : (
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Source</th>
                    <th>Type</th>
                    <th>Src</th>
                    <th>Dst</th>
                    <th>Proto</th>
                    <th>Signature</th>
                    <th>Severity</th>
                    <th>Sensor</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {events.map((event) => (
                    <tr key={event.id}>
                      <td>{new Date(event.ts).toLocaleString()}</td>
                      <td>{event.source}</td>
                      <td>{event.event_type}</td>
                      <td>
                        {event.src_ip}
                        {event.src_port ? `:${event.src_port}` : ""}
                      </td>
                      <td>
                        {event.dst_ip}
                        {event.dst_port ? `:${event.dst_port}` : ""}
                      </td>
                      <td>{event.proto ?? "—"}</td>
                      <td>{event.signature ?? "—"}</td>
                      <td>{event.severity ?? "—"}</td>
                      <td>{event.sensor_name ?? event.sensor_id ?? "—"}</td>
                      <td>
                        <button
                          type="button"
                          className="btn btn-ghost"
                          onClick={() => handleCreateIncident(event.id)}
                        >
                          Create Incident
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default NetworkSecurityEventsPage;
