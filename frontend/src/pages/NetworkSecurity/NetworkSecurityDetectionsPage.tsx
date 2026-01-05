import { useEffect, useMemo, useState } from "react";
import type { DetectionRule } from "../../services/api";
import { listDetectionRules } from "../../services/api";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import { EmptyState } from "../../components/common/EmptyState";

const NetworkSecurityDetectionsPage = () => {
  const [rules, setRules] = useState<DetectionRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadRules = async () => {
    try {
      setLoading(true);
      const data = await listDetectionRules();
      setRules(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load rules");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRules();
  }, []);

  const networkRules = useMemo(
    () =>
      rules.filter(
        (rule) =>
          (rule.conditions as Record<string, unknown>)?.["event_type"] ===
            "network" ||
          (rule.conditions as Record<string, unknown>)?.["details.source"] ===
            "suricata" ||
          (rule.conditions as Record<string, unknown>)?.["details.source"] === "zeek"
      ),
    [rules]
  );

  return (
    <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">Network Detections</div>
          <div className="page-subtitle">
            Detection rules evaluated against IDS events.
          </div>
        </div>
        <div className="stack-horizontal">
          <button type="button" className="btn btn-ghost" onClick={loadRules}>
            Refresh
          </button>
        </div>
      </div>

      {loading && <LoadingState message="Loading detection rules…" />}
      {error && <ErrorState message={error} />}

      {!loading && !error && (
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Network rules</div>
              <div className="card-subtitle">
                {networkRules.length} rules scoped to network telemetry.
              </div>
            </div>
          </div>
          {networkRules.length === 0 ? (
            <EmptyState message="No network detection rules configured yet." />
          ) : (
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Severity</th>
                    <th>Status</th>
                    <th>Create Incident</th>
                    <th>Conditions</th>
                  </tr>
                </thead>
                <tbody>
                  {networkRules.map((rule) => (
                    <tr key={rule.id}>
                      <td>{rule.name}</td>
                      <td>{rule.severity}</td>
                      <td>{rule.enabled ? "Enabled" : "Disabled"}</td>
                      <td>{rule.create_incident ? "Yes" : "No"}</td>
                      <td>
                        <pre className="code-block">
                          {JSON.stringify(rule.conditions, null, 2)}
                        </pre>
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

export default NetworkSecurityDetectionsPage;
