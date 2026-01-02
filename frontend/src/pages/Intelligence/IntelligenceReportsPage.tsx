import { useEffect, useState } from "react";
import CtiAdapterFallback from "../../components/cti/CtiAdapterFallback";
import ctiAdapter from "../../services/cti";
import { CtiNotImplementedError } from "../../services/cti/apiAdapter";
import type { CtiReportsData } from "../../services/cti";
import "../../components/cti/cti.css";

const IntelligenceReportsPage = () => {
  const [data, setData] = useState<CtiReportsData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [adapterUnavailable, setAdapterUnavailable] = useState(false);

  useEffect(() => {
    let mounted = true;
    ctiAdapter
      .getReports()
      .then((response) => {
        if (mounted) setData(response);
      })
      .catch((err) => {
        console.error(err);
        if (mounted && err instanceof CtiNotImplementedError) {
          setAdapterUnavailable(true);
          return;
        }
        if (mounted) setError("Unable to load reports.");
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
      <div className="cti-reports-shell">
        <div className="cti-placeholder">
          <h1>Reports</h1>
          <p>{error ?? "Loading reports..."}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="cti-reports-shell">
      <aside className="cti-reports-sidebar">
        <div className="cti-reports-sidebar-header">
          <div className="cti-reports-logo" />
          <div>
            <div className="cti-reports-title">SIEM Console</div>
            <div className="cti-reports-subtitle">Analyst View</div>
          </div>
        </div>
        <nav className="cti-reports-nav">
          {["Dashboard", "Alerts", "Reports", "Cases", "Settings"].map((item) => (
            <a key={item} className={`cti-reports-link ${item === "Reports" ? "active" : ""}`} href="#">
              <span className="material-symbols-outlined">
                {item === "Dashboard"
                  ? "dashboard"
                  : item === "Alerts"
                  ? "notifications"
                  : item === "Reports"
                  ? "description"
                  : item === "Cases"
                  ? "work"
                  : "settings"}
              </span>
              <span>{item}</span>
            </a>
          ))}
        </nav>
        <div className="cti-reports-user">
          <div className="cti-reports-user-avatar" />
          <div>
            <div className="cti-reports-user-name">Alex Morgan</div>
            <div className="cti-reports-user-role">SOC Analyst L2</div>
          </div>
        </div>
      </aside>

      <main className="cti-reports-main">
        <header className="cti-reports-topbar">
          <div>
            <div className="cti-reports-breadcrumbs">
              <a href="/intelligence/dashboard">Home</a>
              <span>/</span>
              <span>Reports</span>
            </div>
            <h2>Threat Intelligence</h2>
          </div>
          <div className="cti-reports-topbar-actions">
            <div className="cti-reports-search">
              <span className="material-symbols-outlined">search</span>
              <input placeholder="Search reports..." />
            </div>
            <button type="button">
              <span className="material-symbols-outlined">help</span>
            </button>
          </div>
        </header>

        <div className="cti-reports-toolbar">
          <div className="cti-reports-toolbar-left">
            <button type="button">
              <span className="material-symbols-outlined">filter_list</span>
              Filter
            </button>
            <button type="button">
              <span className="material-symbols-outlined">calendar_today</span>
              Last 7 Days
            </button>
          </div>
          <button className="primary" type="button">
            <span className="material-symbols-outlined">add</span>
            Add Manual Report
          </button>
        </div>

        <div className="cti-reports-content">
          <div className="cti-reports-table">
            <div className="cti-reports-table-body">
              <table>
                <thead>
                  <tr>
                    <th>Source</th>
                    <th>Report Name</th>
                    <th>Markers</th>
                    <th>Created</th>
                    <th style={{ textAlign: "right" }}>Objects</th>
                  </tr>
                </thead>
                <tbody>
                  {data.reports.map((report) => (
                    <tr key={report.id} className={report.selected ? "selected" : undefined}>
                      <td>
                        <div className="cti-reports-source">
                          <div className="cti-reports-status" />
                          <div className="cti-reports-source-label">
                            <span className="material-symbols-outlined">{report.sourceIcon}</span>
                            {report.source}
                          </div>
                        </div>
                      </td>
                      <td>
                        <div className="cti-reports-name">
                          <div>{report.title}</div>
                          <div className="cti-reports-summary">{report.summary}</div>
                        </div>
                      </td>
                      <td>
                        <div className="cti-reports-markers">
                          {report.markers.map((marker) => (
                            <span key={marker.label} style={{ background: marker.color, color: marker.textColor }}>
                              {marker.label}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="muted">{report.createdAt}</td>
                      <td style={{ textAlign: "right" }}>
                        <span className="cti-reports-objects">{report.objects}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="cti-reports-pagination">
              <span>Showing 1-5 of 128 reports</span>
              <div className="cti-reports-pagination-buttons">
                <button type="button">
                  <span className="material-symbols-outlined">chevron_left</span>
                </button>
                <button type="button">
                  <span className="material-symbols-outlined">chevron_right</span>
                </button>
              </div>
            </div>
          </div>

          <aside className="cti-reports-detail">
            <div className="cti-reports-detail-header">
              <div className="cti-reports-detail-title">
                <div className="cti-reports-detail-icon">
                  <span className="material-symbols-outlined filled">report</span>
                </div>
                <div>
                  <h3>{data.detail.title}</h3>
                  <div className="cti-reports-detail-meta">
                    <span>ID: {data.detail.id}</span>
                    <span>•</span>
                    <a href="#">View Source</a>
                  </div>
                </div>
              </div>
              <button type="button">
                <span className="material-symbols-outlined">close</span>
              </button>
              <div className="cti-reports-detail-actions">
                <button className="primary" type="button">
                  <span className="material-symbols-outlined">play_arrow</span>
                  Run Extraction
                </button>
                <button type="button">
                  <span className="material-symbols-outlined">add_box</span>
                  Create Case
                </button>
              </div>
            </div>

            <div className="cti-reports-detail-body">
              <section>
                <h4>
                  <span className="material-symbols-outlined">summarize</span>
                  Summary
                </h4>
                <p>{data.detail.summary}</p>
              </section>

              <section>
                <div className="cti-reports-section-header">
                  <h4>
                    <span className="material-symbols-outlined">data_object</span>
                    Extracted Observables
                  </h4>
                  <span className="cti-reports-pill">{data.detail.observablesCount} Found</span>
                </div>
                <div className="cti-reports-observables">
                  {data.detail.observables.map((obs) => (
                    <div key={obs.id} className="cti-reports-observable">
                      <div className="cti-reports-observable-main">
                        <span className="material-symbols-outlined" style={{ color: obs.color }}>
                          {obs.icon}
                        </span>
                        <div>
                          <div className="value">{obs.value}</div>
                          <div className="type">{obs.type}</div>
                        </div>
                      </div>
                      <div className="cti-reports-observable-actions">
                        <button type="button">
                          <span className="material-symbols-outlined">content_copy</span>
                        </button>
                        <button type="button">
                          <span className="material-symbols-outlined">search</span>
                        </button>
                      </div>
                    </div>
                  ))}
                  <div className="cti-reports-observable-footer">
                    <button type="button">View All {data.detail.observablesCount} Observables</button>
                  </div>
                </div>
              </section>

              <section>
                <h4>
                  <span className="material-symbols-outlined">hub</span>
                  Relationships
                </h4>
                <div className="cti-reports-relationships">
                  {data.detail.relationships.map((rel) => (
                    <div key={rel.id} className="cti-reports-relationship">
                      <div className="cti-reports-relationship-icon" style={{ color: rel.color }}>
                        <span className="material-symbols-outlined">{rel.icon}</span>
                      </div>
                      <div>
                        <div className="label">{rel.label}</div>
                        <div className="value">{rel.value}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            </div>

            <div className="cti-reports-detail-footer">
              <span>{data.detail.ingested}</span>
              <span>{data.detail.updated}</span>
            </div>
          </aside>
        </div>
      </main>
    </div>
  );
};

export default IntelligenceReportsPage;
