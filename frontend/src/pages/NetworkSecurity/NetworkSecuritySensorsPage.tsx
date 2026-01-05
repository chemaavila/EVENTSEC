import { useEffect, useState } from "react";
import type { NetworkSensor } from "../../services/api";
import { listNetworkSensors } from "../../services/api";
import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";

const NetworkSecuritySensorsPage = () => {
  const [sensors, setSensors] = useState<NetworkSensor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadSensors = async () => {
    try {
      setLoading(true);
      const data = await listNetworkSensors();
      setSensors(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load sensors");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSensors();
  }, []);

  return (
    <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">Network Sensors</div>
          <div className="page-subtitle">
            Health status and last seen for IDS sensors.
          </div>
        </div>
        <div className="stack-horizontal">
          <button type="button" className="btn btn-ghost" onClick={loadSensors}>
            Refresh
          </button>
        </div>
      </div>

      {loading && <LoadingState message="Loading sensors…" />}
      {error && <ErrorState message={error} />}

      {!loading && !error && (
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Sensors</div>
              <div className="card-subtitle">{sensors.length} sensors</div>
            </div>
          </div>
          {sensors.length === 0 ? (
            <EmptyState message="No sensors registered yet." />
          ) : (
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Kind</th>
                    <th>Location</th>
                    <th>Last Seen</th>
                    <th>Status</th>
                    <th>Error Count</th>
                  </tr>
                </thead>
                <tbody>
                  {sensors.map((sensor) => (
                    <tr key={sensor.id}>
                      <td>{sensor.name}</td>
                      <td>{sensor.kind}</td>
                      <td>{sensor.location ?? "—"}</td>
                      <td>
                        {sensor.last_seen_at
                          ? new Date(sensor.last_seen_at).toLocaleString()
                          : "—"}
                      </td>
                      <td>{sensor.status}</td>
                      <td>{sensor.error_count}</td>
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

export default NetworkSecuritySensorsPage;
