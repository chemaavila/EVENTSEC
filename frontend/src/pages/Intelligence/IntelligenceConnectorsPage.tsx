import { useEffect, useState } from "react";
import CtiAdapterFallback from "../../components/cti/CtiAdapterFallback";
import ctiAdapter from "../../services/cti";
import { CtiNotImplementedError } from "../../services/cti/apiAdapter";
import type { CtiConnectorsData } from "../../services/cti";
import "../../components/cti/cti.css";

const IntelligenceConnectorsPage = () => {
  const [data, setData] = useState<CtiConnectorsData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [adapterUnavailable, setAdapterUnavailable] = useState(false);

  useEffect(() => {
    let mounted = true;
    ctiAdapter
      .getConnectors()
      .then((response) => {
        if (mounted) setData(response);
      })
      .catch((err) => {
        console.error(err);
        if (mounted && err instanceof CtiNotImplementedError) {
          setAdapterUnavailable(true);
          return;
        }
        if (mounted) setError("Unable to load connectors.");
      });
    return () => {
      mounted = false;
    };
  }, []);

  if (adapterUnavailable) {
    return (
      <CtiAdapterFallback
        onSwitchToMock={() => {
          window.localStorage.setItem("cti_use_mock", "true");
          window.location.reload();
        }}
      />
    );
  }

  if (!data) {
    return (
      <div className="cti-connectors-shell">
        <div className="cti-placeholder">
          <h1>Connectors</h1>
          <p>{error ?? "Loading connectors..."}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="cti-connectors-shell">
      <header className="cti-connectors-topbar">
        <div className="cti-connectors-topbar-left">
          <div className="cti-connectors-brand">
            <div className="cti-connectors-brand-icon">
              <span className="material-symbols-outlined" style={{ fontSize: 20 }}>
                shield_lock
              </span>
            </div>
            <h2>Consola SIEM/XDR</h2>
          </div>
          <nav className="cti-connectors-nav">
            {[
              { label: "Dashboard", active: false },
              { label: "Threat Intel", active: false },
              { label: "Connectors", active: true },
              { label: "Incidents", active: false },
              { label: "Settings", active: false },
            ].map((item) => (
              <a key={item.label} className={item.active ? "active" : ""} href="#">
                {item.label}
              </a>
            ))}
          </nav>
        </div>
        <div className="cti-connectors-topbar-right">
          <button type="button">
            <span className="material-symbols-outlined">search</span>
          </button>
          <button type="button">
            <span className="material-symbols-outlined">notifications</span>
          </button>
          <div className="cti-connectors-avatar">JD</div>
        </div>
      </header>

      <main className="cti-connectors-main">
        <div className="cti-connectors-header">
          <div>
            <h1>Connectors</h1>
            <p>Manage integrations, data sources, and ingestion pipelines.</p>
          </div>
          <div className="cti-connectors-header-actions">
            <button type="button">
              <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
                help
              </span>
              Documentation
            </button>
            <button className="primary" type="button">
              <span className="material-symbols-outlined" style={{ fontSize: 20 }}>
                add
              </span>
              Add Connector
            </button>
          </div>
        </div>

        <div className="cti-connectors-stats">
          {data.stats.map((stat) => (
            <div key={stat.id} className="cti-connectors-stat">
              <div className="cti-connectors-stat-icon" style={{ color: stat.color }}>
                <span className="material-symbols-outlined">{stat.icon}</span>
              </div>
              <div>
                <p>{stat.label}</p>
                <h3>{stat.value}</h3>
              </div>
            </div>
          ))}
        </div>

        <div className="cti-connectors-content">
          <section className="cti-connectors-list">
            <div className="cti-connectors-toolbar">
              <div className="cti-connectors-search">
                <span className="material-symbols-outlined">search</span>
                <input placeholder="Search connectors by name or IP..." />
              </div>
              <div className="cti-connectors-filters">
                {["All", "Import", "Enrichment", "Stream"].map((filter) => (
                  <button key={filter} className={filter === "All" ? "active" : ""} type="button">
                    {filter}
                  </button>
                ))}
              </div>
            </div>
            <div className="cti-connectors-table">
              <table>
                <thead>
                  <tr>
                    <th>Connector Name</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>Last Sync</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {data.connectors.map((connector) => (
                    <tr key={connector.id} className={connector.selected ? "selected" : undefined}>
                      <td>
                        <div className="cti-connectors-name">
                          <div className="cti-connectors-icon">
                            <span>{connector.name.split(" ")[0].slice(0, 2).toUpperCase()}</span>
                          </div>
                          <div>
                            <p>{connector.name}</p>
                            <span>
                              {connector.subtitle} • ID: {connector.id}
                            </span>
                          </div>
                        </div>
                      </td>
                      <td>
                        <span className={`cti-connectors-type ${connector.type.toLowerCase()}`}>{connector.type}</span>
                      </td>
                      <td>
                        <div className="cti-connectors-status" style={{ color: connector.statusColor }}>
                          <span className="dot" style={{ background: connector.statusColor }} />
                          {connector.status}
                        </div>
                      </td>
                      <td className="muted">{connector.lastSync}</td>
                      <td>
                        <span className="material-symbols-outlined">chevron_right</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <aside className="cti-connectors-detail">
            <div className="cti-connectors-detail-header">
              <div className="cti-connectors-detail-title">
                <div className="cti-connectors-detail-logo">CS</div>
                <div>
                  <h3>{data.detail.name}</h3>
                  <div className="cti-connectors-detail-meta">
                    <span className="cti-connectors-status-pill">{data.detail.status}</span>
                    <span>{data.detail.version}</span>
                  </div>
                </div>
              </div>
              <div className="cti-connectors-detail-actions">
                <button className="primary" type="button">
                  <span className="material-symbols-outlined">play_arrow</span>
                  Execute Now
                </button>
                <button type="button">
                  <span className="material-symbols-outlined">settings</span>
                </button>
                <button type="button">
                  <span className="material-symbols-outlined">more_vert</span>
                </button>
              </div>
            </div>

            <div className="cti-connectors-detail-body">
              <div className="cti-connectors-metrics">
                <div className="cti-connectors-metric">
                  <p>Last Heartbeat</p>
                  <div className="value">
                    <span className="material-symbols-outlined">monitor_heart</span>
                    {data.detail.heartbeat}
                  </div>
                  <small>{data.detail.heartbeatTime}</small>
                </div>
                <div className="cti-connectors-metric">
                  <p>Last Execution</p>
                  <div className="value">
                    <span className="material-symbols-outlined">check_circle</span>
                    {data.detail.lastExecution}
                  </div>
                  <small>{data.detail.lastExecutionDetail}</small>
                </div>
              </div>

              <div className="cti-connectors-config">
                <h4>Configuration</h4>
                {[
                  { label: "API Endpoint", value: data.detail.apiEndpoint },
                  { label: "Client ID", value: data.detail.clientId },
                  { label: "API Key", value: data.detail.apiKeyMasked },
                ].map((item) => (
                  <div key={item.label} className="cti-connectors-config-row">
                    <label>{item.label}</label>
                    <div>
                      <span>{item.value}</span>
                      <span className="material-symbols-outlined">content_copy</span>
                    </div>
                  </div>
                ))}
                <div className="cti-connectors-config-footer">
                  <span>Sync Interval</span>
                  <span className="chip">{data.detail.syncInterval}</span>
                </div>
              </div>

              <div className="cti-connectors-logs">
                <div className="cti-connectors-logs-header">
                  <h4>Live Logs</h4>
                  <div className="cti-connectors-live">
                    <span className="dot" />Live
                    <button type="button">Download</button>
                  </div>
                </div>
                <div className="cti-connectors-log-console">
                  <div className="session">Session ID: #LOG-88219</div>
                  {data.detail.logs.map((line) => (
                    <div key={line}>{line}</div>
                  ))}
                  <div className="cursor">_</div>
                </div>
              </div>
            </div>
          </aside>
        </div>
      </main>

      <div className="cti-connectors-assistant">
        <div className="cti-connectors-assistant-header">
          <span className="material-symbols-outlined">magic_button</span>
          {data.assistant.title}
          <span className="material-symbols-outlined">close</span>
        </div>
        <div className="cti-connectors-assistant-body">
          <p>{data.assistant.message}</p>
          <small>{data.assistant.subtitle}</small>
          <div className="progress">
            <span style={{ width: `${data.assistant.progress}%` }} />
          </div>
          <button type="button">Resume Setup</button>
        </div>
      </div>
    </div>
  );
};

export default IntelligenceConnectorsPage;
