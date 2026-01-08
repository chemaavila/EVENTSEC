import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { Alert, AlertCreatePayload } from "../../services/api";
import { createAlert, listAlerts } from "../../services/api";
import { useToast } from "../../components/common/ToastProvider";
import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";

const emptyForm: AlertCreatePayload = {
  title: "",
  description: "",
  source: "",
  category: "",
  severity: "medium",
  url: "",
  sender: "",
  username: "",
  hostname: "",
};

const AlertsPage = () => {
  const navigate = useNavigate();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<AlertCreatePayload>(emptyForm);
  const [creating, setCreating] = useState(false);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const { pushToast } = useToast();

  const loadAlerts = async () => {
    try {
      setLoading(true);
      const data = await listAlerts();
      setAlerts(data);
      setError(null);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unexpected error while loading alerts"
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, []);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    try {
      setCreating(true);
      // Convert empty strings to null for optional fields
      const payload: AlertCreatePayload = {
        title: form.title,
        description: form.description,
        source: form.source,
        category: form.category,
        severity: form.severity,
        url: form.url && form.url.trim() ? form.url.trim() : null,
        sender: form.sender && form.sender.trim() ? form.sender.trim() : null,
        username: form.username && form.username.trim() ? form.username.trim() : null,
        hostname: form.hostname && form.hostname.trim() ? form.hostname.trim() : null,
      };
      await createAlert(payload);
      setForm(emptyForm);
      await loadAlerts();
    } catch (err) {
      const details = err instanceof Error ? err.message : "Unknown error";
      pushToast({
        title: "Failed to create alert",
        message: "Please review the details and try again.",
        details,
        variant: "error",
      });
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">Alerts</div>
          <div className="page-subtitle">
            Central view to triage, investigate and document security alerts.
          </div>
        </div>
        <div className="stack-horizontal">
          <button
            type="button"
            className="btn btn-ghost"
            onClick={loadAlerts}
            disabled={loading}
          >
            {loading ? "Refreshing…" : "Refresh"}
          </button>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Active alerts</div>
              <div className="card-subtitle">
                All alerts currently open or under investigation.
              </div>
            </div>
          </div>

          <div className="stack-vertical">
            {loading && <LoadingState message="Loading alerts…" />}
            {error && (
              <ErrorState
                message="Failed to load alerts."
                details={error}
                onRetry={() => loadAlerts()}
              />
            )}
            {!loading && !error && alerts.length === 0 && (
              <EmptyState
                title="No alerts yet"
                message="Create a manual alert to start triage."
              />
            )}
            {!loading &&
              !error &&
              alerts.map((alert) => (
                <button
                  key={alert.id}
                  type="button"
                  className="alert-row"
                  onClick={() => setSelectedAlert(alert)}
                >
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
                </button>
              ))}
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Create manual alert</div>
              <div className="card-subtitle">
                Use this form for playbook testing or manual incident registration.
              </div>
            </div>
          </div>

          <form className="stack-vertical" onSubmit={handleSubmit}>
            <div className="grid-2">
              <div className="field-group">
                <label htmlFor="title" className="field-label">
                  Title
                </label>
                <input
                  id="title"
                  name="title"
                  className="field-control"
                  value={form.title}
                  onChange={handleChange}
                  required
                />
              </div>
              <div className="field-group">
                <label htmlFor="source" className="field-label">
                  Source
                </label>
                <input
                  id="source"
                  name="source"
                  className="field-control"
                  value={form.source}
                  onChange={handleChange}
                  placeholder="EDR, Azure AD, WAF…"
                  required
                />
              </div>
            </div>

            <div className="grid-2">
              <div className="field-group">
                <label htmlFor="category" className="field-label">
                  Category
                </label>
                <input
                  id="category"
                  name="category"
                  className="field-control"
                  value={form.category}
                  onChange={handleChange}
                  placeholder="Authentication, Malware, Web…"
                />
              </div>
              <div className="field-group">
                <label htmlFor="severity" className="field-label">
                  Severity
                </label>
                <select
                  id="severity"
                  name="severity"
                  className="field-control"
                  value={form.severity}
                  onChange={handleChange}
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>
            </div>

            <div className="field-group">
              <label htmlFor="description" className="field-label">
                Description
              </label>
              <textarea
                id="description"
                name="description"
                className="field-control"
                rows={4}
                value={form.description}
                onChange={handleChange}
                placeholder="Short description of the alert context and detection source."
              />
            </div>

            <div className="grid-2">
              <div className="field-group">
                <label htmlFor="url" className="field-label">
                  URL
                </label>
                <input
                  id="url"
                  name="url"
                  className="field-control"
                  value={form.url ?? ""}
                  onChange={handleChange}
                  placeholder="Optional related URL"
                />
              </div>
              <div className="field-group">
                <label htmlFor="sender" className="field-label">
                  Sender
                </label>
                <input
                  id="sender"
                  name="sender"
                  className="field-control"
                  value={form.sender ?? ""}
                  onChange={handleChange}
                  placeholder="Email sender (for phishing cases)"
                />
              </div>
            </div>

            <div className="grid-2">
              <div className="field-group">
                <label htmlFor="username" className="field-label">
                  Username
                </label>
                <input
                  id="username"
                  name="username"
                  className="field-control"
                  value={form.username ?? ""}
                  onChange={handleChange}
                  placeholder="Impacted user"
                />
              </div>
              <div className="field-group">
                <label htmlFor="hostname" className="field-label">
                  Hostname
                </label>
                <input
                  id="hostname"
                  name="hostname"
                  className="field-control"
                  value={form.hostname ?? ""}
                  onChange={handleChange}
                  placeholder="Impacted endpoint"
                />
              </div>
            </div>

            <div className="stack-horizontal" style={{ justifyContent: "flex-end" }}>
              <button
                type="submit"
                className="btn btn-sm"
                disabled={creating}
              >
                {creating ? "Creating…" : "Create alert"}
              </button>
            </div>
          </form>
        </div>
      </div>
      {selectedAlert && (
        <div className="modal-backdrop" onClick={() => setSelectedAlert(null)}>
          <div
            className="modal-content"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
          >
            <div className="modal-header">
              <div>
                <div className="modal-title">{selectedAlert.title}</div>
                <div className="modal-subtitle">
                  Created{" "}
                  {new Date(selectedAlert.created_at).toLocaleString()}
                </div>
              </div>
              <button
                className="modal-close-btn"
                type="button"
                onClick={() => setSelectedAlert(null)}
              >
                &times;
              </button>
            </div>
            <div className="modal-body">
              <div className="field-group">
                <div className="field-label">Description</div>
                <div>{selectedAlert.description}</div>
              </div>
              <div className="field-group">
                <div className="field-label">Source</div>
                <div className="muted">{selectedAlert.source}</div>
              </div>
              <div className="grid-2">
                <div className="field-group">
                  <div className="field-label">Severity</div>
                  <span className={`severity-pill severity-${selectedAlert.severity}`}>
                    {selectedAlert.severity.toUpperCase()}
                  </span>
                </div>
                <div className="field-group">
                  <div className="field-label">Status</div>
                  <span className="badge">{selectedAlert.status}</span>
                </div>
              </div>
              <div className="grid-2">
                <div className="field-group">
                  <div className="field-label">User</div>
                  <div>{selectedAlert.username ?? "—"}</div>
                </div>
                <div className="field-group">
                  <div className="field-label">Endpoint</div>
                  <div>{selectedAlert.hostname ?? "—"}</div>
                </div>
              </div>
              {selectedAlert.url && (
                <div className="field-group">
                  <div className="field-label">URL</div>
                  <a
                    href={selectedAlert.url}
                    target="_blank"
                    rel="noreferrer"
                    className="link"
                  >
                    {selectedAlert.url}
                  </a>
                </div>
              )}
              <div className="stack-horizontal" style={{ justifyContent: "space-between" }}>
                <button
                  type="button"
                  className="btn btn-ghost btn-sm"
                  onClick={() => {
                    setSelectedAlert(null);
                    navigate(`/alerts/${selectedAlert.id}`);
                  }}
                >
                  Open full view
                </button>
                <button
                  type="button"
                  className="btn btn-sm"
                  onClick={() => setSelectedAlert(null)}
                >
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

export default AlertsPage;
