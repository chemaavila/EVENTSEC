import { useEffect, useState } from "react";
import ctiAdapter from "../../services/cti";
import type { CtiGraphData } from "../../services/cti";
import "../../components/cti/cti.css";

const IntelligenceGraphPage = () => {
  const [graph, setGraph] = useState<CtiGraphData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    ctiAdapter
      .getGraphData()
      .then((data) => {
        if (mounted) setGraph(data);
      })
      .catch((err) => {
        console.error(err);
        if (mounted) setError("Unable to load graph data.");
      });
    return () => {
      mounted = false;
    };
  }, []);

  if (!graph) {
    return (
      <div className="cti-graph-shell">
        <div className="cti-placeholder">
          <h1>Graph Explorer</h1>
          <p>{error ?? "Loading graph data..."}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="cti-graph-shell">
      <header className="cti-graph-topbar">
        <div className="cti-graph-topbar-left">
          <div className="cti-search-brand-icon" style={{ width: 32, height: 32 }}>
            <span className="material-symbols-outlined">hub</span>
          </div>
          <div className="cti-graph-title">
            <h2>Graph Explorer</h2>
            <span>Threat Intelligence | Case #4921</span>
          </div>
        </div>
        <div className="cti-graph-topbar-actions">
          <nav className="cti-graph-nav">
            <a href="/intelligence/dashboard">Dashboard</a>
            <a href="/alerts">Incidents</a>
            <a className="active" href="/intelligence/graph">
              Graph Explorer
            </a>
            <a href="/intelligence/search">Threat Intel</a>
            <a href="/intelligence/dashboard">Reports</a>
          </nav>
          <div className="cti-divider" />
          <button className="cti-graph-icon-button" type="button">
            <span className="material-symbols-outlined">notifications</span>
          </button>
          <button className="cti-graph-icon-button" type="button">
            <span className="material-symbols-outlined">settings</span>
          </button>
          <div className="cti-graph-avatar" title="User Profile" />
        </div>
      </header>

      <main className="cti-graph-body">
        <div className="cti-graph-canvas">
          <svg className="absolute inset-0 w-full h-full pointer-events-none" aria-hidden="true">
            {graph.edges.map((edge) => (
              <line
                key={edge.id}
                x1={edge.x1}
                y1={edge.y1}
                x2={edge.x2}
                y2={edge.y2}
                stroke={edge.color}
                strokeWidth={edge.width}
                strokeDasharray={edge.dashed ? "4 2" : undefined}
              />
            ))}
          </svg>

          {graph.nodes.map((node) => {
            const isCenter = node.id === "center";
            return (
              <div
                key={node.id}
                className={`cti-graph-node ${isCenter ? "center" : ""}`}
                style={{ left: node.x, top: node.y, color: node.textColor }}
              >
                <div
                  className="node-circle"
                  style={{
                    width: isCenter ? 64 : node.type === "malware" ? 56 : 48,
                    height: isCenter ? 64 : node.type === "malware" ? 56 : 48,
                    borderColor: node.borderColor,
                    color: node.textColor,
                  }}
                >
                  <span className="material-symbols-outlined" style={{ fontSize: isCenter ? 32 : 24 }}>
                    {node.icon}
                  </span>
                  {node.score ? <span className="node-score">{node.score}</span> : null}
                </div>
                <span className="node-label">{node.label}</span>
                {node.tooltip ? (
                  <div className="cti-graph-tooltip">
                    <div style={{ color: "#94a3b8" }}>{node.tooltip.subtitle}</div>
                    <div style={{ color: "#fff", fontWeight: 600 }}>{node.tooltip.title}</div>
                    <div style={{ color: node.tooltip.riskColor, marginTop: 4 }}>{node.tooltip.riskLabel}</div>
                  </div>
                ) : null}
              </div>
            );
          })}

          <div className="cti-graph-toolbar">
            <div className="toolbar-row">
              <div className="cti-graph-control">
                <div style={{ position: "relative" }}>
                  <span className="material-symbols-outlined search-icon">search</span>
                  <input placeholder="Search graph nodes..." />
                </div>
                <div className="cti-depth-group">
                  <span>Depth</span>
                  <div className="cti-depth-buttons">
                    <button className="active" type="button">
                      1
                    </button>
                    <button type="button">2</button>
                    <button type="button">3</button>
                  </div>
                </div>
              </div>

              <div className="cti-graph-control">
                <div className="cti-layout-buttons">
                  <button className="active" type="button">
                    <span className="material-symbols-outlined">hub</span>
                  </button>
                  <button type="button">
                    <span className="material-symbols-outlined">data_usage</span>
                  </button>
                  <button type="button">
                    <span className="material-symbols-outlined">account_tree</span>
                  </button>
                </div>
                <div className="cti-divider" />
                <button className="cti-graph-time" type="button">
                  <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
                    calendar_today
                  </span>
                  Last 24h
                  <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
                    arrow_drop_down
                  </span>
                </button>
              </div>

              <div className="cti-graph-slider">
                <span style={{ fontSize: 11, color: "#94a3b8" }}>Max Nodes</span>
                <div className="cti-graph-slider-track">
                  <div className="cti-graph-slider-thumb" />
                </div>
                <span style={{ fontSize: 12, fontFamily: "ui-monospace, monospace" }}>150</span>
              </div>
            </div>

            <div className="cti-filter-chips">
              <button className="cti-filter-chip primary" type="button">
                Rel: Connected To
                <span className="material-symbols-outlined" style={{ fontSize: 14 }}>
                  close
                </span>
              </button>
              <button className="cti-filter-chip" type="button">
                Type: Malware
                <span className="material-symbols-outlined" style={{ fontSize: 14 }}>
                  arrow_drop_down
                </span>
              </button>
              <button className="cti-filter-chip" type="button">
                Risk: High+
                <span className="material-symbols-outlined" style={{ fontSize: 14 }}>
                  arrow_drop_down
                </span>
              </button>
              <button className="cti-filter-chip add" type="button">
                <span className="material-symbols-outlined" style={{ fontSize: 14 }}>
                  add
                </span>
                Add Filter
              </button>
            </div>
          </div>

          <div className="cti-graph-legend">
            <h4>Legend</h4>
            <div className="cti-graph-legend-grid">
              <div className="cti-graph-legend-item">
                <span style={{ width: 10, height: 10, borderRadius: 999, background: "#e11d48", boxShadow: "0 0 8px rgba(225,29,72,0.5)" }} />
                Malicious
              </div>
              <div className="cti-graph-legend-item">
                <span style={{ width: 10, height: 10, borderRadius: 999, background: "#137fec" }} />
                Internal Asset
              </div>
              <div className="cti-graph-legend-item">
                <span style={{ width: 10, height: 10, borderRadius: 999, border: "1px solid #64748b" }} />
                External/Cloud
              </div>
              <div className="cti-graph-legend-item">
                <span style={{ width: 16, height: 2, background: "#64748b" }} />
                Standard Rel
              </div>
              <div className="cti-graph-legend-item">
                <span style={{ width: 16, height: 2, background: "#e11d48" }} />
                Attack Path
              </div>
            </div>
          </div>

          <div className="cti-graph-actions">
            <button className="cti-graph-action-button" type="button" title="Fit to Screen">
              <span className="material-symbols-outlined">center_focus_strong</span>
            </button>
            <button className="cti-graph-action-button" type="button" title="Export Snapshot">
              <span className="material-symbols-outlined">photo_camera</span>
            </button>
            <div className="cti-graph-zoom">
              <button type="button">
                <span className="material-symbols-outlined">add</span>
              </button>
              <button type="button">
                <span className="material-symbols-outlined">remove</span>
              </button>
            </div>
          </div>
        </div>

        <aside className="cti-graph-sidepanel">
          <div className="cti-graph-sidepanel-header">
            <div className="cti-graph-sidepanel-head">
              <div className="cti-graph-sidepanel-title">
                <div style={{ width: 40, height: 40, borderRadius: 8, background: "rgba(225,29,72,0.1)", border: "1px solid rgba(225,29,72,0.2)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <span className="material-symbols-outlined" style={{ color: "#e11d48", fontSize: 24 }}>
                    public
                  </span>
                </div>
                <div>
                  <div style={{ fontSize: 10, color: "#e11d48", textTransform: "uppercase", letterSpacing: "0.08em", fontWeight: 700 }}>
                    Selected Node
                  </div>
                  <h3>{graph.selectedNode.id}</h3>
                </div>
              </div>
              <button className="cti-graph-sidepanel-close" type="button">
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>
            <div className="cti-graph-risk">
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                <span style={{ fontSize: 12, color: "#94a3b8" }}>Risk Score</span>
                <span style={{ fontSize: 14, fontWeight: 700, color: "#e11d48" }}>
                  {graph.selectedNode.riskScore}
                </span>
              </div>
              <div className="cti-graph-risk-bar">
                <div className="cti-graph-risk-fill" />
              </div>
              <p style={{ fontSize: 10, color: "#94a3b8", marginTop: 8 }}>{graph.selectedNode.riskNote}</p>
            </div>
          </div>
          <div className="cti-graph-sidepanel-body">
            <div style={{ marginBottom: 24 }}>
              <h4 className="cti-graph-section-title">
                <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
                  info
                </span>
                Properties
              </h4>
              {graph.selectedNode.properties.map((prop) => (
                <div key={prop.label} className="cti-graph-property">
                  <label>{prop.label}</label>
                  <div className="cti-graph-property-value">
                    <span>{prop.value}</span>
                    {prop.copyable ? (
                      <button type="button">
                        <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
                          content_copy
                        </span>
                      </button>
                    ) : null}
                  </div>
                  <div className="cti-graph-property-divider" />
                </div>
              ))}
              <div className="cti-graph-property">
                <label>Location</label>
                <div className="cti-graph-property-value" style={{ justifyContent: "flex-start", gap: 8 }}>
                  <span className="cti-graph-flag" />
                  <span>{graph.selectedNode.location}</span>
                </div>
              </div>
            </div>

            <div style={{ marginBottom: 24 }}>
              <h4 className="cti-graph-section-title">
                <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
                  hub
                </span>
                Connections (3)
              </h4>
              <div style={{ display: "grid", gap: 8 }}>
                {graph.selectedNode.connections.map((connection) => (
                  <div key={connection.id} className="cti-graph-connection">
                    <span className="material-symbols-outlined" style={{ color: connection.iconColor, fontSize: 18 }}>
                      {connection.icon}
                    </span>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 12, color: "#fff" }}>{connection.label}</div>
                      <div style={{ fontSize: 10, color: "#94a3b8" }}>{connection.relation}</div>
                    </div>
                    <span className="material-symbols-outlined" style={{ fontSize: 16, color: "#64748b" }}>
                      chevron_right
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className="cti-graph-footer">
            <button className="primary" type="button">
              <span className="material-symbols-outlined" style={{ fontSize: 18, marginRight: 8 }}>
                add_moderator
              </span>
              Create Case
            </button>
            <div className="secondary-grid">
              <button className="secondary" type="button">
                <span className="material-symbols-outlined" style={{ fontSize: 16, marginRight: 6 }}>
                  auto_awesome
                </span>
                Enrich
              </button>
              <button className="secondary" type="button">
                <span className="material-symbols-outlined" style={{ fontSize: 16, marginRight: 6 }}>
                  pivot_table_chart
                </span>
                Pivot
              </button>
            </div>
          </div>
        </aside>
      </main>
    </div>
  );
};

export default IntelligenceGraphPage;
