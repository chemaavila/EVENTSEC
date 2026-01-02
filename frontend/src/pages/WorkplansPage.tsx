import { useEffect, useMemo, useState } from "react";
import {
  createWorkplan,
  listAlerts,
  listWorkplans,
  updateWorkplan,
  type Alert,
  type Workplan,
  type WorkplanCreatePayload,
} from "../services/api";
import { useToast } from "../components/common/ToastProvider";
import { EmptyState } from "../components/common/EmptyState";
import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";

const defaultWorkplan: WorkplanCreatePayload = {
  title: "",
  description: "",
  alert_id: undefined,
  assigned_to: undefined,
};

const WorkplansPage = () => {
  const [workplans, setWorkplans] = useState<Workplan[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [form, setForm] = useState(defaultWorkplan);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filterAlertId, setFilterAlertId] = useState<number | null>(null);
  const { pushToast } = useToast();

  const loadData = async () => {
    try {
      setLoading(true);
      const [plans, alertData] = await Promise.all([listWorkplans(), listAlerts()]);
      setWorkplans(plans);
      setAlerts(alertData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load workplans");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData().catch((err) => console.error(err));
  }, []);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]:
        name === "alert_id" || name === "assigned_to"
          ? value
            ? Number(value)
            : undefined
          : value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      await createWorkplan(form);
      setForm(defaultWorkplan);
      await loadData();
    } catch (err) {
      const details = err instanceof Error ? err.message : "Unknown error";
      pushToast({
        title: "Failed to create workplan",
        message: "Please check the payload and try again.",
        details,
        variant: "error",
      });
    } finally {
      setSaving(false);
    }
  };

  const handleStatusChange = async (plan: Workplan, status: string) => {
    try {
      await updateWorkplan(plan.id, { status });
      await loadData();
    } catch (err) {
      const details = err instanceof Error ? err.message : "Unknown error";
      pushToast({
        title: "Unable to update status",
        message: "Please try again in a moment.",
        details,
        variant: "error",
      });
    }
  };

  const filteredPlans = useMemo(() => {
    if (!filterAlertId) return workplans;
    return workplans.filter((wp) => wp.alert_id === filterAlertId);
  }, [filterAlertId, workplans]);

  return (
    <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">Workplans</div>
          <div className="page-subtitle">
            Create plans, assign owners and tie tasks to specific alerts.
          </div>
        </div>
        <div className="stack-horizontal">
          <button type="button" className="btn btn-ghost" onClick={loadData} disabled={loading}>
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <ErrorState
          message="Failed to load workplans."
          details={error}
          onRetry={() => loadData()}
        />
      )}

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Existing workplans</div>
              <div className="card-subtitle">Track progress per alert.</div>
            </div>
            <div className="stack-horizontal" style={{ gap: "0.5rem" }}>
              <label className="field-label">Filter by alert</label>
              <select
                className="field-control"
                value={filterAlertId ?? ""}
                onChange={(e) => setFilterAlertId(e.target.value ? Number(e.target.value) : null)}
              >
                <option value="">All</option>
                {alerts.map((alert) => (
                  <option key={alert.id} value={alert.id}>
                    #{alert.id} {alert.title}
                  </option>
                ))}
              </select>
            </div>
          </div>
          {loading ? (
            <LoadingState message="Loading workplans…" />
          ) : workplans.length === 0 ? (
            <EmptyState
              title="No workplans yet"
              message="Create a workplan to assign tasks to alerts."
            />
          ) : (
            <div className="stack-vertical">
              {filteredPlans.map((plan) => (
                <div key={plan.id} className="card sandbox-mini">
                  <div className="stack-horizontal" style={{ justifyContent: "space-between" }}>
                    <div>
                      <div className="card-title">{plan.title}</div>
                      <div className="muted small">{plan.description}</div>
                    </div>
                    <select
                      className="field-control"
                      value={plan.status}
                      onChange={(e) => handleStatusChange(plan, e.target.value)}
                    >
                      <option value="open">Open</option>
                      <option value="in_progress">In progress</option>
                      <option value="blocked">Blocked</option>
                      <option value="closed">Closed</option>
                    </select>
                  </div>
                  <div className="muted small">
                    Alert:
                    {" "}
                    {plan.alert_id ?? "N/A"}
                    {" • Updated "}
                    {new Date(plan.updated_at).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Create workplan</div>
              <div className="card-subtitle">Assign an owner and link it to an alert.</div>
            </div>
          </div>
          <form className="stack-vertical" onSubmit={handleSubmit}>
            <div className="field-group">
              <label htmlFor="workplan-title" className="field-label">
                Title
              </label>
              <input
                id="workplan-title"
                name="title"
                className="field-control"
                value={form.title}
                onChange={handleChange}
                required
              />
            </div>
            <div className="field-group">
              <label htmlFor="workplan-description" className="field-label">
                Description
              </label>
              <textarea
                id="workplan-description"
                name="description"
                className="field-control"
                rows={3}
                value={form.description}
                onChange={handleChange}
                required
              />
            </div>
            <div className="grid-2">
              <div className="field-group">
                <label htmlFor="workplan-alert" className="field-label">
                  Related alert
                </label>
                <select
                  id="workplan-alert"
                  name="alert_id"
                  className="field-control"
                  value={form.alert_id ?? ""}
                  onChange={handleChange}
                >
                  <option value="">Unassigned</option>
                  {alerts.map((alert) => (
                    <option key={alert.id} value={alert.id}>
                      #{alert.id}
                      {" "}
                      {alert.title}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field-group">
                <label htmlFor="workplan-assigned" className="field-label">
                  Assigned to (user ID)
                </label>
                <input
                  id="workplan-assigned"
                  name="assigned_to"
                  className="field-control"
                  type="number"
                  value={form.assigned_to ?? ""}
                  onChange={handleChange}
                  min={1}
                />
              </div>
            </div>
            <div style={{ textAlign: "right" }}>
              <button type="submit" className="btn btn-sm" disabled={saving}>
                {saving ? "Saving…" : "Create workplan"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default WorkplansPage;
