import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import {
  listPasswordGuardEvents,
  type PasswordGuardAction,
  type PasswordGuardEvent,
} from "../../services/passwordGuard";

const ACTION_LABELS: Record<PasswordGuardAction, string> = {
  DETECTED: "Detected",
  USER_APPROVED_ROTATION: "User approved rotation",
  USER_DENIED_ROTATION: "User denied rotation",
  ROTATED: "Rotated",
};

const PasswordGuardPage = () => {
  const [events, setEvents] = useState<PasswordGuardEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hostId, setHostId] = useState("");
  const [user, setUser] = useState("");
  const [action, setAction] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [selectedEvent, setSelectedEvent] = useState<PasswordGuardEvent | null>(
    null,
  );

  const loadEvents = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = await listPasswordGuardEvents({
        host_id: hostId || undefined,
        user: user || undefined,
        action: action ? (action as PasswordGuardAction) : undefined,
        from: dateFrom ? new Date(dateFrom).toISOString() : undefined,
        to: dateTo ? new Date(dateTo).toISOString() : undefined,
      });
      setEvents(payload);
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

  const timelineEvents = useMemo(() => {
    if (!selectedEvent) {
      return [];
    }
    return events
      .filter(
        (event) =>
          event.entry_id === selectedEvent.entry_id &&
          event.host_id === selectedEvent.host_id,
      )
      .sort(
        (a, b) =>
          new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
      );
  }, [events, selectedEvent]);

  const currentStatus =
    timelineEvents.length > 0
      ? ACTION_LABELS[timelineEvents[timelineEvents.length - 1].action]
      : selectedEvent
        ? ACTION_LABELS[selectedEvent.action]
        : "—";

  return (
    <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">PasswordGuard</div>
          <div className="page-subtitle">
            Track pwned password detections, approvals, and rotations from managed
            endpoints.
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
            <span className="field-label">Host</span>
            <input
              value={hostId}
              onChange={(event) => setHostId(event.target.value)}
              placeholder="workstation-12"
            />
          </label>
          <label className="field">
            <span className="field-label">User</span>
            <input
              value={user}
              onChange={(event) => setUser(event.target.value)}
              placeholder="alice"
            />
          </label>
          <label className="field">
            <span className="field-label">Action</span>
            <select value={action} onChange={(event) => setAction(event.target.value)}>
              <option value="">All actions</option>
              {Object.entries(ACTION_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span className="field-label">From</span>
            <input
              type="datetime-local"
              value={dateFrom}
              onChange={(event) => setDateFrom(event.target.value)}
            />
          </label>
          <label className="field">
            <span className="field-label">To</span>
            <input
              type="datetime-local"
              value={dateTo}
              onChange={(event) => setDateTo(event.target.value)}
            />
          </label>
          <div className="stack-horizontal" style={{ alignItems: "flex-end" }}>
            <button type="submit" className="btn" disabled={loading}>
              {loading ? "Searching…" : "Search"}
            </button>
          </div>
        </form>
      </div>

      {loading && <LoadingState message="Loading PasswordGuard events…" />}
      {error && <ErrorState message={error} />}

      {!loading && !error && (
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Latest events</div>
              <div className="card-subtitle">{events.length} events</div>
            </div>
          </div>
          {events.length === 0 ? (
            <EmptyState message="No PasswordGuard events match your filters." />
          ) : (
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Host</th>
                    <th>User</th>
                    <th>Entry</th>
                    <th>Action</th>
                    <th>Exposures</th>
                    <th>Alert</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {events.map((event) => (
                    <tr key={event.id}>
                      <td>{new Date(event.timestamp).toLocaleString()}</td>
                      <td>{event.host_id}</td>
                      <td>{event.user}</td>
                      <td>{event.entry_label}</td>
                      <td>
                        <span className="badge">{ACTION_LABELS[event.action]}</span>
                      </td>
                      <td>{event.exposure_count}</td>
                      <td>
                        {event.alert_id ? (
                          <Link to={`/alerts/${event.alert_id}`}>
                            Alert #{event.alert_id}
                          </Link>
                        ) : (
                          "—"
                        )}
                      </td>
                      <td>
                        <button
                          type="button"
                          className="btn btn-ghost"
                          onClick={() => setSelectedEvent(event)}
                        >
                          View details
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

      {selectedEvent && (
        <div
          className="drawer-backdrop"
          role="presentation"
          onClick={() => setSelectedEvent(null)}
        >
          <aside
            className="drawer-panel"
            role="dialog"
            aria-modal="true"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="drawer-header">
              <div>
                <div className="drawer-title">PasswordGuard event</div>
                <div className="drawer-subtitle">
                  {selectedEvent.entry_label} · {selectedEvent.host_id}
                </div>
              </div>
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => setSelectedEvent(null)}
              >
                Close
              </button>
            </div>
            <div className="drawer-body">
              <div className="drawer-fields">
                {[
                  { label: "Entry ID", value: selectedEvent.entry_id },
                  { label: "User", value: selectedEvent.user },
                  { label: "Host", value: selectedEvent.host_id },
                  { label: "Exposure count", value: selectedEvent.exposure_count },
                  { label: "Current status", value: currentStatus },
                  { label: "Client version", value: selectedEvent.client_version },
                  {
                    label: "Last update",
                    value: new Date(selectedEvent.updated_at).toLocaleString(),
                  },
                ].map((field) => (
                  <div key={field.label} className="drawer-field">
                    <div className="drawer-field-label">{field.label}</div>
                    <div className="drawer-field-value">{field.value}</div>
                  </div>
                ))}
              </div>

              <div className="passwordguard-timeline">
                <div className="passwordguard-timeline-title">Rotation timeline</div>
                {timelineEvents.length === 0 ? (
                  <div className="passwordguard-timeline-empty">
                    No related events found in the current result set.
                  </div>
                ) : (
                  <ol className="passwordguard-timeline-list">
                    {timelineEvents.map((item) => (
                      <li key={item.id} className="passwordguard-timeline-item">
                        <div className="passwordguard-timeline-dot" />
                        <div className="passwordguard-timeline-content">
                          <div className="passwordguard-timeline-action">
                            {ACTION_LABELS[item.action]}
                          </div>
                          <div className="passwordguard-timeline-meta">
                            {new Date(item.timestamp).toLocaleString()} ·
                            Exposures: {item.exposure_count}
                          </div>
                        </div>
                      </li>
                    ))}
                  </ol>
                )}
              </div>
            </div>
          </aside>
        </div>
      )}
    </div>
  );
};

export default PasswordGuardPage;
