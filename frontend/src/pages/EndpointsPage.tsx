import { useEffect, useMemo, useState } from "react";
import {
  createEndpointAction,
  getEndpoint,
  listEndpointActions,
  listEndpoints,
  type Endpoint,
  type EndpointAction,
} from "../services/api";
import { useToast } from "../components/common/ToastProvider";
import { EmptyState } from "../components/common/EmptyState";
import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";

const EndpointsPage = () => {
  const [endpoints, setEndpoints] = useState<Endpoint[]>([]);
  const [selected, setSelected] = useState<Endpoint | null>(null);
  const [actions, setActions] = useState<EndpointAction[]>([]);
  const [command, setCommand] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [offlineVisible, setOfflineVisible] = useState(true);
  const { pushToast } = useToast();

  const loadEndpoints = async () => {
    try {
      setLoading(true);
      const data = await listEndpoints();
      setEndpoints(data);
      if (data.length > 0) {
        const detail = await getEndpoint(data[0].id);
        setSelected(detail);
        const actionHistory = await listEndpointActions(data[0].id);
        setActions(actionHistory);
      }
      setError(null);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unexpected error while loading endpoints"
      );
    } finally {
      setLoading(false);
    }
  };

  const offlineEndpoints = useMemo(() => {
    const STALE_MS = 5 * 60 * 1000; // 5 minutes
    const now = Date.now();
    return endpoints.filter((e) => {
      const lastSeenMs = e.last_seen ? new Date(e.last_seen).getTime() : 0;
      const tooOld = !lastSeenMs || now - lastSeenMs > STALE_MS;
      return e.agent_status !== "connected" || tooOld;
    });
  }, [endpoints]);

  useEffect(() => {
    loadEndpoints().catch((err) => console.error(err));
  }, []);

  const handleSelect = async (endpoint: Endpoint) => {
    try {
      const detail = await getEndpoint(endpoint.id);
      setSelected(detail);
      const actionHistory = await listEndpointActions(endpoint.id);
      setActions(actionHistory);
    } catch (err) {
      const details = err instanceof Error ? err.message : "Unexpected error";
      pushToast({
        title: "Failed to load endpoint",
        message: "Please try again.",
        details,
        variant: "error",
      });
    }
  };

  const triggerAction = async (
    endpointId: number,
    action_type: EndpointAction["action_type"],
    parameters: Record<string, unknown> = {}
  ) => {
    try {
      await createEndpointAction(endpointId, { action_type, parameters });
      const updated = await listEndpointActions(endpointId);
      setActions(updated);
    } catch (err) {
      const details = err instanceof Error ? err.message : "Unexpected error";
      pushToast({
        title: "Failed to queue action",
        message: "Please retry or check agent connectivity.",
        details,
        variant: "error",
      });
    }
  };

  return (
    <div className="page-root">
      {offlineEndpoints.length > 0 && offlineVisible && (
        <div className="toast toast-error">
          <div className="toast-title">Agent offline detected</div>
          <div className="toast-body">
            {offlineEndpoints.map((ep) => (
              <div key={ep.id} className="toast-row">
                <div className="toast-row-title">{ep.display_name}</div>
                <div className="toast-row-meta">
                  <span className="tag danger">{ep.agent_status || "offline"}</span>
                  <span className="tag">{ep.ip_address}</span>
                  <span className="tag">Last seen: {ep.last_seen ? new Date(ep.last_seen).toLocaleString() : "unknown"}</span>
                </div>
              </div>
            ))}
          </div>
          <button type="button" className="btn btn-ghost btn-sm" onClick={() => setOfflineVisible(false)}>
            Dismiss
          </button>
        </div>
      )}

      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">Endpoint inventory</div>
          <div className="page-subtitle">
            Monitor agent health, resource usage, and open alerts for managed assets.
          </div>
        </div>
        <div className="stack-horizontal">
          <button type="button" className="btn btn-ghost" onClick={loadEndpoints}>
            Refresh
          </button>
        </div>
      </div>

      <div className="grid-3">
        <div className="card">
          <div className="card-subtitle">Total endpoints</div>
          <div className="card-value">{endpoints.length}</div>
        </div>
        <div className="card">
          <div className="card-subtitle">Connected</div>
          <div className="card-value">
            {endpoints.filter((e) => e.agent_status === "connected").length}
          </div>
        </div>
        <div className="card">
          <div className="card-subtitle">Alerts open</div>
          <div className="card-value">
            {endpoints.reduce((acc, item) => acc + item.alerts_open, 0)}
          </div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Asset list</div>
              <div className="card-subtitle">
                Select an endpoint to view deep-dive information.
              </div>
            </div>
          </div>

          {loading && <LoadingState message="Loading endpoints…" />}
          {error && (
            <ErrorState
              message="Failed to load endpoints."
              details={error}
              onRetry={() => loadEndpoints()}
            />
          )}
          {!loading && !error && endpoints.length === 0 && (
            <EmptyState
              title="No endpoints available"
              message="Connect an agent to see endpoint inventory."
            />
          )}
          {!loading && !error && endpoints.length > 0 && (
            <div className="stack-vertical">
              {endpoints.map((endpoint) => (
                <button
                  type="button"
                  key={endpoint.id}
                  className={`alert-row ${
                    selected?.id === endpoint.id ? "sidebar-link-active" : ""
                  }`}
                  onClick={() => handleSelect(endpoint)}
                >
                  <div className="alert-row-main">
                    <div className="alert-row-title">{endpoint.display_name}</div>
                    <div className="alert-row-meta">
                      <span className="tag">{endpoint.status}</span>
                      <span className="tag">{endpoint.ip_address}</span>
                    </div>
                  </div>
                  <div className="muted">{endpoint.owner}</div>
                </button>
              ))}
            </div>
          )}
        </div>

        {selected && (
          <div className="card">
            <div className="card-header">
              <div>
                <div className="card-title">
                  Endpoint details:
                  {" "}
                  {selected.display_name}
                </div>
                <div className="card-subtitle">
                  Last seen
                  {" "}
                  {new Date(selected.last_seen).toLocaleString()}
                </div>
              </div>
              <div className="stack-horizontal">
                <button
                  type="button"
                  className="btn btn-ghost btn-sm"
                  onClick={() => selected && triggerAction(selected.id, "command", { command: "run-scan" })}
                >
                  Run scan
                </button>
                <button
                  type="button"
                  className="btn btn-danger btn-sm"
                  onClick={() => selected && triggerAction(selected.id, "isolate")}
                >
                  Isolate endpoint
                </button>
                <button
                  type="button"
                  className="btn btn-ghost btn-sm"
                  onClick={() => selected && triggerAction(selected.id, "release")}
                >
                  Release
                </button>
                <button
                  type="button"
                  className="btn btn-ghost btn-sm"
                  onClick={() => selected && triggerAction(selected.id, "reboot")}
                >
                  Reboot
                </button>
              </div>
            </div>

            <div className="grid-2">
              <div className="stack-vertical">
                <div className="field-group">
                  <div className="field-label">Agent status</div>
                  <div className="tag">{selected.agent_status}</div>
                </div>
                <div className="field-group">
                  <div className="field-label">Agent version</div>
                  <div>{selected.agent_version}</div>
                </div>
                <div className="field-group">
                  <div className="field-label">Primary IP</div>
                  <div>{selected.ip_address}</div>
                </div>
              </div>
              <div className="stack-vertical">
                <div className="field-group">
                  <div className="field-label">Operating system</div>
                  <div>
                    {selected.os}
                    {" "}
                    {selected.os_version}
                  </div>
                </div>
                <div className="field-group">
                  <div className="field-label">Hardware</div>
                  <div>
                    {selected.cpu_model}
                    {" "}
                    •
                    {" "}
                    {selected.ram_gb}
                    {" "}
                    GB RAM •
                    {" "}
                    {selected.disk_gb}
                    {" "}
                    GB SSD
                  </div>
                </div>
                <div className="field-group">
                  <div className="field-label">Alerts open</div>
                  <div>{selected.alerts_open}</div>
                </div>
              </div>
            </div>

            <div className="grid-3" style={{ marginTop: "1rem" }}>
              <div className="card sandbox-mini">
                <div className="field-label">CPU usage</div>
                <div className="progress-bar">
                  <div
                    className="progress-track"
                    style={{ width: `${selected.resource_usage.cpu ?? 0}%` }}
                  />
                </div>
                <div className="muted">
                  {selected.resource_usage.cpu ?? 0}
                  %
                </div>
              </div>
              <div className="card sandbox-mini">
                <div className="field-label">Memory usage</div>
                <div className="progress-bar">
                  <div
                    className="progress-track"
                    style={{ width: `${selected.resource_usage.memory ?? 0}%` }}
                  />
                </div>
                <div className="muted">
                  {selected.resource_usage.memory ?? 0}
                  %
                </div>
              </div>
              <div className="card sandbox-mini">
                <div className="field-label">Disk usage</div>
                <div className="progress-bar">
                  <div
                    className="progress-track"
                    style={{ width: `${selected.resource_usage.disk ?? 0}%` }}
                  />
                </div>
                <div className="muted">
                  {selected.resource_usage.disk ?? 0}
                  %
                </div>
              </div>
            </div>

            <div className="stack-vertical" style={{ marginTop: "1rem" }}>
              <div className="field-label">Active processes</div>
              <div className="table-responsive">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Process</th>
                      <th>PID</th>
                      <th>User</th>
                      <th>CPU %</th>
                      <th>RAM %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selected.processes.map((proc) => (
                      <tr key={proc.pid}>
                        <td>{proc.name}</td>
                        <td>{proc.pid}</td>
                        <td>{proc.user}</td>
                        <td>{proc.cpu.toFixed(2)}</td>
                        <td>{proc.ram.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="stack-vertical" style={{ marginTop: "1rem" }}>
              <div className="field-label">Remote command</div>
              <div className="stack-horizontal">
                <input
                  className="field-control"
                  placeholder="e.g. Get-WinEvent Security"
                  value={command}
                  onChange={(e) => setCommand(e.target.value)}
                />
                <button
                  type="button"
                  className="btn btn-sm"
                  onClick={() => {
                    if (!selected || !command.trim()) return;
                    triggerAction(selected.id, "command", { command: command.trim() });
                    setCommand("");
                  }}
                >
                  Execute
                </button>
              </div>
            </div>

            <div className="stack-vertical" style={{ marginTop: "1rem" }}>
              <div className="field-label">Action history</div>
              {actions.length === 0 ? (
                <div className="muted">No actions requested for this endpoint.</div>
              ) : (
                <div className="table-responsive">
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Type</th>
                        <th>Status</th>
                        <th>Requested</th>
                      </tr>
                    </thead>
                    <tbody>
                      {actions.map((action) => (
                        <tr key={action.id}>
                          <td>{action.action_type}</td>
                          <td>{action.status}</td>
                          <td>{new Date(action.requested_at).toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default EndpointsPage;
