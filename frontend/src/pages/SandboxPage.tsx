import { useEffect, useMemo, useRef, useState } from "react";
import {
  analyzeSandbox,
  listEndpoints,
  listSandboxAnalyses,
  listYaraRules,
  type Endpoint,
  type SandboxAnalysisPayload,
  type SandboxAnalysisResult,
  type YaraRule,
} from "../services/api";

type Mode = "file" | "url";

const SandboxPage = () => {
  const [mode, setMode] = useState<Mode>("file");
  const [file, setFile] = useState<File | null>(null);
  const [url, setUrl] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [currentResult, setCurrentResult] = useState<SandboxAnalysisResult | null>(null);
  const [history, setHistory] = useState<SandboxAnalysisResult[]>([]);
  const [endpoints, setEndpoints] = useState<Endpoint[]>([]);
  const [yaraRules, setYaraRules] = useState<YaraRule[]>([]);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const loadData = async () => {
    const [analyses, eps, rules] = await Promise.all([
      listSandboxAnalyses(),
      listEndpoints(),
      listYaraRules(),
    ]);
    setHistory(analyses);
    setEndpoints(eps);
    setYaraRules(rules);
    if (analyses.length > 0) {
      setCurrentResult(analyses[0]);
    }
  };

  useEffect(() => {
    loadData().catch((err) => console.error(err));
  }, []);

  const computeFileHash = async (blob: Blob) => {
    const buffer = await blob.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest("SHA-256", buffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
  };

  const handleFileChange = (selectedFile: File | null) => {
    setFile(selectedFile);
  };

  const handleAnalyze = async () => {
    try {
      setSubmitting(true);
      let payload: SandboxAnalysisPayload;
      if (mode === "file") {
        if (!file) throw new Error("Please select a file.");
        const hash = await computeFileHash(file);
        payload = {
          type: "file",
          value: hash,
          filename: file.name,
          metadata: {
            hash,
            size: file.size,
            filename: file.name,
          },
        };
      } else {
        if (!url.trim()) throw new Error("Please enter a URL.");
        payload = {
          type: "url",
          value: url.trim(),
          metadata: { url: url.trim() },
        };
      }

      const result = await analyzeSandbox(payload);
      setCurrentResult(result);
      await loadData();
      setFile(null);
      setUrl("");
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (err) {
      alert(`Failed to analyze: ${err instanceof Error ? err.message : "Unexpected error"}`);
    } finally {
      setSubmitting(false);
    }
  };

  const selectedEndpointDetails = useMemo(() => {
    if (!currentResult) return [];
    return currentResult.endpoints
      .map((match) => {
        const endpoint = endpoints.find((e) => e.id === match.id);
        return endpoint
          ? {
              ...match,
              owner: endpoint.owner,
              location: match.location,
            }
          : null;
      })
      .filter((item): item is NonNullable<typeof item> => Boolean(item));
  }, [currentResult, endpoints]);

  return (
    <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">Threat Analysis Sandbox</div>
          <div className="page-subtitle">
            Submit a file or URL to analyze with VirusTotal, OSINT, and curated YARA rules.
          </div>
        </div>
        <div className="stack-horizontal">
          <button type="button" className="btn btn-ghost" onClick={loadData}>
            Refresh data
          </button>
        </div>
      </div>

      <div className="card">
        <div className="tabs">
          <button
            type="button"
            className={`tab ${mode === "file" ? "tab-active" : ""}`}
            onClick={() => setMode("file")}
          >
            Upload file
          </button>
          <button
            type="button"
            className={`tab ${mode === "url" ? "tab-active" : ""}`}
            onClick={() => setMode("url")}
          >
            Analyze URL
          </button>
        </div>

        {mode === "file" ? (
          <div className="sandbox-dropzone" onClick={() => fileInputRef.current?.click()}>
            <div className="sandbox-dropzone-icon">⬆️</div>
            <div className="sandbox-dropzone-title">Drag & drop a file to analyze</div>
            <div className="sandbox-dropzone-subtitle">
              Maximum file size: 100 MB — {file ? file.name : "Or select a file"}
            </div>
            <input
              type="file"
              ref={fileInputRef}
              style={{ display: "none" }}
              onChange={(e) => handleFileChange(e.target.files?.[0] ?? null)}
            />
            <button
              type="button"
              className="btn btn-sm"
              style={{ marginTop: "1rem" }}
              onClick={handleAnalyze}
              disabled={submitting}
            >
              {submitting ? "Analyzing…" : "Analyze file"}
            </button>
          </div>
        ) : (
          <div className="stack-vertical">
            <div className="field-group">
              <label htmlFor="sandbox-url" className="field-label">
                URL to analyze
              </label>
              <input
                id="sandbox-url"
                className="field-control"
                placeholder="https://example.com/suspicious"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />
            </div>
            <div style={{ textAlign: "right" }}>
              <button type="button" className="btn btn-sm" onClick={handleAnalyze} disabled={submitting}>
                {submitting ? "Analyzing…" : "Analyze URL"}
              </button>
            </div>
          </div>
        )}
      </div>

      {currentResult && (
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">
                Analysis complete — {currentResult.filename || currentResult.value}
              </div>
              <div className="card-subtitle">
                Verdict generated at {new Date(currentResult.created_at).toLocaleString()}
              </div>
            </div>
            <button type="button" className="btn btn-ghost btn-sm">
              Download report
            </button>
          </div>

          <div className="grid-4">
            <div className="card sandbox-mini">
              <div className="field-label">Verdict</div>
              <div className={`sandbox-verdict ${currentResult.verdict}`}>
                {currentResult.verdict.toUpperCase()}
              </div>
            </div>
            <div className="card sandbox-mini">
              <div className="field-label">Threat type</div>
              <div>{currentResult.threat_type || "N/A"}</div>
            </div>
            <div className="card sandbox-mini">
              <div className="field-label">File hash (SHA-256)</div>
              <div className="muted">{currentResult.file_hash}</div>
            </div>
            <div className="card sandbox-mini">
              <div className="field-label">Status</div>
              <div>{currentResult.status}</div>
            </div>
          </div>

          <div className="grid-2" style={{ marginTop: "1rem" }}>
            <div className="stack-vertical">
              <div className="field-label">Indicators of Compromise (IOCs)</div>
              <div className="table-responsive">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Type</th>
                      <th>Value</th>
                      <th>Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    {currentResult.iocs.map((ioc) => (
                      <tr key={`${ioc.type}-${ioc.value}`}>
                        <td>{ioc.type}</td>
                        <td>{ioc.value}</td>
                        <td>{ioc.description}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            {currentResult.yara_matches.length > 0 && (
              <div className="stack-vertical">
                <div className="field-label">YARA matches</div>
                <div className="table-responsive">
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Rule</th>
                        <th>Source</th>
                      </tr>
                    </thead>
                    <tbody>
                      {currentResult.yara_matches.map((match) => (
                        <tr key={match.rule_id}>
                          <td>
                            <div className="table-ellipsis">{match.rule_name}</div>
                            <div className="muted small">{match.tags.join(", ")}</div>
                          </td>
                          <td>{match.source}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>

          {selectedEndpointDetails.length > 0 && (
            <div className="stack-vertical" style={{ marginTop: "1rem" }}>
              <div className="field-label">Endpoints impacted</div>
              <div className="grid-2">
                {selectedEndpointDetails.map((endpoint) => (
                  <div key={endpoint.id} className="card sandbox-mini">
                    <div className="card-title">{endpoint.hostname}</div>
                    <div className="muted">
                      Status: {endpoint.status} • IP: {endpoint.ip_address}
                    </div>
                    <div className="muted">
                      Owner: {endpoint.owner} • Last seen:{" "}
                      {new Date(endpoint.last_seen).toLocaleTimeString()}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">Recent analyses</div>
            <div className="card-subtitle">Historical sandbox executions.</div>
          </div>
        </div>
        {history.length === 0 ? (
          <div className="muted">No analyses yet.</div>
        ) : (
          <div className="table-responsive">
            <table className="table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Artifact</th>
                  <th>Verdict</th>
                  <th>Threat</th>
                </tr>
              </thead>
              <tbody>
                {history.map((item) => (
                  <tr
                    key={item.id}
                    onClick={() => setCurrentResult(item)}
                    className={currentResult?.id === item.id ? "table-row-active" : ""}
                  >
                    <td>{new Date(item.created_at).toLocaleString()}</td>
                    <td>{item.filename || item.value}</td>
                    <td>{item.verdict}</td>
                    <td>{item.threat_type || "N/A"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">Available YARA rules</div>
            <div className="card-subtitle">
              Reference extracted from Yara-Rules and InQuest awesome-yara for offline testing.
            </div>
          </div>
        </div>
        {yaraRules.length === 0 ? (
          <div className="muted">No YARA rules loaded.</div>
        ) : (
          <div className="table-responsive">
            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Source</th>
                  <th>Tags</th>
                </tr>
              </thead>
              <tbody>
                {yaraRules.map((rule) => (
                  <tr key={rule.rule_id}>
                    <td>{rule.rule_name}</td>
                    <td>{rule.source}</td>
                    <td>
                      {rule.tags.map((tag) => (
                        <span key={tag} className="tag">
                          {tag}
                        </span>
                      ))}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default SandboxPage;


