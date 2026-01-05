import { useEffect, useState } from "react";
import {
  createResponseAction,
  listResponseActions,
} from "../../services/actions";
import type { ResponseAction } from "../../services/actions";
import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import { useToast } from "../../components/common/ToastProvider";

const emptyForm = {
  action_type: "BLOCK_IP",
  target: "",
  ttl_minutes: "60",
};

const NetworkSecurityActionsPage = () => {
  const [actions, setActions] = useState<ResponseAction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [submitting, setSubmitting] = useState(false);
  const { pushToast } = useToast();

  const loadActions = async () => {
    try {
      setLoading(true);
      const data = await listResponseActions();
      setActions(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load actions");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadActions();
  }, []);

  const handleChange = (
    event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      setSubmitting(true);
      await createResponseAction({
        action_type: form.action_type,
        target: form.target,
        ttl_minutes: form.ttl_minutes ? Number(form.ttl_minutes) : undefined,
      });
      setForm(emptyForm);
      await loadActions();
    } catch (err) {
      pushToast({
        title: "Failed to create action",
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
          <div className="page-title">Response Actions (IPS-lite)</div>
          <div className="page-subtitle">
            Track orchestrated response actions without inline blocking.
          </div>
        </div>
        <div className="stack-horizontal">
          <button type="button" className="btn btn-ghost" onClick={loadActions}>
            Refresh
          </button>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Create action</div>
              <div className="card-subtitle">
                Submit a response request for external execution.
              </div>
            </div>
          </div>
          <form className="stack-vertical" onSubmit={handleSubmit}>
            <label className="field">
              <span className="field-label">Action type</span>
              <select
                name="action_type"
                value={form.action_type}
                onChange={handleChange}
              >
                <option value="BLOCK_IP">BLOCK_IP</option>
                <option value="BLOCK_DOMAIN">BLOCK_DOMAIN</option>
                <option value="QUARANTINE_HOST">QUARANTINE_HOST</option>
                <option value="DISABLE_USER">DISABLE_USER</option>
                <option value="CREATE_TICKET">CREATE_TICKET</option>
              </select>
            </label>
            <label className="field">
              <span className="field-label">Target</span>
              <input
                name="target"
                value={form.target}
                onChange={handleChange}
                placeholder="1.2.3.4 or domain"
                required
              />
            </label>
            <label className="field">
              <span className="field-label">TTL (minutes)</span>
              <input
                name="ttl_minutes"
                value={form.ttl_minutes}
                onChange={handleChange}
                type="number"
                min={1}
              />
            </label>
            <div className="stack-horizontal" style={{ justifyContent: "flex-end" }}>
              <button type="submit" className="btn" disabled={submitting}>
                {submitting ? "Submitting…" : "Create"}
              </button>
            </div>
          </form>
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Queued actions</div>
              <div className="card-subtitle">{actions.length} actions</div>
            </div>
          </div>
          {loading && <LoadingState message="Loading actions…" />}
          {error && <ErrorState message={error} />}
          {!loading && !error && actions.length === 0 && (
            <EmptyState message="No response actions yet." />
          )}
          {!loading && !error && actions.length > 0 && (
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Type</th>
                    <th>Target</th>
                    <th>Status</th>
                    <th>Requested</th>
                  </tr>
                </thead>
                <tbody>
                  {actions.map((action) => (
                    <tr key={action.id}>
                      <td>{action.action_type}</td>
                      <td>{action.target}</td>
                      <td>{action.status}</td>
                      <td>{new Date(action.created_at).toLocaleString()}</td>
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

export default NetworkSecurityActionsPage;
