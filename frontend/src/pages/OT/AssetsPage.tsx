import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import otAdapter from "../../services/ot";
import type { OtAsset, OtAssetType, OtCriticality, OtSeverity, PaginatedResponse } from "../../types/ot";
import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import OtDrawer from "../../components/ot/OtDrawer";
import TableSkeleton from "../../components/ot/TableSkeleton";
import Pagination from "../../components/ot/Pagination";
import { criticalityClass, formatRelativeTime, severityClass } from "../../lib/otFormat";
import { useDebouncedValue } from "../../lib/useDebouncedValue";

const defaultPageSize = 8;

const AssetsPage = () => {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const debouncedQuery = useDebouncedValue(query, 400);
  const [site, setSite] = useState("");
  const [zone, setZone] = useState("");
  const [type, setType] = useState<OtAssetType | "">("");
  const [criticality, setCriticality] = useState<OtCriticality | "">("");
  const [lastSeenPreset, setLastSeenPreset] = useState("7d");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<PaginatedResponse<OtAsset> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAssetId, setSelectedAssetId] = useState<string | null>(null);
  const [assetDetail, setAssetDetail] = useState<{
    asset: OtAsset;
    relatedDetections: { id: string; title: string; severity: OtSeverity; ts: string }[];
    topCommunications: Array<{ peerIp: string; protocol: string; count: number }>;
  } | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);

  const filtersActive = useMemo(() => {
    return Boolean(
      debouncedQuery || site || zone || type || criticality || lastSeenPreset !== "7d"
    );
  }, [debouncedQuery, site, zone, type, criticality, lastSeenPreset]);

  const loadAssets = useCallback(async () => {
    try {
      setLoading(true);
      const response = await otAdapter.listOtAssets({
        q: debouncedQuery || undefined,
        site: site || undefined,
        zone: zone || undefined,
        type: type || undefined,
        criticality: criticality || undefined,
        lastSeen: { preset: lastSeenPreset as "24h" | "7d" | "30d" },
        page,
        pageSize: defaultPageSize,
      });
      setData(response);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load assets.");
    } finally {
      setLoading(false);
    }
  }, [debouncedQuery, site, zone, type, criticality, lastSeenPreset, page]);

  useEffect(() => {
    loadAssets().catch((err) => console.error(err));
  }, [loadAssets]);

  const loadAssetDetail = useCallback(async () => {
    if (!selectedAssetId) return;
    try {
      setDetailLoading(true);
      const detail = await otAdapter.getOtAsset(selectedAssetId);
      setAssetDetail({
        asset: detail.asset,
        relatedDetections: detail.relatedDetections.map((det) => ({
          id: det.id,
          title: det.title,
          severity: det.severity,
          ts: det.ts,
        })),
        topCommunications: detail.topCommunications.map((comm) => ({
          peerIp: comm.peerIp,
          protocol: comm.protocol,
          count: comm.count,
        })),
      });
      setDetailError(null);
    } catch (err) {
      console.error(err);
      setDetailError(err instanceof Error ? err.message : "Failed to load asset detail.");
    } finally {
      setDetailLoading(false);
    }
  }, [selectedAssetId]);

  useEffect(() => {
    if (!selectedAssetId) {
      setAssetDetail(null);
      setDetailError(null);
      return;
    }
    loadAssetDetail().catch((err) => console.error(err));
  }, [loadAssetDetail, selectedAssetId]);

  const resetFilters = () => {
    setQuery("");
    setSite("");
    setZone("");
    setType("");
    setCriticality("");
    setLastSeenPreset("7d");
    setPage(1);
  };

  const assets = data?.items ?? [];
  const total = data?.total ?? 0;

  return (
    <div className="ot-root">
      <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">Assets</div>
          <div className="page-subtitle">Discovered OT/ICS assets grouped by site and zone.</div>
        </div>
        <div className="stack-horizontal">
          <button type="button" className="btn btn-ghost">
            Export CSV
          </button>
          <button type="button" className="btn btn-ghost">
            Add Tag
          </button>
        </div>
      </div>

      <div className="ot-filter-bar">
        <div className="field" style={{ minWidth: 220 }}>
          <label className="field-label" htmlFor="asset-search">Search</label>
          <input
            id="asset-search"
            type="text"
            placeholder="Search by name, IP, vendor..."
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setPage(1);
            }}
          />
        </div>
        <div className="field">
          <label className="field-label" htmlFor="asset-site">Site</label>
          <select
            id="asset-site"
            value={site}
            onChange={(event) => {
              setSite(event.target.value);
              setPage(1);
            }}
          >
            <option value="">All</option>
            <option value="HQ">HQ</option>
            <option value="Plant West">Plant West</option>
            <option value="Plant North">Plant North</option>
          </select>
        </div>
        <div className="field">
          <label className="field-label" htmlFor="asset-zone">Zone</label>
          <select
            id="asset-zone"
            value={zone}
            onChange={(event) => {
              setZone(event.target.value);
              setPage(1);
            }}
          >
            <option value="">All</option>
            <option value="Level 1">Level 1</option>
            <option value="Level 2">Level 2</option>
            <option value="Level 3">Level 3</option>
            <option value="Cell 3">Cell 3</option>
            <option value="Engineering">Engineering</option>
            <option value="Packaging">Packaging</option>
          </select>
        </div>
        <div className="field">
          <label className="field-label" htmlFor="asset-type">Type</label>
          <select
            id="asset-type"
            value={type}
            onChange={(event) => {
              setType(event.target.value as OtAssetType | "");
              setPage(1);
            }}
          >
            <option value="">All</option>
            <option value="PLC">PLC</option>
            <option value="HMI">HMI</option>
            <option value="RTU">RTU</option>
            <option value="Server">Server</option>
            <option value="Switch">Switch</option>
            <option value="Unknown">Unknown</option>
          </select>
        </div>
        <div className="field">
          <label className="field-label" htmlFor="asset-criticality">Criticality</label>
          <select
            id="asset-criticality"
            value={criticality}
            onChange={(event) => {
              setCriticality(event.target.value as OtCriticality | "");
              setPage(1);
            }}
          >
            <option value="">All</option>
            <option value="low">Low</option>
            <option value="med">Med</option>
            <option value="high">High</option>
          </select>
        </div>
        <div className="field">
          <label className="field-label" htmlFor="asset-time">Last seen</label>
          <select
            id="asset-time"
            value={lastSeenPreset}
            onChange={(event) => {
              setLastSeenPreset(event.target.value);
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
          message="Failed to load assets. Please check sensor connectivity and try again."
          details={error}
          onRetry={loadAssets}
        />
      ) : total === 0 && !filtersActive ? (
        <EmptyState
          title="No assets discovered yet"
          message="Ensure sensor is online or upload a PCAP."
          action={
            <div className="stack-horizontal">
              <button type="button" className="btn" onClick={() => navigate("/ot/pcap")}>Upload PCAP</button>
              <button type="button" className="btn btn-ghost" onClick={() => navigate("/ot/sensors")}>Go to Sensors</button>
            </div>
          }
        />
      ) : total === 0 ? (
        <EmptyState
          title="No assets match your filters"
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
                <th>Asset</th>
                <th>IP</th>
                <th>Vendor / Model</th>
                <th>Site / Zone</th>
                <th>Criticality</th>
                <th>Last Seen</th>
                <th>Tags</th>
              </tr>
            </thead>
            <tbody>
              {assets.map((asset) => (
                <tr
                  key={asset.id}
                  className="table-row-clickable"
                  onClick={() => {
                    setSelectedAssetId(asset.id);
                    setDetailError(null);
                  }}
                >
                  <td>{asset.name}</td>
                  <td className="muted">{asset.ip}</td>
                  <td>
                    <div>{asset.vendor ?? "—"}</div>
                    <div className="muted">{asset.model ?? "—"}</div>
                  </td>
                  <td>
                    <div className="stack-horizontal">
                      <span className="tag">Site: {asset.site}</span>
                      <span className="tag">Zone: {asset.zone}</span>
                    </div>
                  </td>
                  <td>
                    <span className={`severity-pill ${criticalityClass(asset.criticality)}`}>
                      {asset.criticality}
                    </span>
                  </td>
                  <td className="muted">{formatRelativeTime(asset.lastSeen)}</td>
                  <td>
                    <div className="stack-horizontal">
                      {asset.tags.map((tag) => (
                        <span key={tag} className="tag">
                          {tag}
                        </span>
                      ))}
                    </div>
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
        title={assetDetail?.asset.name ?? "Asset"}
        subtitle={assetDetail?.asset.ip}
        open={Boolean(selectedAssetId)}
        onClose={() => setSelectedAssetId(null)}
        footer={
          <div className="stack-horizontal">
            <button type="button" className="btn" onClick={() => navigate("/ot/detections")}>Open in Detections</button>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => assetDetail && navigator.clipboard.writeText(assetDetail.asset.ip)}
            >
              Copy IP
            </button>
          </div>
        }
      >
        {detailLoading ? (
          <div className="loading-skeleton-line" />
        ) : detailError ? (
          <ErrorState
            message="Failed to load asset detail."
            details={detailError}
            onRetry={loadAssetDetail}
          />
        ) : assetDetail ? (
          <div className="stack-vertical">
            <div className="card">
              <div className="card-title">Summary</div>
              <div className="drawer-fields">
                <div className="drawer-field">
                  <div className="drawer-field-label">Type</div>
                  <div className="drawer-field-value">{assetDetail.asset.assetType}</div>
                </div>
                <div className="drawer-field">
                  <div className="drawer-field-label">Site / Zone</div>
                  <div className="drawer-field-value">{assetDetail.asset.site} · {assetDetail.asset.zone}</div>
                </div>
                <div className="drawer-field">
                  <div className="drawer-field-label">Criticality</div>
                  <div className="drawer-field-value">{assetDetail.asset.criticality}</div>
                </div>
                <div className="drawer-field">
                  <div className="drawer-field-label">First seen</div>
                  <div className="drawer-field-value">{formatRelativeTime(assetDetail.asset.firstSeen)}</div>
                </div>
                <div className="drawer-field">
                  <div className="drawer-field-label">Last seen</div>
                  <div className="drawer-field-value">{formatRelativeTime(assetDetail.asset.lastSeen)}</div>
                </div>
              </div>
            </div>
            <div className="card">
              <div className="card-title">Related detections</div>
              <table className="table">
                <thead>
                  <tr>
                    <th>Severity</th>
                    <th>Title</th>
                    <th>Time</th>
                  </tr>
                </thead>
                <tbody>
                  {assetDetail.relatedDetections.map((det) => (
                    <tr key={det.id}>
                      <td>
                    <span className={`severity-pill ${severityClass(det.severity)}`}>
                      {det.severity}
                    </span>
                      </td>
                      <td>{det.title}</td>
                      <td className="muted">{formatRelativeTime(det.ts)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="card">
              <div className="card-title">Top communications</div>
              <ul className="ot-simple-list">
                {assetDetail.topCommunications.map((comm) => (
                  <li key={`${comm.peerIp}-${comm.protocol}`}>
                    <span>{comm.peerIp}</span>
                    <span className="muted">{comm.protocol} · {comm.count}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ) : (
          <EmptyState message="Select an asset to view its details." />
        )}
      </OtDrawer>
      </div>
    </div>
  );
};

export default AssetsPage;
