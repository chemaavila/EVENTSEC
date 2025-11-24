import { useEffect, useState } from "react";
import { listAnalyticsRules, type AnalyticsRule } from "../services/api";

const AnalyticsRulesPage = () => {
  const [rules, setRules] = useState<AnalyticsRule[]>([]);
  const [selectedRule, setSelectedRule] = useState<AnalyticsRule | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadRules = async () => {
    try {
      setLoading(true);
      const data = await listAnalyticsRules();
      setRules(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load rules");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRules().catch((err) => console.error(err));
  }, []);

  return (
    <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">Analytics rules</div>
          <div className="page-subtitle">
            KQL/Sigma detections powering the SOC workflows.
          </div>
        </div>
        <div className="stack-horizontal">
          <button type="button" className="btn btn-ghost" onClick={loadRules} disabled={loading}>
            Refresh
          </button>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">Rules</div>
            <div className="card-subtitle">
              Click a rule to inspect the query and metadata.
            </div>
          </div>
        </div>

        {error && (
          <div className="muted" style={{ color: "var(--danger)" }}>
            {error}
          </div>
        )}

        {loading ? (
          <div className="muted">Loading rules…</div>
        ) : rules.length === 0 ? (
          <div className="muted">No rules configured.</div>
        ) : (
          <div className="stack-vertical">
            {rules.map((rule) => (
              <button
                key={rule.id}
                type="button"
                className="alert-row"
                onClick={() => setSelectedRule(rule)}
              >
                <div className="alert-row-main">
                  <div className="alert-row-title">
                    #{rule.id}
                    {" "}
                    —{" "}
                    {rule.name}
                  </div>
                  <div className="alert-row-meta">
                    <span className="tag">{rule.datasource}</span>
                    <span className="tag">{rule.owner}</span>
                  </div>
                </div>
                <div className="stack-horizontal">
                  <span className={`severity-pill severity-${rule.severity}`}>
                    {rule.severity.toUpperCase()}
                  </span>
                  <span className="badge">{rule.status}</span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {selectedRule && (
        <div className="modal-backdrop" onClick={() => setSelectedRule(null)}>
          <div
            className="modal-content"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
          >
            <div className="modal-header">
              <div>
                <div className="modal-title">{selectedRule.name}</div>
                <div className="modal-subtitle">
                  Last updated{" "}
                  {new Date(selectedRule.updated_at).toLocaleString()}
                </div>
              </div>
              <button
                type="button"
                className="modal-close-btn"
                onClick={() => setSelectedRule(null)}
              >
                &times;
              </button>
            </div>
            <div className="modal-body">
              <div className="field-group">
                <div className="field-label">Datasource</div>
                <div>{selectedRule.datasource}</div>
              </div>
              <div className="field-group">
                <div className="field-label">Description</div>
                <div>{selectedRule.description}</div>
              </div>
              <div className="field-group">
                <div className="field-label">Detection query</div>
                <pre className="code-block">{selectedRule.query}</pre>
              </div>
              <div className="stack-horizontal" style={{ justifyContent: "flex-end" }}>
                <button
                  type="button"
                  className="btn btn-sm"
                  onClick={() => setSelectedRule(null)}
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

export default AnalyticsRulesPage;
