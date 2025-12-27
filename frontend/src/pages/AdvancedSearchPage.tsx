import type { KeyboardEvent } from "react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { runKqlQuery } from "../services/api";

type SampleQuery = {
  label: string;
  description: string;
  query: string;
};

const SAMPLE_QUERIES: SampleQuery[] = [
  {
    label: "Critical heartbeats",
    description: "Agent heartbeats with severity=critical in the last hour",
    query: `SecurityEvent
| where severity == "critical" and category == "AgentHeartbeat"
| limit 100`,
  },
  {
    label: "Suspicious logon",
    description: "Failed logons that mention remote access keywords",
    query: `SecurityEvent
| where message contains "logon failure" and message contains "remote"
| limit 75`,
  },
  {
    label: "Network phishing",
    description: "Network events that include phishing verdicts",
    query: `SecurityEvent
| where event_type == "network" and details.url contains "login"
| limit 50`,
  },
];

type QueryStatus = "idle" | "running";

const AdvancedSearchPage = () => {
  const [queryText, setQueryText] = useState(SAMPLE_QUERIES[0].query);
  const [limit, setLimit] = useState(200);
  const [status, setStatus] = useState<QueryStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [rows, setRows] = useState<Array<Record<string, unknown>>>([]);
  const [history, setHistory] = useState<string[]>([]);
  const [selectedRow, setSelectedRow] = useState<Record<string, unknown> | null>(null);
  const [meta, setMeta] = useState({ took: 0, total: 0, index: "events-v1" });
  const [projectedFields, setProjectedFields] = useState<string[]>([]);
  const [lastRunAt, setLastRunAt] = useState<string | null>(null);
  const initialLoadRef = useRef(false);

  const runQuery = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed) {
        setError("Query cannot be empty.");
        return;
      }

      setStatus("running");
      setError(null);
      try {
        const response = await runKqlQuery({ query: trimmed, limit });
        setRows(response.hits);
        setMeta({ took: response.took_ms, total: response.total, index: response.index });
        setProjectedFields(response.fields ?? []);
        setSelectedRow(response.hits[0] ?? null);
        setLastRunAt(new Date().toLocaleTimeString());
        setHistory((prev) => [trimmed, ...prev.filter((entry) => entry !== trimmed)].slice(0, 6));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unable to run KQL query");
      } finally {
        setStatus("idle");
      }
    },
    [limit]
  );

  useEffect(() => {
    if (!initialLoadRef.current) {
      initialLoadRef.current = true;
      runQuery(SAMPLE_QUERIES[0].query).catch((err) => console.error(err));
    }
  }, [runQuery]);

  const displayedRows = useMemo(() => rows.slice(0, 200), [rows]);

  const columns = useMemo(() => {
    const defaults = ["timestamp", "severity", "category", "message"];
    const set = new Set(defaults);
    rows.forEach((row) => {
      Object.keys(row || {}).forEach((key) => set.add(key));
    });
    return Array.from(set);
  }, [rows]);

  const timelineBuckets = useMemo(() => {
    const counts = new Map<string, number>();
    rows.forEach((row) => {
      const rawTs =
        row.timestamp || row["@timestamp"] || row.time || row.event_time || row.last_seen;
      if (!rawTs) {
        return;
      }
      const date = new Date(String(rawTs));
      if (Number.isNaN(date.getTime())) {
        return;
      }
      const bucket = `${date.toISOString().slice(0, 13)}:00`;
      counts.set(bucket, (counts.get(bucket) ?? 0) + 1);
    });
    return Array.from(counts.entries())
      .sort((a, b) => (a[0] > b[0] ? 1 : -1))
      .slice(-12);
  }, [rows]);

  const handleTextareaKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
      event.preventDefault();
      runQuery(queryText).catch((err) => console.error(err));
    }
  };

  const renderCellValue = (value: unknown) => {
    if (value === null || value === undefined) return "—";
    if (typeof value === "object") return JSON.stringify(value);
    const asString = String(value);
    return asString.length > 140 ? `${asString.slice(0, 137)}…` : asString;
  };

  return (
    <div className="kql-shell">
      <div className="kql-header">
        <div>
          <div className="kql-title">KQL workbench</div>
          <div className="kql-subtitle">
            Sentinel-inspired hunting window powered by OpenSearch and Kusto Query Language.
          </div>
        </div>
        <div className="kql-metrics">
          <div className="kql-metric">
            <span>Records returned</span>
            <strong>{meta.total.toLocaleString()}</strong>
          </div>
          <div className="kql-metric">
            <span>Query time</span>
            <strong>{meta.took} ms</strong>
          </div>
          <div className="kql-metric">
            <span>Result window</span>
            <strong>{Math.min(limit, displayedRows.length)}</strong>
          </div>
        </div>
      </div>

      <div className="kql-body">
        <section className="kql-editor-card">
          <div className="kql-toolbar">
            <div className="kql-toolbar-left">
              <label className="kql-limit-field">
                Limit
                <input
                  type="number"
                  min={1}
                  max={500}
                  value={limit}
                  onChange={(event) => setLimit(Number(event.target.value) || 1)}
                />
              </label>
              <span className="kql-connection">Connected to {meta.index}</span>
            </div>
            <div className="kql-toolbar-actions">
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={() => setQueryText("")}
                disabled={status === "running"}
              >
                Clear editor
              </button>
              <button
                type="button"
                className="btn btn-sm"
                onClick={() => runQuery(queryText).catch((err) => console.error(err))}
                disabled={status === "running"}
              >
                {status === "running" ? "Running…" : "Run query"}
              </button>
            </div>
          </div>
          <textarea
            className="kql-editor-input"
            value={queryText}
            onChange={(event) => setQueryText(event.target.value)}
            onKeyDown={handleTextareaKeyDown}
            spellCheck={false}
            rows={9}
            placeholder='SecurityEvent | where severity == "high" and message contains "phish" | limit 100'
          />
          <div className="kql-status-row">
            <div className="kql-status-item">
              {error ? <span className="kql-error">{error}</span> : "Ready"}
            </div>
            <div className="kql-status-item">
              {lastRunAt ? `Last run at ${lastRunAt}` : "Press Ctrl+Enter to run"}
            </div>
            {projectedFields.length > 0 && (
              <div className="kql-status-item kql-fields">
                Projected:{" "}
                {projectedFields.map((field) => (
                  <span key={field} className="kql-field-pill">
                    {field}
                  </span>
                ))}
              </div>
            )}
          </div>
        </section>

        <aside className="kql-sidepanel">
          <div className="kql-side-section">
            <div className="kql-side-title">Saved queries</div>
            <div className="kql-side-subtitle">1-click hunting templates</div>
            <ul>
              {SAMPLE_QUERIES.map((sample) => (
                <li key={sample.label}>
                  <button
                    type="button"
                    className="kql-sample"
                    onClick={() => {
                      setQueryText(sample.query);
                      runQuery(sample.query).catch((err) => console.error(err));
                    }}
                  >
                    <div className="kql-sample-label">{sample.label}</div>
                    <div className="kql-sample-description">{sample.description}</div>
                  </button>
                </li>
              ))}
            </ul>
          </div>
          <div className="kql-side-section">
            <div className="kql-side-title">Recent history</div>
            <div className="kql-side-subtitle">Click to re-run</div>
            {history.length === 0 && <div className="muted small">No queries yet.</div>}
            <ul>
              {history.map((entry) => (
                <li key={entry}>
                  <button
                    type="button"
                    className="kql-history"
                    onClick={() => {
                      setQueryText(entry);
                      runQuery(entry).catch((err) => console.error(err));
                    }}
                  >
                    {entry.length > 120 ? `${entry.slice(0, 117)}…` : entry}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </aside>
      </div>

      <div className="kql-results-grid">
        <section className="kql-results-card">
          <div className="kql-results-header">
            <div>
              <div className="kql-results-title">Result table</div>
              <div className="kql-results-subtitle">
                Showing {displayedRows.length} / {rows.length} documents
              </div>
            </div>
            {status === "running" && <span className="muted small">Streaming…</span>}
          </div>
          <div className="kql-table-wrapper">
            <div className="kql-table">
              <div className="kql-table-head">
                {columns.map((column) => (
                  <span key={column}>{column}</span>
                ))}
              </div>
              {displayedRows.length === 0 && (
                <div className="muted small" style={{ padding: "1rem" }}>
                  {status === "running" ? "Waiting for data…" : "No rows matched this query."}
                </div>
              )}
              {displayedRows.map((row, idx) => (
                <button
                  type="button"
                  key={`${row.timestamp ?? ""}-${idx}`}
                  className={
                    "kql-table-row" +
                    (selectedRow === row ? " kql-table-row-selected" : "")
                  }
                  onClick={() => setSelectedRow(row)}
                >
                  {columns.map((column) => (
                    <span key={column}>{renderCellValue(row[column])}</span>
                  ))}
                </button>
              ))}
            </div>
          </div>
        </section>

        <section className="kql-side-results">
          <div className="kql-mini-card">
            <div className="kql-mini-card-header">
              <div>
                <div className="kql-mini-card-title">Timeline</div>
                <div className="kql-mini-card-subtitle">Per-hour distribution</div>
              </div>
            </div>
            <div className="kql-timeline">
              {timelineBuckets.length === 0 && (
                <div className="muted small">No timestamp data available.</div>
              )}
              {timelineBuckets.map(([bucket, count]) => (
                <div key={bucket} className="kql-timeline-row">
                  <span>{bucket}</span>
                  <div className="kql-timeline-bar">
                    <span
                      style={{ width: `${Math.min(100, count * 12)}%` }}
                      data-count={count}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="kql-mini-card">
            <div className="kql-mini-card-header">
              <div>
                <div className="kql-mini-card-title">Result inspector</div>
                <div className="kql-mini-card-subtitle">
                  Raw JSON for the selected document
                </div>
              </div>
            </div>
            <pre className="kql-json-viewer">
              {selectedRow ? JSON.stringify(selectedRow, null, 2) : "Select a row to inspect it."}
            </pre>
          </div>
        </section>
      </div>
    </div>
  );
};

export default AdvancedSearchPage;
