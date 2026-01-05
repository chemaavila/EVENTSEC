import { useCallback, useEffect, useState } from "react";
import otAdapter from "../../services/ot";
import type { OtSensor } from "../../types/ot";
import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import OtDrawer from "../../components/ot/OtDrawer";
import CapabilityBadges from "../../components/ot/CapabilityBadges";
import TableSkeleton from "../../components/ot/TableSkeleton";
import { formatRelativeTime, sensorStatusClass } from "../../lib/otFormat";

const SensorsPage = () => {
  const [sensors, setSensors] = useState<OtSensor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSensor, setSelectedSensor] = useState<OtSensor | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [activeTab, setActiveTab] = useState<"connect" | "instructions">("connect");

  const loadSensors = useCallback(async () => {
    try {
      setLoading(true);
      const data = await otAdapter.listOtSensors();
      setSensors(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load sensors.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSensors().catch((err) => console.error(err));
  }, [loadSensors]);

  const statusLabel = (status: OtSensor["status"]) =>
    status === "online" ? "Online" : status === "degraded" ? "Degraded" : "Offline";

  return (
    <div className="ot-root">
      <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">Sensors</div>
          <div className="page-subtitle">OT sensors (Zeek + ICSNPP/ACID) and ingestion health.</div>
        </div>
        <div className="stack-horizontal">
          <button type="button" className="btn" onClick={() => setShowModal(true)}>
            Add Sensor
          </button>
        </div>
      </div>

      {loading ? (
        <div className="card">
          <TableSkeleton rows={5} columns={5} />
        </div>
      ) : error ? (
        <ErrorState
          message="Failed to load sensors. Please check ingestion health and try again."
          details={error}
          onRetry={loadSensors}
        />
      ) : sensors.length === 0 ? (
        <EmptyState
          title="No sensors registered"
          message="Add a new sensor to start monitoring your OT environment."
          action={
            <button type="button" className="btn" onClick={() => setShowModal(true)}>
              Add Sensor
            </button>
          }
        />
      ) : (
        <div className="card table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Site / Zone</th>
                <th>Status</th>
                <th>Last seen</th>
                <th>Capabilities</th>
              </tr>
            </thead>
            <tbody>
              {sensors.map((sensor) => (
                <tr
                  key={sensor.id}
                  className="table-row-clickable"
                  onClick={() => setSelectedSensor(sensor)}
                >
                  <td>{sensor.name}</td>
                  <td>
                    <div className="stack-horizontal">
                      <span className="tag">Site: {sensor.site}</span>
                      <span className="tag">Zone: {sensor.zone}</span>
                    </div>
                  </td>
                  <td>
                    <span className={`status-pill ${sensorStatusClass(sensor.status)}`}>
                      {statusLabel(sensor.status)}
                    </span>
                  </td>
                  <td className="muted">{formatRelativeTime(sensor.lastSeen)}</td>
                  <td>
                    <CapabilityBadges capabilities={sensor.capabilities} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <OtDrawer
        title={selectedSensor?.name ?? "Sensor"}
        subtitle={selectedSensor ? `${selectedSensor.site} · ${selectedSensor.zone}` : undefined}
        open={Boolean(selectedSensor)}
        onClose={() => setSelectedSensor(null)}
      >
        {selectedSensor ? (
          <div className="stack-vertical">
            <div className="drawer-fields">
              <div className="drawer-field">
                <div className="drawer-field-label">Status</div>
                <div className="drawer-field-value">{statusLabel(selectedSensor.status)}</div>
              </div>
              <div className="drawer-field">
                <div className="drawer-field-label">Last seen</div>
                <div className="drawer-field-value">{formatRelativeTime(selectedSensor.lastSeen)}</div>
              </div>
              <div className="drawer-field">
                <div className="drawer-field-label">Version</div>
                <div className="drawer-field-value">{selectedSensor.version}</div>
              </div>
              <div className="drawer-field">
                <div className="drawer-field-label">Ingest method</div>
                <div className="drawer-field-value">{selectedSensor.ingest.method.toUpperCase()}</div>
              </div>
              {selectedSensor.ingest.endpoint ? (
                <div className="drawer-field">
                  <div className="drawer-field-label">Endpoint</div>
                  <div className="drawer-field-value">{selectedSensor.ingest.endpoint}</div>
                </div>
              ) : null}
            </div>
            <div className="card">
              <div className="card-title">Capabilities</div>
              <CapabilityBadges capabilities={selectedSensor.capabilities} />
            </div>
            <div className="card">
              <div className="card-title">Coverage hints</div>
              <div className="muted">Monitors network segment 192.168.10.0/24</div>
            </div>
          </div>
        ) : null}
      </OtDrawer>

      {showModal ? (
        <div className="modal-backdrop" role="presentation" onClick={() => setShowModal(false)}>
          <div className="modal-content" role="dialog" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <div>
                <div className="modal-title">Add New Sensor</div>
                <div className="modal-subtitle">Register or deploy a new OT sensor.</div>
              </div>
              <button type="button" className="modal-close-btn" onClick={() => setShowModal(false)}>
                ×
              </button>
            </div>
            <div className="modal-body">
              <div className="tabs">
                <button
                  type="button"
                  className={`tab ${activeTab === "connect" ? "tab-active" : ""}`}
                  onClick={() => setActiveTab("connect")}
                >
                  Connect
                </button>
                <button
                  type="button"
                  className={`tab ${activeTab === "instructions" ? "tab-active" : ""}`}
                  onClick={() => setActiveTab("instructions")}
                >
                  Instructions
                </button>
              </div>

              {activeTab === "connect" ? (
                <div className="field-grid">
                  <div className="field">
                    <label className="field-label" htmlFor="sensor-name">Name</label>
                    <input id="sensor-name" type="text" placeholder="Sensor-OT-09" />
                  </div>
                  <div className="field">
                    <label className="field-label" htmlFor="sensor-site">Site</label>
                    <input id="sensor-site" type="text" placeholder="HQ" />
                  </div>
                  <div className="field">
                    <label className="field-label" htmlFor="sensor-zone">Zone</label>
                    <input id="sensor-zone" type="text" placeholder="Level 2" />
                  </div>
                  <div className="field">
                    <label className="field-label" htmlFor="sensor-key">API Key</label>
                    <input id="sensor-key" type="text" placeholder="••••••••" />
                  </div>
                  <button type="button" className="btn" disabled>
                    Register Sensor
                  </button>
                </div>
              ) : (
                <div className="card">
                  <div className="card-title">Deployment steps</div>
                  <ol className="ot-ordered-list">
                    <li>Configure SPAN/TAP on network switch.</li>
                    <li>Deploy sensor software on a dedicated monitoring host.</li>
                    <li>Validate heartbeat appears in Sensors page.</li>
                    <li>Confirm assets appear in Assets page.</li>
                  </ol>
                  <p className="muted">
                    Installation method depends on deployment environment and sensor package.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      ) : null}
      </div>
    </div>
  );
};

export default SensorsPage;
