import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import otAdapter from "../../services/ot";
import type { OtOverviewResponse } from "../../services/ot";
import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import TableSkeleton from "../../components/ot/TableSkeleton";
import { formatRelativeTime, severityClass } from "../../lib/otFormat";
import type { OtSeverity } from "../../types/ot";

const OverviewPage = () => {
  const navigate = useNavigate();
  const [overview, setOverview] = useState<OtOverviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadOverview = useCallback(async () => {
    try {
      setLoading(true);
      const data = await otAdapter.getOtOverview();
      setOverview(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load OT overview.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadOverview().catch((err) => console.error(err));
  }, [loadOverview]);

  const kpis = useMemo(() => {
    if (!overview) return [];
    return [
      {
        id: "sensors",
        icon: "📡",
        label: "Sensors Online",
        value: `${overview.kpis.sensorsOnline} / ${overview.kpis.sensorsTotal}`,
        meta: overview.kpis.sensorsTotal > overview.kpis.sensorsOnline ? "Check degraded sensors" : "All healthy",
      },
      {
        id: "assets",
        icon: "🧭",
        label: "Assets Discovered",
        value: `${overview.kpis.assets24h}`,
        meta: `+${overview.kpis.assets24h} (24h) / +${overview.kpis.assets7d} (7d)`,
      },
      {
        id: "detections",
        icon: "🚨",
        label: "Open Detections",
        value: Object.values(overview.kpis.openDetectionsBySeverity).reduce((sum, value) => sum + value, 0).toString(),
        meta: "By severity",
      },
      {
        id: "comms",
        icon: "🔁",
        label: "New IT → OT Comms (24h)",
        value: `${overview.kpis.newItToOt24h}`,
        meta: "Review new paths",
      },
    ];
  }, [overview]);

  const hasData = (overview?.topDetections.length ?? 0) > 0;

  return (
    <div className="ot-root">
      <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">OT Security</div>
          <div className="page-subtitle">
            Passive visibility from OT sensors and PCAP analysis.
          </div>
        </div>
        <div className="stack-horizontal">
          <button type="button" className="btn" onClick={() => navigate("/ot/pcap")}>
            Upload PCAP
          </button>
          <button type="button" className="btn btn-ghost" onClick={() => navigate("/ot/sensors")}>
            Sensors
          </button>
        </div>
      </div>

      {loading ? (
        <>
          <div className="grid-4">
            {Array.from({ length: 4 }).map((_, idx) => (
              <div key={idx} className="card ot-kpi-card">
                <div className="loading-skeleton-line" />
                <div className="loading-skeleton-line" />
                <div className="loading-skeleton-line" />
              </div>
            ))}
          </div>
          <div className="ot-main-grid">
            <div className="card">
              <TableSkeleton rows={6} columns={7} />
            </div>
            <div className="stack-vertical">
              <div className="card">
                <div className="loading-skeleton-line" />
                <div className="loading-skeleton-line" />
                <div className="loading-skeleton-line" />
              </div>
              <div className="card">
                <div className="loading-skeleton-line" />
                <div className="loading-skeleton-line" />
                <div className="loading-skeleton-line" />
              </div>
            </div>
          </div>
        </>
      ) : error ? (
        <ErrorState
          title="Failed to load OT overview"
          message="Failed to load OT overview. Please check sensor connectivity and try again."
          details={error}
          onRetry={loadOverview}
        />
      ) : !hasData ? (
        <EmptyState
          title="No OT data yet"
          message="Connect an OT sensor (SPAN/TAP) or upload a PCAP."
          action={
            <div className="stack-horizontal">
              <button type="button" className="btn" onClick={() => navigate("/ot/pcap")}>
                Upload PCAP
              </button>
              <button type="button" className="btn btn-ghost" onClick={() => navigate("/ot/sensors")}>
                Go to Sensors
              </button>
            </div>
          }
        />
      ) : (
        <>
          <div className="grid-4">
            {kpis.map((kpi) => (
              <div key={kpi.id} className="card ot-kpi-card">
                <div className="ot-kpi-icon" aria-hidden="true">
                  {kpi.icon}
                </div>
                <div className="ot-kpi-value">{kpi.value}</div>
                <div className="ot-kpi-label">{kpi.label}</div>
                <div className="ot-kpi-meta">{kpi.meta}</div>
                {kpi.id === "detections" && overview ? (
                  <div className="ot-kpi-stack">
                    {Object.entries(overview.kpis.openDetectionsBySeverity).map(([severity, count]) => (
                      <span key={severity} className={`severity-pill ${severityClass(severity as OtSeverity)}`}>
                        {severity}: {count}
                      </span>
                    ))}
                  </div>
                ) : null}
              </div>
            ))}
          </div>

          <div className="ot-main-grid">
            <div className="card">
              <div className="card-header">
                <div>
                  <div className="card-title">Top Detections</div>
                  <div className="card-subtitle">Most impactful OT detections today.</div>
                </div>
              </div>
              <div className="table-wrap">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Severity</th>
                      <th>Title</th>
                      <th>Technique</th>
                      <th>Assets</th>
                      <th>Sensor</th>
                      <th>Time</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {overview?.topDetections.map((det) => (
                      <tr
                        key={det.id}
                        className="table-row-clickable"
                        onClick={() => navigate(`/ot/detections?detectionId=${det.id}`)}
                      >
                        <td>
                          <span className={`severity-pill ${severityClass(det.severity)}`}>
                            {det.severity}
                          </span>
                        </td>
                        <td>{det.title}</td>
                        <td>
                          <span className="ot-chip">
                            {det.technique?.techniqueId ?? "—"}
                          </span>
                        </td>
                        <td className="muted">{det.assetIds.length}</td>
                        <td className="muted">{det.sensorId}</td>
                        <td className="muted">{formatRelativeTime(det.ts)}</td>
                        <td>
                          <span className="badge">{det.status}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="stack-vertical">
              <div className="card">
                <div className="card-header">
                  <div>
                    <div className="card-title">Recent Changes</div>
                    <div className="card-subtitle">Latest assets, protocols, and new paths.</div>
                  </div>
                </div>
                <ul className="ot-activity-list">
                  {overview?.recentChanges.map((change) => (
                    <li key={change.id} className="ot-activity-item">
                      <div>
                        <div className="ot-activity-summary">{change.message}</div>
                        <div className="ot-activity-meta">{formatRelativeTime(change.ts)}</div>
                      </div>
                      <div className="ot-activity-chips">
                        {change.site ? <span className="tag">Site: {change.site}</span> : null}
                        {change.zone ? <span className="tag">Zone: {change.zone}</span> : null}
                      </div>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="card">
                <div className="card-header">
                  <div>
                    <div className="card-title">Top Protocols</div>
                    <div className="card-subtitle">Observed in the last 7 days.</div>
                  </div>
                </div>
                <div className="stack-vertical">
                  {overview?.topProtocols7d?.map((protocol) => (
                    <div key={protocol.protocol} className="ot-protocol-row">
                      <span>{protocol.protocol}</span>
                      <span className="muted">{protocol.count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </>
      )}
      </div>
    </div>
  );
};

export default OverviewPage;
