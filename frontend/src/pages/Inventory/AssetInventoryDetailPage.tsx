import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { fetchAssetDetail } from "../../api/inventory";
import { fetchAssetVulns, updateFindingStatus } from "../../api/vulnerabilities";
import RiskChip from "../../components/common/RiskChip";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import type { InventoryAssetDetail } from "../../types/inventory";
import type { AssetVulnerability } from "../../types/vuln";

type TabKey = "software" | "vulnerabilities";

const AssetInventoryDetailPage = () => {
  const { assetId } = useParams();
  const resolvedAssetId = Number(assetId);
  const [assetDetail, setAssetDetail] = useState<InventoryAssetDetail | null>(null);
  const [findings, setFindings] = useState<AssetVulnerability[]>([]);
  const [tab, setTab] = useState<TabKey>("software");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    min_risk: "",
    kev: false,
    status: "",
  });

  const loadDetail = async () => {
    try {
      setLoading(true);
      const detail = await fetchAssetDetail(resolvedAssetId);
      setAssetDetail(detail);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load asset detail");
    } finally {
      setLoading(false);
    }
  };

  const loadFindings = async () => {
    if (!resolvedAssetId) {
      return;
    }
    const response = await fetchAssetVulns(resolvedAssetId, {
      status: filters.status || undefined,
      min_risk: filters.min_risk || undefined,
      kev: filters.kev || undefined,
    });
    setFindings(response.items);
  };

  useEffect(() => {
    if (!Number.isFinite(resolvedAssetId)) {
      return;
    }
    loadDetail().catch((err) => console.error(err));
  }, [resolvedAssetId]);

  useEffect(() => {
    loadFindings().catch((err) => console.error(err));
  }, [resolvedAssetId, filters]);

  useEffect(() => {
    if (findings.length > 0) {
      setTab("vulnerabilities");
    }
  }, [findings.length]);

  const riskSummary = assetDetail?.risk;
  const riskCounts = useMemo(
    () =>
      riskSummary
        ? {
            CRITICAL: riskSummary.critical_count,
            HIGH: riskSummary.high_count,
            MEDIUM: riskSummary.medium_count,
            LOW: riskSummary.low_count,
          }
        : undefined,
    [riskSummary]
  );

  const handleStatusChange = async (findingId: number, status: string) => {
    await updateFindingStatus(resolvedAssetId, findingId, status);
    loadFindings().catch((err) => console.error(err));
  };

  if (loading) {
    return <LoadingState message="Loading asset inventory…" />;
  }

  if (error || !assetDetail) {
    return <ErrorState message={error ?? "Asset not found"} />;
  }

  return (
    <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <h1 className="page-title">{assetDetail.asset.name}</h1>
          <p className="page-subtitle">{assetDetail.asset.ip_address}</p>
        </div>
        {riskSummary && (
          <RiskChip label={riskSummary.top_risk_label ?? "LOW"} counts={riskCounts} />
        )}
      </div>

      {riskSummary && (
        <div className="pill">
          🔥 Critical: {riskSummary.critical_count} | High: {riskSummary.high_count} |
          Medium: {riskSummary.medium_count} | Low: {riskSummary.low_count}
        </div>
      )}

      <div className="tabs">
        <button
          className={`tab ${tab === "software" ? "tab-active" : ""}`}
          onClick={() => setTab("software")}
        >
          Software
        </button>
        <button
          className={`tab ${tab === "vulnerabilities" ? "tab-active" : ""}`}
          onClick={() => setTab("vulnerabilities")}
        >
          Vulnerabilities
        </button>
      </div>

      {tab === "software" && (
        <div className="card">
          <div className="card-header">
            <div className="card-title">Software components</div>
            <div className="card-subtitle">
              {assetDetail.software.length} components detected
            </div>
          </div>
          <div className="table-responsive">
            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Version</th>
                  <th>Vendor</th>
                  <th>Last seen</th>
                </tr>
              </thead>
              <tbody>
                {assetDetail.software.map((component) => (
                  <tr key={component.id}>
                    <td>{component.name}</td>
                    <td>{component.version}</td>
                    <td>{component.vendor ?? "—"}</td>
                    <td>{new Date(component.last_seen_at).toLocaleString()}</td>
                  </tr>
                ))}
                {assetDetail.software.length === 0 && (
                  <tr>
                    <td colSpan={4}>No software components detected.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === "vulnerabilities" && (
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Vulnerabilities</div>
              <div className="card-subtitle">{findings.length} findings</div>
            </div>
            <div className="filters-row">
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
              <select
                value={filters.status}
                onChange={(event) =>
                  setFilters((prev) => ({ ...prev, status: event.target.value }))
                }
              >
                <option value="">Status</option>
                <option value="open">Open</option>
                <option value="mitigated">Mitigated</option>
                <option value="accepted">Accepted</option>
                <option value="false_positive">False positive</option>
              </select>
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
                  <th>Risk</th>
                  <th>CVE/OSV</th>
                  <th>Software</th>
                  <th>Version</th>
                  <th>CVSS</th>
                  <th>EPSS</th>
                  <th>KEV</th>
                  <th>First seen</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {findings.map((finding) => (
                  <tr key={finding.id}>
                    <td>
                      <RiskChip label={finding.risk_label} />
                    </td>
                    <td>{finding.vulnerability?.cve_id ?? finding.vulnerability?.osv_id}</td>
                    <td>{finding.software_component?.name ?? "—"}</td>
                    <td>{finding.software_component?.version ?? "—"}</td>
                    <td>{finding.vulnerability?.cvss_score ?? "—"}</td>
                    <td>
                      {finding.vulnerability?.epss_score !== undefined
                        ? finding.vulnerability?.epss_score?.toFixed(2)
                        : "—"}
                    </td>
                    <td>{finding.vulnerability?.kev ? "Yes" : "No"}</td>
                    <td>{new Date(finding.first_seen_at).toLocaleDateString()}</td>
                    <td>
                      <select
                        value={finding.status}
                        onChange={(event) =>
                          handleStatusChange(finding.id, event.target.value)
                        }
                      >
                        <option value="open">Open</option>
                        <option value="mitigated">Mitigated</option>
                        <option value="accepted">Accepted</option>
                        <option value="false_positive">False positive</option>
                      </select>
                    </td>
                  </tr>
                ))}
                {findings.length === 0 && (
                  <tr>
                    <td colSpan={9}>No vulnerabilities found for this asset.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default AssetInventoryDetailPage;
