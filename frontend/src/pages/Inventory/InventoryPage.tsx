import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchAssetsWithRisk } from "../../api/inventory";
import RiskChip from "../../components/common/RiskChip";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import type { AssetInventorySummary } from "../../types/inventory";

const InventoryPage = () => {
  const [assets, setAssets] = useState<AssetInventorySummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadAssets = async () => {
    try {
      setLoading(true);
      const data = await fetchAssetsWithRisk();
      setAssets(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load assets");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAssets().catch((err) => console.error(err));
  }, []);

  if (loading) {
    return <LoadingState message="Loading inventory assets…" />;
  }

  if (error) {
    return <ErrorState message={error} />;
  }

  return (
    <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <h1 className="page-title">Inventory</h1>
          <p className="page-subtitle">Software inventory risk overview per asset.</p>
        </div>
      </div>
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">Assets</div>
            <div className="card-subtitle">{assets.length} tracked assets</div>
          </div>
        </div>
        <div className="table-responsive">
          <table className="table">
            <thead>
              <tr>
                <th>Asset</th>
                <th>IP</th>
                <th>Last seen</th>
                <th>Risk</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {assets.map((item) => (
                <tr key={item.asset.id}>
                  <td>{item.asset.name}</td>
                  <td>{item.asset.ip_address}</td>
                  <td>
                    {item.asset.last_seen
                      ? new Date(item.asset.last_seen).toLocaleString()
                      : "—"}
                  </td>
                  <td>
                    <RiskChip
                      label={item.risk.top_risk_label ?? "LOW"}
                      counts={{
                        CRITICAL: item.risk.critical_count,
                        HIGH: item.risk.high_count,
                        MEDIUM: item.risk.medium_count,
                        LOW: item.risk.low_count,
                      }}
                    />
                  </td>
                  <td>
                    <Link className="link" to={`/inventory/assets/${item.asset.id}`}>
                      View
                    </Link>
                  </td>
                </tr>
              ))}
              {assets.length === 0 && (
                <tr>
                  <td colSpan={5}>No software inventory data yet.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default InventoryPage;
