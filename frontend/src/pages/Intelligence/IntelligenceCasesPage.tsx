import { useEffect, useState } from "react";
import CtiAdapterFallback from "../../components/cti/CtiAdapterFallback";
import ctiAdapter from "../../services/cti";
import { CtiNotImplementedError } from "../../services/cti/apiAdapter";
import type { CtiCasesData } from "../../services/cti";
import "../../components/cti/cti.css";

const statusClassMap = {
  open: "cti-cases-status open",
  "in-progress": "cti-cases-status in-progress",
  closed: "cti-cases-status closed",
};

const IntelligenceCasesPage = () => {
  const [data, setData] = useState<CtiCasesData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [adapterUnavailable, setAdapterUnavailable] = useState(false);

  useEffect(() => {
    let mounted = true;
    ctiAdapter
      .getCases()
      .then((response) => {
        if (mounted) setData(response);
      })
      .catch((err) => {
        console.error(err);
        if (mounted && err instanceof CtiNotImplementedError) {
          setAdapterUnavailable(true);
          return;
        }
        if (mounted) setError("Unable to load cases.");
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
      <div className="cti-cases-shell">
        <div className="cti-placeholder">
          <h1>Cases</h1>
          <p>{error ?? "Loading cases..."}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="cti-cases-shell">
      <header className="cti-cases-topbar">
        <div className="cti-cases-topbar-left">
          <div className="cti-cases-logo">
            <svg viewBox="0 0 48 48" aria-hidden="true">
              <path
                d="M13.8261 17.4264C16.7203 18.1174 20.2244 18.5217 24 18.5217C27.7756 18.5217 31.2797 18.1174 34.1739 17.4264C36.9144 16.7722 39.9967 15.2331 41.3563 14.1648L24.8486 40.6391C24.4571 41.267 23.5429 41.267 23.1514 40.6391L6.64374 14.1648C8.00331 15.2331 11.0856 16.7722 13.8261 17.4264Z"
                fill="currentColor"
              />
              <path
                clipRule="evenodd"
                d="M39.998 12.236C39.9944 12.2537 39.9875 12.2845 39.9748 12.3294C39.9436 12.4399 39.8949 12.5741 39.8346 12.7175C39.8168 12.7597 39.7989 12.8007 39.7813 12.8398C38.5103 13.7113 35.9788 14.9393 33.7095 15.4811C30.9875 16.131 27.6413 16.5217 24 16.5217C20.3587 16.5217 17.0125 16.131 14.2905 15.4811C12.0012 14.9346 9.44505 13.6897 8.18538 12.8168C8.17384 12.7925 8.16216 12.767 8.15052 12.7408C8.09919 12.6249 8.05721 12.5114 8.02977 12.411C8.00356 12.3152 8.00039 12.2667 8.00004 12.2612C8.00004 12.261 8 12.2607 8.00004 12.2612C8.00004 12.2359 8.0104 11.9233 8.68485 11.3686C9.34546 10.8254 10.4222 10.2469 11.9291 9.72276C14.9242 8.68098 19.1919 8 24 8C28.8081 8 33.0758 8.68098 36.0709 9.72276C37.5778 10.2469 38.6545 10.8254 39.3151 11.3686C39.9006 11.8501 39.9857 12.1489 39.998 12.236ZM4.95178 15.2312L21.4543 41.6973C22.6288 43.5809 25.3712 43.5809 26.5457 41.6973L43.0534 15.223C43.0709 15.1948 43.0878 15.1662 43.104 15.1371L41.3563 14.1648C43.104 15.1371 43.1038 15.1374 43.104 15.1371L43.1051 15.135L43.1065 15.1325L43.1101 15.1261L43.1199 15.1082C43.1276 15.094 43.1377 15.0754 43.1497 15.0527C43.1738 15.0075 43.2062 14.9455 43.244 14.8701C43.319 14.7208 43.4196 14.511 43.5217 14.2683C43.6901 13.8679 44 13.0689 44 12.2609C44 10.5573 43.003 9.22254 41.8558 8.2791C40.6947 7.32427 39.1354 6.55361 37.385 5.94477C33.8654 4.72057 29.133 4 24 4C18.867 4 14.1346 4.72057 10.615 5.94478C8.86463 6.55361 7.30529 7.32428 6.14419 8.27911C4.99695 9.22255 3.99999 10.5573 3.99999 12.2609C3.99999 13.1275 4.29264 13.9078 4.49321 14.3607C4.60375 14.6102 4.71348 14.8196 4.79687 14.9689C4.83898 15.0444 4.87547 15.1065 4.9035 15.1529C4.91754 15.1762 4.92954 15.1957 4.93916 15.2111L4.94662 15.223L4.95178 15.2312ZM35.9868 18.996L24 38.22L12.0131 18.996C12.4661 19.1391 12.9179 19.2658 13.3617 19.3718C16.4281 20.1039 20.0901 20.5217 24 20.5217C27.9099 20.5217 31.5719 20.1039 34.6383 19.3718C35.082 19.2658 35.5339 19.1391 35.9868 18.996Z"
                fill="currentColor"
                fillRule="evenodd"
              />
            </svg>
          </div>
          <h1>Consola SIEM</h1>
          <div className="cti-cases-tabs">
            {[
              { label: "Dashboard", active: false },
              { label: "Cases", active: true },
              { label: "Alerts", active: false },
              { label: "Intelligence", active: false },
            ].map((tab) => (
              <a key={tab.label} className={tab.active ? "active" : ""} href="#">
                {tab.label}
              </a>
            ))}
          </div>
        </div>
        <div className="cti-cases-topbar-right">
          <div className="cti-cases-search">
            <span className="material-symbols-outlined">search</span>
            <input placeholder="Search cases, entities..." />
          </div>
          <button type="button">
            <span className="material-symbols-outlined">notifications</span>
            <span className="cti-cases-dot" />
          </button>
          <div className="cti-cases-avatar" />
        </div>
      </header>

      <main className="cti-cases-body">
        <section className="cti-cases-list">
          <div className="cti-cases-header">
            <div>
              <div className="cti-cases-crumbs">
                <span>Operations</span>
                <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
                  chevron_right
                </span>
                <span className="current">Cases</span>
              </div>
              <h2>Case Management</h2>
              <p>Manage, investigate, and resolve security incidents.</p>
            </div>
            <button className="primary" type="button">
              <span className="material-symbols-outlined">add</span>
              Create New Case
            </button>
          </div>

          <div className="cti-cases-filters">
            <button type="button">
              <span className="material-symbols-outlined">filter_list</span>
              Filter
            </button>
            <div className="divider" />
            <button className="chip active" type="button">
              Status: Open
              <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
                close
              </span>
            </button>
            <button className="chip" type="button">
              Severity
              <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
                expand_more
              </span>
            </button>
            <button className="chip" type="button">
              Assigned To
              <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
                expand_more
              </span>
            </button>
            <div className="cti-cases-count">Showing 1-15 of 42 cases</div>
          </div>

          <div className="cti-cases-table">
            <table>
              <thead>
                <tr>
                  <th>Case Details</th>
                  <th>Status</th>
                  <th>Severity</th>
                  <th>Assigned To</th>
                  <th style={{ textAlign: "center" }}>Entities</th>
                  <th style={{ textAlign: "right" }}>Last Updated</th>
                </tr>
              </thead>
              <tbody>
                {data.cases.map((caseItem) => (
                  <tr key={caseItem.id} className={caseItem.selected ? "selected" : undefined}>
                    <td>
                      <div className="cti-cases-details">
                        <span className={caseItem.selected ? "id active" : "id"}>{caseItem.id}</span>
                        <span className="title">{caseItem.title}</span>
                      </div>
                    </td>
                    <td>
                      <span className={statusClassMap[caseItem.statusStyle]}>{caseItem.status}</span>
                    </td>
                    <td>
                      <div className="cti-cases-severity">
                        <span className="dot" style={{ background: caseItem.severityColor }} />
                        {caseItem.severity}
                      </div>
                    </td>
                    <td>
                      <div className="cti-cases-assignee">
                        {caseItem.assigneeAvatar ? (
                          <div
                            className="avatar"
                            style={{ backgroundImage: `url('${caseItem.assigneeAvatar}')` }}
                          />
                        ) : (
                          <div className="avatar initials">{caseItem.assigneeInitials}</div>
                        )}
                        <span className={caseItem.assignee === "Unassigned" ? "muted" : undefined}>
                          {caseItem.assignee}
                        </span>
                      </div>
                    </td>
                    <td style={{ textAlign: "center" }}>
                      <span className="cti-cases-entities">
                        <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
                          link
                        </span>
                        {caseItem.entities}
                      </span>
                    </td>
                    <td style={{ textAlign: "right" }} className="muted">
                      {caseItem.lastUpdated}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <aside className="cti-cases-detail">
          <div className="cti-cases-detail-header">
            <div>
              <div className="cti-cases-detail-badges">
                <span className="cti-cases-detail-id">{data.detail.id}</span>
                <span className="cti-cases-detail-severity">{data.detail.severity}</span>
              </div>
              <h3>{data.detail.title}</h3>
            </div>
            <button type="button">
              <span className="material-symbols-outlined">close</span>
            </button>
            <div className="cti-cases-detail-actions">
              <button type="button">
                <span className="material-symbols-outlined">picture_as_pdf</span>
                Export Report
              </button>
              <button type="button" className="icon">
                <span className="material-symbols-outlined">edit</span>
              </button>
              <button type="button" className="icon">
                <span className="material-symbols-outlined">share</span>
              </button>
            </div>
          </div>

          <div className="cti-cases-detail-body">
            <div className="cti-cases-tabs-detail">
              <button className="active" type="button">
                Overview
              </button>
              <button type="button">Intelligence Graph</button>
              <button type="button">Artifacts</button>
            </div>

            <div className="cti-cases-detail-content">
              <section>
                <div className="cti-cases-section-header">
                  <h4>Response Checklist</h4>
                  <span>{data.detail.checklistProgress}</span>
                </div>
                <div className="cti-cases-checklist">
                  {data.detail.checklist.map((item) => (
                    <label key={item.id} className={item.completed ? "completed" : undefined}>
                      <input type="checkbox" checked={item.completed} readOnly />
                      <div>
                        <span>{item.text}</span>
                        {item.note ? <small>{item.note}</small> : null}
                      </div>
                    </label>
                  ))}
                </div>
              </section>

              <section>
                <h4>Linked CTI Objects</h4>
                <div className="cti-cases-graph">
                  <div className="cti-cases-graph-node">
                    <span className="material-symbols-outlined">dns</span>
                    <span className="label">SRV-01</span>
                  </div>
                  <div className="cti-cases-graph-node secondary">
                    <span className="material-symbols-outlined">public</span>
                    <span className="label">192.168.x.x</span>
                  </div>
                  <div className="cti-cases-graph-link" />
                  <div className="cti-cases-graph-footer">View Full Graph</div>
                </div>
              </section>

              <section>
                <h4>Activity Timeline</h4>
                <div className="cti-cases-timeline">
                  {data.detail.timeline.map((item) => (
                    <div
                      key={item.id}
                      className={`cti-cases-timeline-item ${item.highlight ? "highlight" : item.critical ? "critical" : ""}`}
                    >
                      <div className="dot" />
                      <div className="content">
                        <div className="meta">
                          <span className="author">
                            {item.system ? (
                              <>
                                <span className="material-symbols-outlined">smart_toy</span>
                                System
                              </>
                            ) : (
                              item.author
                            )}
                          </span>
                          <span className="time">{item.time}</span>
                        </div>
                        <div className={item.system ? "system" : "note"}>{item.content}</div>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="cti-cases-note">
                  <div className="avatar" />
                  <input placeholder="Add a note or comment..." />
                </div>
              </section>
            </div>
          </div>
        </aside>
      </main>
    </div>
  );
};

export default IntelligenceCasesPage;
