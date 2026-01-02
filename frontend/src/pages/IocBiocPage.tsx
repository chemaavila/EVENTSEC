import { useEffect, useState } from "react";
import {
  createBiocRule,
  createIndicator,
  listBiocRules,
  listIndicators,
  updateBiocRule,
  updateIndicator,
  type BiocRule,
  type BiocRulePayload,
  type Indicator,
  type IndicatorCreatePayload,
} from "../services/api";
import { useToast } from "../components/common/ToastProvider";

type IndicatorFormState = IndicatorCreatePayload & { tagsInput: string };
type BiocFormState = BiocRulePayload & { tagsInput: string };

const defaultIndicatorForm: IndicatorFormState = {
  type: "url",
  value: "",
  description: "",
  severity: "medium",
  source: "manual",
  tags: [],
  tagsInput: "",
};

const defaultBiocForm: BiocFormState = {
  name: "",
  description: "",
  platform: "Windows",
  tactic: "Execution",
  technique: "",
  detection_logic: "",
  severity: "medium",
  tags: [],
  tagsInput: "",
};

const IocBiocPage = () => {
  const [indicators, setIndicators] = useState<Indicator[]>([]);
  const [biocs, setBiocs] = useState<BiocRule[]>([]);
  const [indicatorForm, setIndicatorForm] = useState<IndicatorFormState>(defaultIndicatorForm);
  const [biocForm, setBiocForm] = useState<BiocFormState>(defaultBiocForm);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { pushToast } = useToast();

  const loadData = async () => {
    try {
      setLoading(true);
      const [indicatorData, biocData] = await Promise.all([listIndicators(), listBiocRules()]);
      setIndicators(indicatorData);
      setBiocs(biocData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load intel data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData().catch((err) => console.error(err));
  }, []);

  const handleIndicatorChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setIndicatorForm((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleBiocChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setBiocForm((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleIndicatorSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createIndicator({
        type: indicatorForm.type,
        value: indicatorForm.value,
        description: indicatorForm.description,
        severity: indicatorForm.severity,
        source: indicatorForm.source,
        tags: indicatorForm.tagsInput
          .split(",")
          .map((tag) => tag.trim())
          .filter(Boolean),
      });
      setIndicatorForm(defaultIndicatorForm);
      await loadData();
    } catch (err) {
      const details = err instanceof Error ? err.message : "Unknown error";
      pushToast({
        title: "Failed to add indicator",
        message: "Please check the payload and try again.",
        details,
        variant: "error",
      });
    }
  };

  const handleBiocSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createBiocRule({
        name: biocForm.name,
        description: biocForm.description,
        platform: biocForm.platform,
        tactic: biocForm.tactic,
        technique: biocForm.technique,
        detection_logic: biocForm.detection_logic,
        severity: biocForm.severity,
        tags: biocForm.tagsInput
          .split(",")
          .map((tag) => tag.trim())
          .filter(Boolean),
      });
      setBiocForm(defaultBiocForm);
      await loadData();
    } catch (err) {
      const details = err instanceof Error ? err.message : "Unknown error";
      pushToast({
        title: "Failed to add BIOC",
        message: "Please check the payload and try again.",
        details,
        variant: "error",
      });
    }
  };

  const handleIndicatorStatusChange = async (indicator: Indicator, status: "active" | "retired") => {
    try {
      await updateIndicator(indicator.id, { status });
      await loadData();
    } catch (err) {
      const details = err instanceof Error ? err.message : "Unknown error";
      pushToast({
        title: "Failed to update indicator",
        message: "Please try again.",
        details,
        variant: "error",
      });
    }
  };

  const handleBiocStatusChange = async (rule: BiocRule, status: "enabled" | "disabled") => {
    try {
      await updateBiocRule(rule.id, { status });
      await loadData();
    } catch (err) {
      const details = err instanceof Error ? err.message : "Unknown error";
      pushToast({
        title: "Failed to update BIOC",
        message: "Please try again.",
        details,
        variant: "error",
      });
    }
  };

  return (
    <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">IOC / BIOC</div>
          <div className="page-subtitle">
            Manage indicators of compromise and behavioral analytics without mixing them with generated endpoint data.
          </div>
        </div>
        <div className="stack-horizontal">
          <button type="button" className="btn btn-ghost" onClick={loadData} disabled={loading}>
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="muted" style={{ color: "var(--danger)" }}>
          Failed to load data:
          {" "}
          {error}
        </div>
      )}

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Indicators of compromise</div>
              <div className="card-subtitle">URLs, hashes, domains, IPs.</div>
            </div>
          </div>
          {indicators.length === 0 ? (
            <div className="muted">{loading ? "Loading indicators…" : "No indicators yet."}</div>
          ) : (
            <div className="table-responsive">
              <table className="table">
                <thead>
                  <tr>
                    <th>Type</th>
                    <th>Value</th>
                    <th>Severity</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {indicators.map((indicator) => (
                    <tr key={indicator.id}>
                      <td>
                        <span className="tag">{indicator.type.toUpperCase()}</span>
                      </td>
                      <td>
                        <div className="table-ellipsis">{indicator.value}</div>
                        <div className="muted small">{indicator.description}</div>
                      </td>
                      <td>
                        <span className={`severity-pill severity-${indicator.severity}`}>
                          {indicator.severity.toUpperCase()}
                        </span>
                      </td>
                      <td>
                        <select
                          className="field-control"
                          value={indicator.status}
                          onChange={(e) =>
                            handleIndicatorStatusChange(
                              indicator,
                              e.target.value as "active" | "retired"
                            )
                          }
                        >
                          <option value="active">Active</option>
                          <option value="retired">Retired</option>
                        </select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <form className="stack-vertical" onSubmit={handleIndicatorSubmit} style={{ marginTop: "1rem" }}>
            <div className="grid-2">
              <div className="field-group">
                <label htmlFor="indicator-type" className="field-label">
                  Type
                </label>
                <select
                  id="indicator-type"
                  name="type"
                  className="field-control"
                  value={indicatorForm.type}
                  onChange={handleIndicatorChange}
                >
                  <option value="url">URL</option>
                  <option value="ip">IP</option>
                  <option value="domain">Domain</option>
                  <option value="hash">Hash</option>
                  <option value="email">Email</option>
                </select>
              </div>
              <div className="field-group">
                <label htmlFor="indicator-severity" className="field-label">
                  Severity
                </label>
                <select
                  id="indicator-severity"
                  name="severity"
                  className="field-control"
                  value={indicatorForm.severity}
                  onChange={handleIndicatorChange}
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>
            </div>
            <div className="field-group">
              <label htmlFor="indicator-value" className="field-label">
                Value
              </label>
              <input
                id="indicator-value"
                name="value"
                className="field-control"
                value={indicatorForm.value}
                onChange={handleIndicatorChange}
                required
              />
            </div>
            <div className="field-group">
              <label htmlFor="indicator-description" className="field-label">
                Description
              </label>
              <textarea
                id="indicator-description"
                name="description"
                className="field-control"
                rows={2}
                value={indicatorForm.description}
                onChange={handleIndicatorChange}
              />
            </div>
            <div className="field-group">
              <label htmlFor="indicator-tagsInput" className="field-label">
                Tags (comma separated)
              </label>
              <input
                id="indicator-tagsInput"
                name="tagsInput"
                className="field-control"
                value={indicatorForm.tagsInput}
                onChange={handleIndicatorChange}
              />
            </div>
            <div style={{ textAlign: "right" }}>
              <button type="submit" className="btn btn-sm" disabled={loading}>
                Add indicator
              </button>
            </div>
          </form>
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Behavior analytics (BIOCs)</div>
              <div className="card-subtitle">
                Author custom detections for process, network, or authentication behaviors.
              </div>
            </div>
          </div>

          {biocs.length === 0 ? (
            <div className="muted">{loading ? "Loading BIOCs…" : "No behavioral rules yet."}</div>
          ) : (
            <div className="table-responsive">
              <table className="table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Platform</th>
                    <th>Severity</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {biocs.map((rule) => (
                    <tr key={rule.id}>
                      <td>
                        <div className="table-ellipsis">{rule.name}</div>
                        <div className="muted small">{rule.description}</div>
                      </td>
                      <td>
                        <span className="tag">{rule.platform}</span>
                        <span className="tag">{rule.tactic}</span>
                      </td>
                      <td>
                        <span className={`severity-pill severity-${rule.severity}`}>
                          {rule.severity.toUpperCase()}
                        </span>
                      </td>
                      <td>
                        <select
                          className="field-control"
                          value={rule.status}
                          onChange={(e) =>
                            handleBiocStatusChange(
                              rule,
                              e.target.value as "enabled" | "disabled"
                            )
                          }
                        >
                          <option value="enabled">Enabled</option>
                          <option value="disabled">Disabled</option>
                        </select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <form className="stack-vertical" onSubmit={handleBiocSubmit} style={{ marginTop: "1rem" }}>
            <div className="field-group">
              <label htmlFor="bioc-name" className="field-label">
                Rule name
              </label>
              <input
                id="bioc-name"
                name="name"
                className="field-control"
                value={biocForm.name}
                onChange={handleBiocChange}
                required
              />
            </div>
            <div className="field-group">
              <label htmlFor="bioc-platform" className="field-label">
                Platform
              </label>
              <input
                id="bioc-platform"
                name="platform"
                className="field-control"
                value={biocForm.platform}
                onChange={handleBiocChange}
              />
            </div>
            <div className="grid-2">
              <div className="field-group">
                <label htmlFor="bioc-tactic" className="field-label">
                  MITRE tactic
                </label>
                <input
                  id="bioc-tactic"
                  name="tactic"
                  className="field-control"
                  value={biocForm.tactic}
                  onChange={handleBiocChange}
                />
              </div>
              <div className="field-group">
                <label htmlFor="bioc-technique" className="field-label">
                  Technique
                </label>
                <input
                  id="bioc-technique"
                  name="technique"
                  className="field-control"
                  value={biocForm.technique}
                  onChange={handleBiocChange}
                />
              </div>
            </div>
            <div className="field-group">
              <label htmlFor="bioc-detection_logic" className="field-label">
                Detection logic
              </label>
              <textarea
                id="bioc-detection_logic"
                name="detection_logic"
                className="field-control"
                rows={3}
                value={biocForm.detection_logic}
                onChange={handleBiocChange}
                required
              />
            </div>
            <div className="grid-2">
              <div className="field-group">
                <label htmlFor="bioc-severity" className="field-label">
                  Severity
                </label>
                <select
                  id="bioc-severity"
                  name="severity"
                  className="field-control"
                  value={biocForm.severity}
                  onChange={handleBiocChange}
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>
              <div className="field-group">
                <label htmlFor="bioc-tagsInput" className="field-label">
                  Tags
                </label>
                <input
                  id="bioc-tagsInput"
                  name="tagsInput"
                  className="field-control"
                  value={biocForm.tagsInput}
                  onChange={handleBiocChange}
                />
              </div>
            </div>
            <div style={{ textAlign: "right" }}>
              <button type="submit" className="btn btn-sm" disabled={loading}>
                Add BIOC
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default IocBiocPage;
