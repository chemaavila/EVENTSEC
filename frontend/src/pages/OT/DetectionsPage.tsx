import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import otAdapter from "../../services/ot";
import type {
  OtAsset,
  OtDetection,
  OtDetectionStatus,
  OtSeverity,
  OtSensor,
  PaginatedResponse,
} from "../../types/ot";
import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import OtDrawer from "../../components/ot/OtDrawer";
import EvidenceKeyValueList from "../../components/ot/EvidenceKeyValueList";
import TableSkeleton from "../../components/ot/TableSkeleton";
import Pagination from "../../components/ot/Pagination";
import { formatRelativeTime, severityClass, detectionStatusClass, statusLabel } from "../../lib/otFormat";
import { useDebouncedValue } from "../../lib/useDebouncedValue";

const defaultPageSize = 8;

const DetectionsPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [query, setQuery] = useState("");
  const debouncedQuery = useDebouncedValue(query, 400);
  const [status, setStatus] = useState<OtDetectionStatus | "">("");
  const [severity, setSeverity] = useState<OtSeverity | "">("");
  const [techniqueId, setTechniqueId] = useState("");
  const [timePreset, setTimePreset] = useState("24h");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<PaginatedResponse<OtDetection> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDetection, setSelectedDetection] = useState<OtDetection | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [assets, setAssets] = useState<OtAsset[]>([]);
  const [sensors, setSensors] = useState<OtSensor[]>([]);
  const [detailLoading, setDetailLoading] = useState(false);

  const detectionIdParam = searchParams.get("detectionId");
  const pcapJobIdParam = searchParams.get("pcapJobId");

  const assetsById = useMemo(() => new Map(assets.map((asset) => [asset.id, asset])), [assets]);
  const sensorsById = useMemo(() => new Map(sensors.map((sensor) => [sensor.id, sensor])), [sensors]);

  const filtersActive = useMemo(() => {
    return Boolean(
      debouncedQuery || status || severity || techniqueId || timePreset !== "24h" || pcapJobIdParam
    );
  }, [debouncedQuery, status, severity, techniqueId, timePreset, pcapJobIdParam]);

  const loadMetadata = useCallback(async () => {
    try {
      const [assetResponse, sensorsResponse] = await Promise.all([
        otAdapter.listOtAssets({ page: 1, pageSize: 200 }),
        otAdapter.listOtSensors(),
      ]);
      setAssets(assetResponse.items);
      setSensors(sensorsResponse);
    } catch (err) {
      console.error(err);
    }
  }, []);

  const loadDetections = useCallback(async () => {
    try {
      setLoading(true);
      const response = await otAdapter.listOtDetections({
        q: debouncedQuery || undefined,
        status: status || undefined,
        severity: severity || undefined,
        techniqueId: techniqueId || undefined,
        timeRange: { preset: timePreset as "24h" | "7d" | "30d" },
        pcapJobId: pcapJobIdParam ?? undefined,
        page,
        pageSize: defaultPageSize,
      });
      setData(response);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load detections.");
    } finally {
      setLoading(false);
    }
  }, [debouncedQuery, status, severity, techniqueId, timePreset, page, pcapJobIdParam]);

  useEffect(() => {
    loadMetadata().catch((err) => console.error(err));
  }, [loadMetadata]);

  useEffect(() => {
    loadDetections().catch((err) => console.error(err));
  }, [loadDetections]);

  const loadDetectionDetail = useCallback(async () => {
    if (!detectionIdParam) return;
    try {
      setDetailLoading(true);
      const det = await otAdapter.getOtDetection(detectionIdParam);
      setSelectedDetection(det);
      setDetailError(null);
    } catch (err) {
      console.error(err);
      setDetailError(err instanceof Error ? err.message : "Failed to load detection detail.");
    } finally {
      setDetailLoading(false);
    }
  }, [detectionIdParam]);

  useEffect(() => {
    if (!detectionIdParam) return;
    loadDetectionDetail().catch((err) => console.error(err));
  }, [detectionIdParam, loadDetectionDetail]);

  const resetFilters = () => {
    setQuery("");
    setStatus("");
    setSeverity("");
    setTechniqueId("");
    setTimePreset("24h");
    setPage(1);
  };

  const detections = data?.items ?? [];
  const total = data?.total ?? 0;

  return (
    <div className="ot-root">
      <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">Detections</div>
          <div className="page-subtitle">Behavior-based detections mapped to MITRE ATT&CK for ICS.</div>
        </div>
      </div>

      <div className="ot-filter-bar">
        <div className="field">
          <label className="field-label" htmlFor="det-search">Search</label>
          <input
            id="det-search"
            type="text"
            placeholder="Search by title, technique..."
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setPage(1);
            }}
          />
        </div>
        <div className="field">
          <label className="field-label" htmlFor="det-status">Status</label>
          <select
            id="det-status"
            value={status}
            onChange={(event) => {
              setStatus(event.target.value as OtDetectionStatus | "");
              setPage(1);
            }}
          >
            <option value="">All</option>
            <option value="open">Open</option>
            <option value="in_progress">In progress</option>
            <option value="closed">Closed</option>
          </select>
        </div>
        <div className="field">
          <label className="field-label" htmlFor="det-severity">Severity</label>
          <select
            id="det-severity"
            value={severity}
            onChange={(event) => {
              setSeverity(event.target.value as OtSeverity | "");
              setPage(1);
            }}
          >
            <option value="">All</option>
            <option value="low">Low</option>
            <option value="med">Med</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
        </div>
        <div className="field" style={{ minWidth: 220 }}>
          <label className="field-label" htmlFor="det-technique">Technique</label>
          <select
            id="det-technique"
            value={techniqueId}
            onChange={(event) => {
              setTechniqueId(event.target.value);
              setPage(1);
            }}
          >
            <option value="">All</option>
            <option value="T0849">T0849 Program Logic Modification</option>
            <option value="T0884">T0884 Modify Controller Tasking</option>
            <option value="T0851">T0851 Monitor Process State</option>
          </select>
        </div>
        <div className="field">
          <label className="field-label" htmlFor="det-time">Time range</label>
          <select
            id="det-time"
            value={timePreset}
            onChange={(event) => {
              setTimePreset(event.target.value);
              setPage(1);
            }}
          >
            <option value="24h">24h</option>
            <option value="7d">7d</option>
            <option value="30d">30d</option>
          </select>
        </div>
        <button type="button" className="text-link" onClick={resetFilters}>
          Reset filters
        </button>
      </div>

      {loading ? (
        <div className="card">
          <TableSkeleton rows={6} columns={7} />
        </div>
      ) : error ? (
        <ErrorState
          message="Failed to load detections. Please check your query and try again."
          details={error}
          onRetry={loadDetections}
        />
      ) : total === 0 && !filtersActive ? (
        <EmptyState
          title="No detections in selected period"
          message="Ensure sensors are online and check filter criteria."
        />
      ) : total === 0 ? (
        <EmptyState
          title="No detections match your filters"
          message="Try resetting your filters."
          action={
            <button type="button" className="btn btn-ghost" onClick={resetFilters}>
              Reset Filters
            </button>
          }
        />
      ) : (
        <div className="card table-wrap">
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
              {detections.map((det) => (
                <tr
                  key={det.id}
                  className="table-row-clickable"
                  onClick={() => {
                    setSelectedDetection(det);
                    setDetailError(null);
                  }}
                >
                  <td>
                    <span className={`severity-pill ${severityClass(det.severity)}`}>
                      {det.severity}
                    </span>
                  </td>
                  <td>{det.title}</td>
                  <td>
                    <span className="ot-chip">{det.technique?.techniqueId ?? "—"}</span>
                  </td>
                  <td className="muted">{det.assetIds.length}</td>
                  <td className="muted">{sensorsById.get(det.sensorId)?.name ?? det.sensorId}</td>
                  <td className="muted">{formatRelativeTime(det.ts)}</td>
                  <td>
                    <span className={`status-pill ${detectionStatusClass(det.status)}`}>
                      {statusLabel(det.status)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <Pagination
            page={data?.page ?? 1}
            pageSize={data?.pageSize ?? defaultPageSize}
            total={total}
            onPageChange={setPage}
          />
        </div>
      )}

      <OtDrawer
        title={selectedDetection?.title ?? "Detection"}
        subtitle={selectedDetection?.technique?.techniqueName}
        open={Boolean(selectedDetection || detailLoading)}
        onClose={() => setSelectedDetection(null)}
        footer={
          <div className="stack-horizontal">
            <button type="button" className="btn btn-ghost">In Progress</button>
            <button type="button" className="btn btn-ghost">Close</button>
          </div>
        }
      >
        {detailLoading ? (
          <div className="loading-skeleton-line" />
        ) : detailError ? (
          <ErrorState
            message="Failed to load detection detail."
            details={detailError}
            onRetry={loadDetectionDetail}
          />
        ) : selectedDetection ? (
          <div className="stack-vertical">
            <div className="card">
              <div className="card-title">Technique</div>
              <div className="card-subtitle">
                {selectedDetection.technique?.techniqueId} · {selectedDetection.technique?.techniqueName}
              </div>
              <p className="muted">{selectedDetection.description}</p>
            </div>
            <div className="card">
              <div className="card-title">Evidence</div>
              <EvidenceKeyValueList items={selectedDetection.evidence} />
            </div>
            <div className="card">
              <div className="card-title">Affected assets</div>
              <ul className="ot-simple-list">
                {selectedDetection.assetIds.map((assetId) => {
                  const asset = assetsById.get(assetId);
                  return (
                    <li key={assetId}>
                      <span>{asset?.name ?? assetId}</span>
                      <button
                        type="button"
                        className="text-link"
                        onClick={() => navigate("/ot/assets")}
                      >
                        {asset?.ip ?? "View asset"}
                      </button>
                    </li>
                  );
                })}
              </ul>
            </div>
            <div className="card">
              <div className="card-title">Recommended actions</div>
              <ul className="ot-simple-list">
                <li>Validate with OT engineer before containment.</li>
                <li>Confirm change window authorization.</li>
                <li>Review recent firmware changes.</li>
              </ul>
            </div>
          </div>
        ) : (
          <EmptyState message="Select a detection to view details." />
        )}
      </OtDrawer>
      </div>
    </div>
  );
};

export default DetectionsPage;
