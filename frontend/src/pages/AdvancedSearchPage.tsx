import { useState } from "react";

const AdvancedSearchPage = () => {
  const [query, setQuery] = useState("");
  const [source, setSource] = useState("all");
  const [severity, setSeverity] = useState("any");
  const [status, setStatus] = useState("any");

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    // For demo purposes we just log the query
    // In a real implementation this would call an API endpoint.
    // eslint-disable-next-line no-console
    console.log({ query, source, severity, status });
  };

  return (
    <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">Advanced search</div>
          <div className="page-subtitle">
            Static layout representing an advanced search across alerts and raw events.
          </div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Search builder</div>
              <div className="card-subtitle">
                Build a query combining natural text and filters.
              </div>
            </div>
          </div>

          <form className="stack-vertical" onSubmit={handleSubmit}>
            <div className="field-group">
              <label htmlFor="query" className="field-label">
                Free text
              </label>
              <textarea
                id="query"
                className="field-control"
                rows={4}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ex: phishing alerts with URL and high severity last 24h"
              />
            </div>

            <div className="grid-2">
              <div className="field-group">
                <label htmlFor="source" className="field-label">
                  Source
                </label>
                <select
                  id="source"
                  className="field-control"
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                >
                  <option value="all">All sources</option>
                  <option value="siem">SIEM</option>
                  <option value="edr">EDR</option>
                  <option value="auth">Authentication</option>
                </select>
              </div>
              <div className="field-group">
                <label htmlFor="severity" className="field-label">
                  Severity
                </label>
                <select
                  id="severity"
                  className="field-control"
                  value={severity}
                  onChange={(e) => setSeverity(e.target.value)}
                >
                  <option value="any">Any</option>
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>
            </div>

            <div className="field-group">
              <label htmlFor="status" className="field-label">
                Status
              </label>
              <select
                id="status"
                className="field-control"
                value={status}
                onChange={(e) => setStatus(e.target.value)}
              >
                <option value="any">Any</option>
                <option value="open">Open</option>
                <option value="in_progress">In progress</option>
                <option value="closed">Closed</option>
              </select>
            </div>

            <div className="stack-horizontal" style={{ justifyContent: "flex-end" }}>
              <button type="submit" className="btn btn-sm">
                Run search (demo)
              </button>
            </div>
          </form>
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Results (demo)</div>
              <div className="card-subtitle">
                Static explanation of how results would be presented.
              </div>
            </div>
          </div>

          <div className="stack-vertical">
            <div className="muted">
              In a real deployment this panel would show:
            </div>
            <ul className="muted">
              <li>Matching alerts with severity, source and status.</li>
              <li>Raw events from SIEM queries.</li>
              <li>Facets to refine by time range, entity or detection source.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdvancedSearchPage;
