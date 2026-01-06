import { useEffect, useState } from "react";
import { fetchGlobalVulns } from "../api/vulnerabilities";
import RiskChip from "../components/common/RiskChip";
import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";
import type { GlobalVulnerabilityRecord } from "../types/vuln";

const VulnerabilitiesPage = () => {
  const [records, setRecords] = useState<GlobalVulnerabilityRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    search: "",
    min_risk: "",
    kev: false,
    epss_min: "",
  });

  const load = async () => {
    try {
      setLoading(true);
      const data = await fetchGlobalVulns({
        min_risk: filters.min_risk || undefined,
        kev: filters.kev || undefined,
        epss_min: filters.epss_min ? Number(filters.epss_min) : undefined,
        software_name: filters.search || undefined,
      });
      setRecords(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load vulnerabilities");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load().catch((err) => console.error(err));
  }, [filters]);

  if (loading) {
    return <LoadingState message="Loading vulnerabilities…" />;
  }

  if (error) {
    return <ErrorState message={error} />;
  }

  return (
    <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <h1 className="page-title">Vulnerabilities</h1>
          <p className="page-subtitle">Global findings across all assets.</p>
        </div>
      </div>
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">Findings</div>
            <div className="card-subtitle">{records.length} findings</div>
          </div>
          <div className="filters-row">
            <input
              placeholder="Search software"
              value={filters.search}
              onChange={(event) =>
                setFilters((prev) => ({ ...prev, search: event.target.value }))
              }
            />
            <select
              value={filters.min_risk}
              onChange={(event) =>
                setFilters((prev) => ({ ...prev, min_risk: event.target.value }))
              }
            >
              <option value="">Min risk</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
            <input
              type="number"
              step="0.01"
              min="0"
              max="1"
              placeholder="EPSS ≥"
              value={filters.epss_min}
              onChange={(event) =>
                setFilters((prev) => ({ ...prev, epss_min: event.target.value }))
              }
            />
            <label className="checkbox">
              <input
                type="checkbox"
                checked={filters.kev}
                onChange={(event) =>
                  setFilters((prev) => ({ ...prev, kev: event.target.checked }))
                }
              />
              KEV only
            </label>
          </div>
        </div>
        <div className="table-responsive">
          <table className="table">
            <thead>
              <tr>
                <th>Asset</th>
                <th>Risk</th>
                <th>CVE/OSV</th>
                <th>Software</th>
                <th>Version</th>
                <th>CVSS</th>
                <th>EPSS</th>
                <th>KEV</th>
              </tr>
            </thead>
            <tbody>
              {records.map((record) => (
                <tr key={record.finding.id}>
                  <td>{record.asset_name ?? record.asset_id}</td>
                  <td>
                    <RiskChip label={record.finding.risk_label} />
                  </td>
                  <td>
                    {record.finding.vulnerability?.cve_id ??
                      record.finding.vulnerability?.osv_id}
                  </td>
                  <td>{record.finding.software_component?.name ?? "—"}</td>
                  <td>{record.finding.software_component?.version ?? "—"}</td>
                  <td>{record.finding.vulnerability?.cvss_score ?? "—"}</td>
                  <td>
                    {record.finding.vulnerability?.epss_score !== undefined
                      ? record.finding.vulnerability?.epss_score?.toFixed(2)
                      : "—"}
                  </td>
                  <td>{record.finding.vulnerability?.kev ? "Yes" : "No"}</td>
                </tr>
              ))}
              {records.length === 0 && (
                <tr>
                  <td colSpan={8}>No vulnerability findings yet.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default VulnerabilitiesPage;
