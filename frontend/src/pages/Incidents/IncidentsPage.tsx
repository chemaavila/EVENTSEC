import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { Incident, IncidentCreatePayload } from "../../services/incidents";
import { createIncident, listIncidents } from "../../services/incidents";
import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import { useToast } from "../../components/common/ToastProvider";

const emptyForm: IncidentCreatePayload = {
  title: "",
  description: "",
  severity: "medium",
  status: "new",
  tags: [],
};

const IncidentsPage = () => {
  const navigate = useNavigate();
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<IncidentCreatePayload>(emptyForm);
  const [submitting, setSubmitting] = useState(false);
  const { pushToast } = useToast();

  const loadIncidents = async () => {
    try {
      setLoading(true);
      const data = await listIncidents();
      setIncidents(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load incidents");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadIncidents();
  }, []);

  const handleChange = (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      setSubmitting(true);
      await createIncident({
        title: form.title,
        description: form.description?.trim() || undefined,
        severity: form.severity,
        status: form.status,
      });
      setForm(emptyForm);
      await loadIncidents();
    } catch (err) {
      pushToast({
        title: "Failed to create incident",
        message: "Check the details and try again.",
        details: err instanceof Error ? err.message : "Unknown error",
        variant: "error",
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">Incidents</div>
          <div className="page-subtitle">
            Track investigations created from alerts and network detections.
          </div>
        </div>
        <div className="stack-horizontal">
          <button type="button" className="btn btn-ghost" onClick={loadIncidents}>
            Refresh
          </button>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Create incident</div>
              <div className="card-subtitle">
                Manual creation for ad-hoc investigations.
              </div>
            </div>
          </div>
          <form className="stack-vertical" onSubmit={handleSubmit}>
            <label className="field">
              <span className="field-label">Title</span>
              <input
                name="title"
                value={form.title ?? ""}
                onChange={handleChange}
                placeholder="Suspicious outbound traffic"
                required
              />
            </label>
            <label className="field">
              <span className="field-label">Description</span>
              <textarea
                name="description"
                value={form.description ?? ""}
                onChange={handleChange}
                placeholder="Context for the investigation"
                rows={4}
              />
            </label>
            <label className="field">
              <span className="field-label">Severity</span>
              <select name="severity" value={form.severity} onChange={handleChange}>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </label>
            <label className="field">
              <span className="field-label">Status</span>
              <select name="status" value={form.status} onChange={handleChange}>
                <option value="new">New</option>
                <option value="triage">Triage</option>
                <option value="in_progress">In progress</option>
                <option value="contained">Contained</option>
                <option value="resolved">Resolved</option>
                <option value="closed">Closed</option>
              </select>
            </label>
            <div className="stack-horizontal" style={{ justifyContent: "flex-end" }}>
              <button type="submit" className="btn" disabled={submitting}>
                {submitting ? "Creating…" : "Create"}
              </button>
            </div>
          </form>
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Active incidents</div>
              <div className="card-subtitle">{incidents.length} incidents</div>
            </div>
          </div>
          {loading && <LoadingState message="Loading incidents…" />}
          {error && <ErrorState message={error} />}
          {!loading && !error && incidents.length === 0 && (
            <EmptyState message="No incidents created yet." />
          )}
          {!loading && !error && incidents.length > 0 && (
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Title</th>
                    <th>Severity</th>
                    <th>Status</th>
                    <th>Updated</th>
                  </tr>
                </thead>
                <tbody>
                  {incidents.map((incident) => (
                    <tr
                      key={incident.id}
                      onClick={() => navigate(`/incidents/${incident.id}`)}
                      style={{ cursor: "pointer" }}
                    >
                      <td>{String(incident.id).padStart(4, "0")}</td>
                      <td>{incident.title}</td>
                      <td>{incident.severity}</td>
                      <td>{incident.status}</td>
                      <td>{new Date(incident.updated_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default IncidentsPage;
