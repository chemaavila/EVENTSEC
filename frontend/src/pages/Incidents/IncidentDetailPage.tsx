import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import type { Incident, IncidentUpdatePayload } from "../../services/incidents";
import { getIncident, updateIncident } from "../../services/incidents";
import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import { useToast } from "../../components/common/ToastProvider";

const IncidentDetailPage = () => {
  const { incidentId } = useParams();
  const navigate = useNavigate();
  const { pushToast } = useToast();
  const [incident, setIncident] = useState<Incident | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<IncidentUpdatePayload["status"]>(
    "new"
  );
  const [severity, setSeverity] = useState<IncidentUpdatePayload["severity"]>(
    "medium"
  );

  const loadIncident = async () => {
    if (!incidentId) return;
    try {
      setLoading(true);
      const data = await getIncident(incidentId);
      setIncident(data);
      setStatus(data.status);
      setSeverity(data.severity);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load incident");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadIncident();
  }, [incidentId]);

  const handleUpdate = async () => {
    if (!incident || !incidentId) return;
    try {
      const updated = await updateIncident(incidentId, {
        status,
        severity,
      });
      setIncident(updated);
      pushToast({
        title: "Incident updated",
        message: "Status and severity saved.",
        variant: "success",
      });
    } catch (err) {
      pushToast({
        title: "Failed to update incident",
        message: "Please try again.",
        details: err instanceof Error ? err.message : "Unknown error",
        variant: "error",
      });
    }
  };

  if (loading) {
    return <LoadingState message="Loading incident…" />;
  }

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!incident) {
    return <EmptyState message="Incident not found." />;
  }

  return (
    <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">Incident {String(incident.id).padStart(4, "0")}</div>
          <div className="page-subtitle">{incident.title}</div>
        </div>
        <div className="stack-horizontal">
          <button type="button" className="btn btn-ghost" onClick={() => navigate(-1)}>
            Back
          </button>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Incident details</div>
              <div className="card-subtitle">Status and ownership controls.</div>
            </div>
          </div>
          <div className="stack-vertical">
            <label className="field">
              <span className="field-label">Status</span>
              <select value={status} onChange={(e) => setStatus(e.target.value as IncidentUpdatePayload["status"])}>
                <option value="new">New</option>
                <option value="triage">Triage</option>
                <option value="in_progress">In progress</option>
                <option value="contained">Contained</option>
                <option value="resolved">Resolved</option>
                <option value="closed">Closed</option>
              </select>
            </label>
            <label className="field">
              <span className="field-label">Severity</span>
              <select value={severity} onChange={(e) => setSeverity(e.target.value as IncidentUpdatePayload["severity"])}>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </label>
            <label className="field">
              <span className="field-label">Description</span>
              <textarea value={incident.description ?? ""} readOnly rows={6} />
            </label>
            <div className="stack-horizontal" style={{ justifyContent: "flex-end" }}>
              <button type="button" className="btn" onClick={handleUpdate}>
                Update
              </button>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Timeline</div>
              <div className="card-subtitle">Attached evidence and actions.</div>
            </div>
          </div>
          {incident.items.length === 0 ? (
            <EmptyState message="No items attached yet." />
          ) : (
            <div className="stack-vertical">
              {incident.items.map((item) => (
                <div key={item.id} className="card-inline">
                  <div className="stack-horizontal" style={{ justifyContent: "space-between" }}>
                    <span className="pill">{item.kind.toUpperCase()}</span>
                    <span className="muted">
                      {new Date(item.created_at).toLocaleString()}
                    </span>
                  </div>
                  <div className="muted">Ref: {item.ref_id}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default IncidentDetailPage;
