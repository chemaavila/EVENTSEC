import { useCallback, useEffect, useMemo, useState } from "react";
import otAdapter from "../../services/ot";
import type { OtAsset, OtCommunication, OtDirection, OtProtocol, PaginatedResponse } from "../../types/ot";
import DirectionPill from "../../components/ot/DirectionPill";
import OtDrawer from "../../components/ot/OtDrawer";
import TableSkeleton from "../../components/ot/TableSkeleton";
import Pagination from "../../components/ot/Pagination";
import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import { formatRelativeTime } from "../../lib/otFormat";
import { useDebouncedValue } from "../../lib/useDebouncedValue";

const defaultPageSize = 8;

const CommunicationsPage = () => {
  const [query, setQuery] = useState("");
  const debouncedQuery = useDebouncedValue(query, 400);
  const [protocol, setProtocol] = useState<OtProtocol | "">("");
  const [direction, setDirection] = useState<OtDirection | "">("");
  const [timePreset, setTimePreset] = useState("24h");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<PaginatedResponse<OtCommunication> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [assets, setAssets] = useState<OtAsset[]>([]);
  const [selectedComm, setSelectedComm] = useState<OtCommunication | null>(null);

  const assetsById = useMemo(() => new Map(assets.map((asset) => [asset.id, asset])), [assets]);

  const filtersActive = useMemo(() => {
    return Boolean(debouncedQuery || protocol || direction || timePreset !== "24h");
  }, [debouncedQuery, protocol, direction, timePreset]);

  const loadAssets = useCallback(async () => {
    try {
      const response = await otAdapter.listOtAssets({ page: 1, pageSize: 200 });
      setAssets(response.items);
    } catch (err) {
      console.error(err);
    }
  }, []);

  const loadComms = useCallback(async () => {
    try {
      setLoading(true);
      const response = await otAdapter.listOtCommunications({
        q: debouncedQuery || undefined,
        protocol: protocol || undefined,
        direction: direction || undefined,
        timeRange: { preset: timePreset as "24h" | "7d" | "30d" },
        page,
        pageSize: defaultPageSize,
      });
      setData(response);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load communications.");
    } finally {
      setLoading(false);
    }
  }, [debouncedQuery, protocol, direction, timePreset, page]);

  useEffect(() => {
    loadAssets().catch((err) => console.error(err));
  }, [loadAssets]);

  useEffect(() => {
    loadComms().catch((err) => console.error(err));
  }, [loadComms]);

  const communications = data?.items ?? [];
  const total = data?.total ?? 0;

  return (
    <div className="ot-root">
      <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">Communications</div>
          <div className="page-subtitle">Observed network communications from passive sensors.</div>
        </div>
      </div>

      <div className="ot-filter-bar">
        <div className="field" style={{ minWidth: 220 }}>
          <label className="field-label" htmlFor="comm-search">Search</label>
          <input
            id="comm-search"
            type="text"
            placeholder="Search by IP, asset, protocol..."
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setPage(1);
            }}
          />
        </div>
        <div className="field">
          <label className="field-label" htmlFor="comm-protocol">Protocol</label>
          <select
            id="comm-protocol"
            value={protocol}
            onChange={(event) => {
              setProtocol(event.target.value as OtProtocol | "");
              setPage(1);
            }}
          >
            <option value="">All</option>
            <option value="Modbus">Modbus</option>
            <option value="DNP3">DNP3</option>
            <option value="BACnet">BACnet</option>
            <option value="S7">S7</option>
            <option value="OPCUA">OPC UA</option>
            <option value="Unknown">Unknown</option>
          </select>
        </div>
        <div className="direction-pill-group">
          {(["IT->OT", "OT->OT", "OT->IT"] as OtDirection[]).map((dir) => (
            <DirectionPill
              key={dir}
              direction={dir}
              active={direction === dir}
              onClick={() => {
                setDirection(direction === dir ? "" : dir);
                setPage(1);
              }}
            />
          ))}
        </div>
        <div className="field">
          <label className="field-label" htmlFor="comm-time">Time range</label>
          <select
            id="comm-time"
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
      </div>

      {loading ? (
        <div className="card">
          <TableSkeleton rows={6} columns={7} />
        </div>
      ) : error ? (
        <ErrorState
          message="Failed to load communications. Please check sensor connectivity and try again."
          details={error}
          onRetry={loadComms}
        />
      ) : total === 0 && !filtersActive ? (
        <EmptyState
          title="No communications observed"
          message="For live data, configure SPAN/TAP to the OT sensor."
        />
      ) : total === 0 ? (
        <EmptyState
          title="No communications match your filters"
          message="Try resetting your filters."
          action={
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => {
                setQuery("");
                setProtocol("");
                setDirection("");
                setTimePreset("24h");
                setPage(1);
              }}
            >
              Reset Filters
            </button>
          }
        />
      ) : (
        <div className="card table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Direction</th>
                <th>Source</th>
                <th>Destination</th>
                <th>Protocol</th>
                <th>Summary</th>
                <th>Bytes/Packets</th>
              </tr>
            </thead>
            <tbody>
              {communications.map((comm) => {
                const srcAsset = comm.srcAssetId ? assetsById.get(comm.srcAssetId) : null;
                const dstAsset = comm.dstAssetId ? assetsById.get(comm.dstAssetId) : null;
                return (
                  <tr
                    key={comm.id}
                    className="table-row-clickable"
                    onClick={() => setSelectedComm(comm)}
                  >
                    <td className="muted">{formatRelativeTime(comm.ts)}</td>
                    <td>
                      <DirectionPill direction={comm.direction} />
                    </td>
                    <td>
                      <div>{comm.srcIp}</div>
                      <div className="muted">{srcAsset?.name ?? "Unknown"}</div>
                    </td>
                    <td>
                      <div>{comm.dstIp}</div>
                      <div className="muted">{dstAsset?.name ?? "Unknown"}</div>
                    </td>
                    <td>
                      <span className="ot-chip">{comm.protocol}</span>
                      <span className="muted">{comm.port ? `:${comm.port}` : ""}</span>
                    </td>
                    <td>{comm.summary}</td>
                    <td className="muted">
                      {comm.bytes ? `${comm.bytes}B` : "—"}
                      {comm.packets ? ` / ${comm.packets} pkts` : ""}
                    </td>
                  </tr>
                );
              })}
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
        title="Conversation Details"
        subtitle={selectedComm ? `${selectedComm.srcIp} → ${selectedComm.dstIp}` : undefined}
        open={Boolean(selectedComm)}
        onClose={() => setSelectedComm(null)}
      >
        {selectedComm ? (
          <div className="stack-vertical">
            <div className="drawer-fields">
              <div className="drawer-field">
                <div className="drawer-field-label">Source</div>
                <div className="drawer-field-value">{selectedComm.srcIp}</div>
              </div>
              <div className="drawer-field">
                <div className="drawer-field-label">Destination</div>
                <div className="drawer-field-value">{selectedComm.dstIp}</div>
              </div>
              <div className="drawer-field">
                <div className="drawer-field-label">Protocol</div>
                <div className="drawer-field-value">{selectedComm.protocol}</div>
              </div>
              <div className="drawer-field">
                <div className="drawer-field-label">Time</div>
                <div className="drawer-field-value">{formatRelativeTime(selectedComm.ts)}</div>
              </div>
              <div className="drawer-field">
                <div className="drawer-field-label">Summary</div>
                <div className="drawer-field-value">{selectedComm.summary}</div>
              </div>
            </div>
            <div className="card">
              <div className="card-title">Raw packet snippet</div>
              <pre className="drawer-json-body">Packet data redacted for safe review.</pre>
            </div>
          </div>
        ) : null}
      </OtDrawer>
      </div>
    </div>
  );
};

export default CommunicationsPage;
