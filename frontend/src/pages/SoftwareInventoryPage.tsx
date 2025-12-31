import { useEffect, useMemo, useState } from "react";
import {
  getInventoryOverview,
  listAgents,
  listEndpoints,
  type Agent,
  type Endpoint,
  type InventorySnapshot,
} from "../services/api";

type SoftwareRow = {
  name: string;
  version?: string;
  vendor?: string;
};

const extractSoftwareRows = (snapshot: InventorySnapshot): SoftwareRow[] | null => {
  const data = snapshot.data as Record<string, unknown>;
  const candidates =
    (Array.isArray(data.packages) && data.packages) ||
    (Array.isArray(data.software) && data.software) ||
    (Array.isArray(data.apps) && data.apps);

  if (!candidates) {
    return null;
  }

  return candidates
    .map((item) => {
      if (!item || typeof item !== "object") {
        return null;
      }
      const record = item as Record<string, unknown>;
      const name = String(record.name ?? record.title ?? record.app ?? "Unknown");
      const version = record.version ? String(record.version) : undefined;
      const vendor = record.vendor
        ? String(record.vendor)
        : record.publisher
        ? String(record.publisher)
        : undefined;
      return { name, version, vendor };
    })
    .filter((item): item is SoftwareRow => Boolean(item?.name));
};

const normalizeMatchValue = (value?: string | null) => value?.trim().toLowerCase() ?? "";

const resolveAgentForEndpoint = (
  endpoint: Endpoint,
  agents: Agent[]
): Agent | undefined => {
  const endpointHostname = normalizeMatchValue(endpoint.hostname);
  const endpointDisplay = normalizeMatchValue(endpoint.display_name);
  const endpointIp = normalizeMatchValue(endpoint.ip_address);

  return agents.find((agent) => {
    const agentName = normalizeMatchValue(agent.name);
    const agentIp = normalizeMatchValue(agent.ip_address);
    return (
      (agentName && (agentName === endpointHostname || agentName === endpointDisplay)) ||
      (agentIp && agentIp === endpointIp)
    );
  });
};

const SoftwareInventoryPage = () => {
  const [endpoints, setEndpoints] = useState<Endpoint[]>([]);
  const [selected, setSelected] = useState<Endpoint | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [snapshots, setSnapshots] = useState<InventorySnapshot[]>([]);
  const [endpointsLoading, setEndpointsLoading] = useState(true);
  const [inventoryLoading, setInventoryLoading] = useState(false);
  const [endpointsError, setEndpointsError] = useState<string | null>(null);
  const [inventoryError, setInventoryError] = useState<string | null>(null);

  const loadEndpoints = async () => {
    try {
      setEndpointsLoading(true);
      const [endpointData, agentData] = await Promise.all([
        listEndpoints(),
        listAgents(),
      ]);
      setEndpoints(endpointData);
      setAgents(agentData);
      setSelected((current) => {
        if (!endpointData.length) {
          return null;
        }
        const existing = current
          ? endpointData.find((endpoint) => endpoint.id === current.id)
          : null;
        return existing ?? endpointData[0];
      });
      setEndpointsError(null);
    } catch (err) {
      setEndpointsError(
        err instanceof Error ? err.message : "Unexpected error while loading endpoints"
      );
    } finally {
      setEndpointsLoading(false);
    }
  };

  const loadSoftwareInventory = async (agentId: number) => {
    try {
      setInventoryLoading(true);
      const overview = await getInventoryOverview(agentId, "software");
      const software = overview.categories?.software ?? [];
      setSnapshots(software);
      setInventoryError(null);
    } catch (err) {
      setInventoryError(
        err instanceof Error
          ? err.message
          : "Unexpected error while loading software inventory"
      );
    } finally {
      setInventoryLoading(false);
    }
  };

  useEffect(() => {
    loadEndpoints().catch((err) => console.error(err));
  }, []);

  useEffect(() => {
    if (selected) {
      const agent = resolveAgentForEndpoint(selected, agents);
      if (!agent) {
        setSnapshots([]);
        setInventoryError(
          "No matching agent found for this endpoint. Ensure the endpoint is linked to an enrolled agent."
        );
        return;
      }
      loadSoftwareInventory(agent.id).catch((err) => console.error(err));
    } else {
      setSnapshots([]);
      setInventoryError(null);
    }
  }, [selected, agents]);

  const mostRecentSnapshot = useMemo(() => {
    if (snapshots.length === 0) {
      return null;
    }
    return [...snapshots].sort(
      (a, b) => new Date(b.collected_at).getTime() - new Date(a.collected_at).getTime()
    )[0];
  }, [snapshots]);

  const softwareRows = useMemo(() => {
    if (!mostRecentSnapshot) {
      return null;
    }
    return extractSoftwareRows(mostRecentSnapshot);
  }, [mostRecentSnapshot]);

  return (
    <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">Software inventory</div>
          <div className="page-subtitle">
            Review installed software reported by each endpoint agent.
          </div>
        </div>
        <div className="stack-horizontal">
          <button type="button" className="btn btn-ghost" onClick={loadEndpoints}>
            Refresh
          </button>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Endpoints</div>
              <div className="card-subtitle">Select a device to view software.</div>
            </div>
          </div>

          {endpointsLoading && <div className="muted">Loading endpoints…</div>}
          {endpointsError && (
            <div className="muted">
              Failed to load endpoints:
              {" "}
              {endpointsError}
            </div>
          )}
          {!endpointsLoading && !endpointsError && (
            <div className="stack-vertical">
              {endpoints.map((endpoint) => (
                <button
                  type="button"
                  key={endpoint.id}
                  className={`alert-row ${
                    selected?.id === endpoint.id ? "sidebar-link-active" : ""
                  }`}
                  onClick={() => setSelected(endpoint)}
                >
                  <div className="alert-row-main">
                    <div className="alert-row-title">{endpoint.display_name}</div>
                    <div className="alert-row-meta">
                      <span className="tag">{endpoint.status}</span>
                      <span className="tag">{endpoint.ip_address}</span>
                    </div>
                  </div>
                  <div className="muted">{endpoint.owner}</div>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Software details</div>
              <div className="card-subtitle">
                {selected
                  ? `Latest snapshot for ${selected.display_name}`
                  : "Select an endpoint to continue"}
              </div>
            </div>
          </div>

          {inventoryLoading && <div className="muted">Loading inventory…</div>}
          {inventoryError && (
            <div className="muted">
              Failed to load inventory:
              {" "}
              {inventoryError}
            </div>
          )}
          {!inventoryLoading && !inventoryError && selected && snapshots.length === 0 && (
            <div className="muted">
              No software inventory yet. Ensure the agent is sending inventory snapshots.
            </div>
          )}
          {!inventoryLoading &&
            !inventoryError &&
            mostRecentSnapshot &&
            softwareRows &&
            softwareRows.length > 0 && (
            <div className="table-responsive">
              <table className="table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Version</th>
                    <th>Vendor</th>
                  </tr>
                </thead>
                <tbody>
                  {softwareRows.map((row, index) => (
                    <tr key={`${row.name}-${index}`}>
                      <td>{row.name}</td>
                      <td>{row.version ?? "—"}</td>
                      <td>{row.vendor ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {!inventoryLoading &&
            !inventoryError &&
            mostRecentSnapshot &&
            (!softwareRows || softwareRows.length === 0) && (
            <pre className="code-block">{JSON.stringify(mostRecentSnapshot.data, null, 2)}</pre>
          )}
        </div>
      </div>
    </div>
  );
};

export default SoftwareInventoryPage;
