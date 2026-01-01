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

type SoftwareStatus = "approved" | "not_approved" | "vulnerable";

type InventoryTableRow = SoftwareRow & {
  id: string;
  license: string;
  lastSeen: string;
  assets: number;
  status: SoftwareStatus;
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
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<SoftwareStatus | "">("");
  const [lastDetected, setLastDetected] = useState("");
  const [showAdd, setShowAdd] = useState(false);

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

  const normalizedSearch = normalizeMatchValue(search);

  const tableRows = useMemo<InventoryTableRow[]>(() => {
    if (!softwareRows || !mostRecentSnapshot) {
      return [];
    }
    const baseLastSeen = new Date(mostRecentSnapshot.collected_at).toLocaleString();
    return softwareRows.map((row, index) => {
      const name = row.name ?? "Unknown";
      const vendor = row.vendor ?? "—";
      let status: SoftwareStatus = "approved";
      const lowered = name.toLowerCase();
      if (!row.vendor) {
        status = "not_approved";
      } else if (lowered.includes("chrome") || lowered.includes("node") || lowered.includes("winrar")) {
        status = "vulnerable";
      }
      const license = row.vendor ? `${row.vendor.slice(0, 4).toUpperCase()}-${String(1000 + index).padEnd(4, "*")}` : "N/A";
      return {
        id: `${name}-${index}`,
        name,
        version: row.version ?? "—",
        vendor,
        license,
        lastSeen: baseLastSeen,
        assets: selected ? 1 : 0,
        status,
      };
    });
  }, [softwareRows, mostRecentSnapshot, selected]);

  const filteredRows = useMemo(() => {
    return tableRows.filter((row) => {
      if (normalizedSearch) {
        const match = `${row.name} ${row.vendor} ${row.version}`.toLowerCase();
        if (!match.includes(normalizedSearch)) {
          return false;
        }
      }
      if (statusFilter && row.status !== statusFilter) {
        return false;
      }
      return true;
    });
  }, [tableRows, normalizedSearch, statusFilter]);

  const statusLabel = (status: SoftwareStatus) => {
    switch (status) {
      case "approved":
        return { label: "Aprobado", className: "inventory-status inventory-status-approved" };
      case "not_approved":
        return { label: "No Aprobado", className: "inventory-status inventory-status-neutral" };
      case "vulnerable":
        return { label: "Vulnerable", className: "inventory-status inventory-status-vulnerable" };
      default:
        return { label: "—", className: "inventory-status" };
    }
  };

  return (
    <div className="page-root inventory-page">
      <div className="inventory-breadcrumbs">
        <span className="muted">Home</span>
        <span className="muted">/</span>
        <span className="muted">Inventory</span>
        <span className="muted">/</span>
        <span>Gestión de Software</span>
      </div>

      <div className="inventory-header">
        <div>
          <div className="page-title">Gestión de Software</div>
          <div className="page-subtitle">
            Inventario centralizado y monitoreo de seguridad en tiempo real para aplicaciones detectadas en endpoints.
          </div>
        </div>
        <div className="stack-horizontal">
          <button type="button" className="btn btn-ghost" onClick={loadEndpoints}>
            Actualizar
          </button>
          <button type="button" className="btn" onClick={() => setShowAdd(true)}>
            Añadir Nuevo Software
          </button>
        </div>
      </div>

      <div className="inventory-filters">
        <label className="field inventory-filter">
          <span>Endpoint</span>
          <select
            value={selected?.id ?? ""}
            onChange={(event) => {
              const next = endpoints.find((endpoint) => String(endpoint.id) === event.target.value);
              setSelected(next ?? null);
            }}
          >
            <option value="">Seleccionar endpoint...</option>
            {endpoints.map((endpoint) => (
              <option key={endpoint.id} value={endpoint.id}>
                {endpoint.display_name}
              </option>
            ))}
          </select>
        </label>
        <label className="field inventory-filter">
          <span>Buscar</span>
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Buscar por nombre, vendedor..."
          />
        </label>
        <label className="field inventory-filter">
          <span>Estado</span>
          <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as SoftwareStatus | "")}>
            <option value="">Todos los estados</option>
            <option value="approved">Aprobado</option>
            <option value="not_approved">No Aprobado</option>
            <option value="vulnerable">Vulnerable</option>
          </select>
        </label>
        <label className="field inventory-filter">
          <span>Última Detección</span>
          <input value={lastDetected} onChange={(event) => setLastDetected(event.target.value)} type="date" />
        </label>
      </div>

      {(endpointsLoading || inventoryLoading) && (
        <div className="card">
          <div className="muted">Cargando inventario…</div>
        </div>
      )}
      {endpointsError && (
        <div className="card">
          <div className="muted">Error al cargar endpoints: {endpointsError}</div>
        </div>
      )}
      {inventoryError && (
        <div className="card">
          <div className="muted">Error al cargar inventario: {inventoryError}</div>
        </div>
      )}
      {!endpointsLoading && !inventoryLoading && selected && snapshots.length === 0 && (
        <div className="card">
          <div className="muted">No hay inventario aún. Revisa que el agente esté enviando snapshots.</div>
        </div>
      )}

      <div className="card inventory-table-card">
        <div className="inventory-table-header">
          <div>
            <div className="card-title">Listado General</div>
            <div className="card-subtitle">
              {selected ? `Último snapshot para ${selected.display_name}` : "Selecciona un endpoint para continuar"}
            </div>
          </div>
          <div className="muted">
            {filteredRows.length} resultados {lastDetected ? `• Fecha filtro: ${lastDetected}` : ""}
          </div>
        </div>

        {filteredRows.length > 0 ? (
          <div className="table-responsive">
            <table className="table inventory-table">
              <thead>
                <tr>
                  <th>Nombre del Software</th>
                  <th>Versión</th>
                  <th>Vendedor</th>
                  <th>Licencia</th>
                  <th>Última Detección</th>
                  <th>Activos</th>
                  <th>Estado</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {filteredRows.map((row) => {
                  const status = statusLabel(row.status);
                  return (
                    <tr key={row.id}>
                      <td>{row.name}</td>
                      <td>{row.version}</td>
                      <td>{row.vendor}</td>
                      <td className="inventory-mono">{row.license}</td>
                      <td>{row.lastSeen}</td>
                      <td>
                        <span className="inventory-link">{row.assets} Endpoints</span>
                      </td>
                      <td>
                        <span className={status.className}>{status.label}</span>
                      </td>
                      <td>
                        <button type="button" className="btn btn-ghost btn-sm">
                          •••
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="muted">No hay software que coincida con los filtros.</div>
        )}
      </div>

      {showAdd && (
        <div className="inventory-modal-backdrop" onClick={() => setShowAdd(false)}>
          <div className="inventory-modal" onClick={(event) => event.stopPropagation()}>
            <div className="inventory-modal-header">
              <div>
                <div className="card-title">Añadir Nuevo Software</div>
                <div className="card-subtitle">Registre una nueva aplicación en el sistema.</div>
              </div>
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => setShowAdd(false)}>
                Cerrar
              </button>
            </div>
            <div className="inventory-modal-body">
              <div className="grid-2">
                <label className="field">
                  <span>Nombre del Software</span>
                  <input placeholder="Ej. CrowdStrike Falcon" />
                </label>
                <label className="field">
                  <span>Versión</span>
                  <input placeholder="Ej. 6.24.156" />
                </label>
              </div>
              <div className="grid-2">
                <label className="field">
                  <span>Vendedor</span>
                  <input placeholder="Ej. CrowdStrike Inc." />
                </label>
                <label className="field">
                  <span>Categoría</span>
                  <select>
                    <option value="">Seleccionar categoría...</option>
                    <option value="security">Seguridad & Antivirus</option>
                    <option value="productivity">Productividad</option>
                    <option value="development">Desarrollo</option>
                    <option value="network">Herramientas de Red</option>
                    <option value="system">Sistema Operativo</option>
                  </select>
                </label>
              </div>
              <div className="grid-2">
                <label className="field">
                  <span>Clave de Licencia</span>
                  <input placeholder="XXXX-XXXX-XXXX-XXXX" />
                </label>
                <label className="field">
                  <span>Estado Inicial</span>
                  <select>
                    <option value="approved">Aprobado</option>
                    <option value="pending">Pendiente de Revisión</option>
                    <option value="restricted">Restringido</option>
                    <option value="blacklisted">Lista Negra</option>
                  </select>
                </label>
              </div>
              <label className="field">
                <span>Descripción</span>
                <textarea placeholder="Detalles técnicos, propósito del software o notas de cumplimiento..." />
              </label>
              <div className="inventory-upload">
                <div className="inventory-upload-header">Método de Instalación</div>
                <div className="inventory-upload-box">
                  <span>Haga clic o arrastre el archivo aquí</span>
                  <span className="muted small">Soporta .msi, .exe, .dmg (Max 500MB)</span>
                </div>
              </div>
            </div>
            <div className="inventory-modal-footer">
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => setShowAdd(false)}>
                Cancelar
              </button>
              <button type="button" className="btn btn-sm">
                Guardar Software
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SoftwareInventoryPage;
