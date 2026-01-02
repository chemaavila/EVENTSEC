import { useEffect, useState } from "react";
import CtiAdapterFallback from "../../components/cti/CtiAdapterFallback";
import ctiAdapter from "../../services/cti";
import { CtiNotImplementedError } from "../../services/cti/apiAdapter";
import type { CtiIndicatorsData, CtiIndicatorRow } from "../../services/cti";
import "../../components/cti/cti.css";

const statusLabelMap: Record<CtiIndicatorRow["enrichmentStatus"], string> = {
  complete: "Complete",
  enriching: "Enriching",
  failed: "Failed",
};

const IntelligenceIndicatorsPage = () => {
  const [data, setData] = useState<CtiIndicatorsData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [adapterUnavailable, setAdapterUnavailable] = useState(false);

  useEffect(() => {
    let mounted = true;
    ctiAdapter
      .getIndicatorsHub()
      .then((response) => {
        if (mounted) setData(response);
      })
      .catch((err) => {
        console.error(err);
        if (mounted && err instanceof CtiNotImplementedError) {
          setAdapterUnavailable(true);
          return;
        }
        if (mounted) setError("Unable to load indicators hub data.");
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
      <div className="cti-indicators-shell">
        <div className="cti-placeholder">
          <h1>Indicators &amp; Observables</h1>
          <p>{error ?? "Loading indicators hub..."}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="cti-indicators-shell">
      <aside className="cti-indicators-sidebar">
        <div className="cti-indicators-sidebar-inner">
          <div className="cti-indicators-logo">
            <div className="cti-indicators-logo-mark">C</div>
            <h1 style={{ fontSize: 16, fontWeight: 700 }}>Consola SIEM/XDR</h1>
          </div>
          <div className="cti-indicators-nav">
            {["Dashboard", "Incidents", "Threat Intelligence", "Hunting", "Settings"].map((item) => (
              <div
                key={item}
                className={`cti-indicators-nav-item ${item === "Threat Intelligence" ? "active" : ""}`}
              >
                <span className="material-symbols-outlined" style={{ fontSize: 24 }}>
                  {item === "Dashboard"
                    ? "dashboard"
                    : item === "Incidents"
                    ? "warning"
                    : item === "Threat Intelligence"
                    ? "database"
                    : item === "Hunting"
                    ? "atr"
                    : "settings"}
                </span>
                <span style={{ fontSize: 14, fontWeight: 500 }}>{item}</span>
              </div>
            ))}
          </div>
          <div className="cti-indicators-user">
            <div style={{ width: 32, height: 32, borderRadius: 999, background: "linear-gradient(90deg,#374151,#4b5563)" }} />
            <div>
              <div style={{ fontSize: 14, fontWeight: 600, color: "#fff" }}>Analyst Jane</div>
              <div style={{ fontSize: 12, color: "#6b7280" }}>SOC Level 2</div>
            </div>
          </div>
        </div>
      </aside>

      <div className="cti-indicators-main">
        <header className="cti-indicators-topbar">
          <div className="cti-indicators-breadcrumbs">
            <a href="/intelligence/dashboard">Home</a>
            <span>/</span>
            <a href="/intelligence/dashboard">Threat Intelligence</a>
            <span>/</span>
            <span style={{ color: "#fff", fontWeight: 500 }}>Indicators &amp; Observables</span>
          </div>
          <div className="cti-indicators-actions">
            <button type="button" aria-label="Search">
              <span className="material-symbols-outlined" style={{ fontSize: 20 }}>
                search
              </span>
            </button>
            <button type="button" aria-label="Notifications" style={{ position: "relative" }}>
              <span className="material-symbols-outlined" style={{ fontSize: 20 }}>
                notifications
              </span>
              <span
                style={{
                  position: "absolute",
                  top: 6,
                  right: 6,
                  width: 8,
                  height: 8,
                  borderRadius: 999,
                  background: "#ef4444",
                  border: "1px solid #111418",
                }}
              />
            </button>
            <button type="button" aria-label="Help">
              <span className="material-symbols-outlined" style={{ fontSize: 20 }}>
                help
              </span>
            </button>
          </div>
        </header>

        <main className="cti-indicators-content">
          <div className="cti-indicators-center">
            <div className="cti-indicators-header">
              <div>
                <h2>Indicators &amp; Observables Hub</h2>
                <p>
                  Centralized management for threat intelligence artifacts. Review raw observables, enrich data, and
                  promote confirmed threats to indicators.
                </p>
              </div>
              <div className="cti-indicators-header-actions">
                <button className="cti-indicators-button" type="button">
                  <span className="material-symbols-outlined" style={{ fontSize: 20 }}>
                    upload
                  </span>
                  Import STIX/TAXII
                </button>
                <button className="cti-indicators-button primary" type="button">
                  <span className="material-symbols-outlined" style={{ fontSize: 20 }}>
                    add
                  </span>
                  Add Observable
                </button>
              </div>
            </div>

            <div className="cti-indicators-search-row">
              <div className="cti-indicators-toggle">
                <button className="active" type="button">
                  Observables <span style={{ background: "rgba(255,255,255,0.2)", padding: "2px 6px", borderRadius: 6, fontSize: 12 }}>{data.observablesCount}</span>
                </button>
                <button type="button">
                  Indicators <span style={{ background: "#283039", padding: "2px 6px", borderRadius: 6, fontSize: 12, color: "#d1d5db" }}>{data.indicatorsCount}</span>
                </button>
              </div>
              <div style={{ position: "relative" }}>
                <span className="material-symbols-outlined cti-indicators-search-icon">search</span>
                <input placeholder="Search by value, type, tag (e.g. type:ipv4 AND risk>80)..." />
              </div>
              <button className="cti-indicators-icon-button" type="button" title="Filter">
                <span className="material-symbols-outlined" style={{ fontSize: 20 }}>
                  filter_list
                </span>
              </button>
              <button className="cti-indicators-icon-button" type="button" title="Export">
                <span className="material-symbols-outlined" style={{ fontSize: 20 }}>
                  download
                </span>
              </button>
            </div>

            <div className="cti-indicators-action-bar">
              <div style={{ display: "flex", alignItems: "center", gap: 8, color: "#60a5fa", fontWeight: 500 }}>
                <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
                  check_box
                </span>
                1 Selected
              </div>
              <div style={{ width: 1, height: 16, background: "#283039" }} />
              <div style={{ display: "flex", gap: 8 }}>
                {[
                  { icon: "auto_awesome", label: "Enrich" },
                  { icon: "publish", label: "Promote" },
                  { icon: "label", label: "Tag" },
                ].map((action) => (
                  <button key={action.label} type="button">
                    <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
                      {action.icon}
                    </span>
                    {action.label}
                  </button>
                ))}
                <button type="button" style={{ color: "#f87171" }}>
                  <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
                    delete
                  </span>
                  Delete
                </button>
              </div>
            </div>

            <div className="cti-indicators-table" style={{ height: "100%" }}>
              <div style={{ overflow: "auto", flex: 1 }}>
                <table>
                  <thead>
                    <tr>
                      <th style={{ width: 48 }}>
                        <input type="checkbox" className="cti-checkbox" />
                      </th>
                      <th>Value</th>
                      <th>Type</th>
                      <th>Last Seen</th>
                      <th>Enrichment</th>
                      <th style={{ width: 200 }}>Risk Score</th>
                      <th style={{ width: 48 }} />
                    </tr>
                  </thead>
                  <tbody>
                    {data.rows.map((row) => (
                      <tr key={row.id} className={`cti-indicators-row ${row.selected ? "selected" : ""}`}>
                        <td>
                          <input type="checkbox" className="cti-checkbox" checked={row.selected} readOnly />
                        </td>
                        <td>
                          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                            <span style={{ fontFamily: "JetBrains Mono, monospace" }}>{row.value}</span>
                            {row.selected ? (
                              <span className="material-symbols-outlined" style={{ fontSize: 16, color: "var(--cti-primary)" }}>
                                content_copy
                              </span>
                            ) : null}
                          </div>
                        </td>
                        <td>
                          <span className="cti-indicators-pill">
                            <span className="material-symbols-outlined" style={{ fontSize: 14 }}>
                              {row.typeIcon}
                            </span>
                            {row.typeLabel}
                          </span>
                        </td>
                        <td style={{ color: "#d1d5db" }}>{row.lastSeen}</td>
                        <td>
                          <span className={`cti-indicators-status ${row.enrichmentStatus}`}>
                            <span
                              style={{
                                width: 6,
                                height: 6,
                                borderRadius: 999,
                                background:
                                  row.enrichmentStatus === "complete"
                                    ? "#34d399"
                                    : row.enrichmentStatus === "enriching"
                                    ? "#fbbf24"
                                    : "#f87171",
                              }}
                            />
                            {statusLabelMap[row.enrichmentStatus]}
                          </span>
                        </td>
                        <td>
                          {row.riskScore ? (
                            <div className="cti-indicators-risk">
                              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12 }}>
                                <span style={{ color: row.riskSeverity === "low" ? "#34d399" : "#f87171", fontWeight: 700 }}>
                                  {row.riskLabel}
                                </span>
                                <span style={{ color: "#9ca3af" }}>{row.riskScore}/100</span>
                              </div>
                              <div className="bar">
                                <span
                                  style={{
                                    width: `${row.riskScore}%`,
                                    background:
                                      row.riskSeverity === "critical"
                                        ? "#dc2626"
                                        : row.riskSeverity === "low"
                                        ? "#10b981"
                                        : "#ef4444",
                                  }}
                                />
                              </div>
                            </div>
                          ) : (
                            <span style={{ fontSize: 12, color: "#9ca3af" }}>
                              {row.enrichmentStatus === "enriching" ? "Pending..." : "N/A"}
                            </span>
                          )}
                        </td>
                        <td style={{ textAlign: "right" }}>
                          <button type="button" style={{ color: "#6b7280" }}>
                            <span className="material-symbols-outlined">more_vert</span>
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="cti-indicators-pagination">
                <span>Showing 1-25 of 12,402</span>
                <div style={{ display: "flex", gap: 8 }}>
                  <button type="button">
                    <span className="material-symbols-outlined">chevron_left</span>
                  </button>
                  <button type="button">
                    <span className="material-symbols-outlined">chevron_right</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <aside className="cti-indicators-drawer">
            <div className="cti-indicators-drawer-header">
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span className="material-symbols-outlined" style={{ color: "var(--cti-primary)" }}>
                  lan
                </span>
                <span style={{ fontSize: 18, fontWeight: 700 }}>{data.drawer.id}</span>
              </div>
              <button type="button" style={{ color: "#9ca3af" }}>
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>
            <div className="cti-indicators-drawer-body">
              <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 16 }}>
                <div className="cti-indicators-card">
                  <div style={{ fontSize: 12, color: "#9ca3af", marginBottom: 4 }}>Risk Score</div>
                  <div style={{ display: "flex", alignItems: "flex-end", gap: 8 }}>
                    <span style={{ fontSize: 24, fontWeight: 700, color: "#f87171" }}>{data.drawer.riskScore}</span>
                    <span style={{ fontSize: 12, color: "#f87171" }}>{data.drawer.riskLabel}</span>
                  </div>
                </div>
                <div className="cti-indicators-card">
                  <div style={{ fontSize: 12, color: "#9ca3af", marginBottom: 4 }}>Confidence</div>
                  <div style={{ display: "flex", alignItems: "flex-end", gap: 8 }}>
                    <span style={{ fontSize: 24, fontWeight: 700 }}>{data.drawer.confidence}</span>
                    <span style={{ fontSize: 12, color: "#9ca3af" }}>High</span>
                  </div>
                </div>
              </div>

              <div>
                <h3 style={{ fontSize: 12, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 8 }}>
                  Metadata
                </h3>
                <div className="cti-indicators-metadata">
                  {[
                    { label: "First Seen", value: data.drawer.firstSeen },
                    { label: "Last Seen", value: data.drawer.lastSeen },
                    { label: "Source", value: data.drawer.source },
                    { label: "Country", value: `🇷🇺 ${data.drawer.country}` },
                  ].map((item) => (
                    <div key={item.label} className="cti-indicators-metadata-row">
                      <span style={{ color: "#9ca3af" }}>{item.label}</span>
                      <span style={{ color: "#fff" }}>{item.value}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h3 style={{ fontSize: 12, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 8 }}>
                  Tags
                </h3>
                <div className="cti-indicators-tags">
                  {data.drawer.tags.map((tag) => (
                    <span key={tag} className={`cti-indicators-tag ${tag === "#botnet" ? "critical" : ""}`}>
                      {tag}
                    </span>
                  ))}
                  <button className="cti-indicators-tag" type="button" style={{ borderStyle: "dashed", color: "#6b7280" }}>
                    + Add
                  </button>
                </div>
              </div>

              <div>
                <h3 style={{ fontSize: 12, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 8 }}>
                  Related Incidents
                </h3>
                {data.drawer.incidents.map((incident) => (
                  <div key={incident.id} className="cti-indicators-incident">
                    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                      <span className="material-symbols-outlined" style={{ fontSize: 16, color: "#ef4444" }}>
                        warning
                      </span>
                      <span style={{ fontWeight: 600, color: "#fff" }}>{incident.id}</span>
                    </div>
                    <p style={{ fontSize: 12, color: "#9ca3af" }}>{incident.summary}</p>
                  </div>
                ))}
              </div>
            </div>
            <div className="cti-indicators-drawer-footer">
              <button className="primary" type="button">
                <span className="material-symbols-outlined" style={{ fontSize: 20 }}>
                  publish
                </span>
                Promote to Indicator
              </button>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 12 }}>
                <button type="button">
                  <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
                    auto_awesome
                  </span>
                  Re-Enrich
                </button>
                <button type="button">
                  <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
                    visibility_off
                  </span>
                  Ignore
                </button>
              </div>
            </div>
          </aside>
        </main>
      </div>
    </div>
  );
};

export default IntelligenceIndicatorsPage;
