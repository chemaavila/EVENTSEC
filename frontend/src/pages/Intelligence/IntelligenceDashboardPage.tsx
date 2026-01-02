import { useCallback, useEffect, useMemo, useState } from "react";
import { NavLink } from "react-router-dom";
import CtiAdapterFallback from "../../components/cti/CtiAdapterFallback";
import ctiAdapter from "../../services/cti";
import { CtiNotImplementedError } from "../../services/cti/apiAdapter";
import type { CtiDashboardData, CtiKpi, CtiStreamEvent } from "../../services/cti";
import "../../components/cti/cti.css";

const trendIcon = (direction: CtiKpi["trend"]["direction"]) => {
  if (direction === "up") return "trending_up";
  if (direction === "down") return "trending_down";
  return "remove";
};

const trendClass = (direction: CtiKpi["trend"]["direction"]) => {
  if (direction === "up") return "cti-trend-up";
  if (direction === "down") return "cti-trend-down";
  return "cti-trend-flat";
};

const IntelligenceDashboardPage = () => {
  const [dashboard, setDashboard] = useState<CtiDashboardData | null>(null);
  const [streamEvents, setStreamEvents] = useState<CtiStreamEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [adapterUnavailable, setAdapterUnavailable] = useState(false);

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await ctiAdapter.getDashboard();
      setDashboard(data);
      setStreamEvents(data.streamEvents);
    } catch (err) {
      console.error(err);
      if (err instanceof CtiNotImplementedError) {
        setAdapterUnavailable(true);
        return;
      }
      setError("Unable to load threat intelligence dashboard data.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  useEffect(() => {
    if (!dashboard) return undefined;
    const unsubscribe = ctiAdapter.subscribeStreamEvents((event) => {
      setStreamEvents((prev) => [event, ...prev].slice(0, 6));
    });
    return unsubscribe;
  }, [dashboard]);

  const kpis = dashboard?.kpis ?? [];
  const recentIntel = dashboard?.recentIntel ?? [];
  const topTechniques = dashboard?.topTechniques ?? [];

  const streamContent = useMemo(() => {
    if (loading) {
      return (
        <div className="cti-stream-list">
          {Array.from({ length: 3 }).map((_, index) => (
            <div key={`stream-skeleton-${index}`} className="cti-stream-item">
              <div className="cti-skeleton" style={{ width: 36, height: 36 }} />
              <div style={{ flex: 1, display: "grid", gap: 8 }}>
                <div className="cti-skeleton" style={{ height: 12, width: "80%" }} />
                <div className="cti-skeleton" style={{ height: 10, width: "40%" }} />
              </div>
              <div className="cti-skeleton" style={{ width: 64, height: 10 }} />
            </div>
          ))}
        </div>
      );
    }

    if (streamEvents.length === 0) {
      return <div className="cti-empty">No stream events yet.</div>;
    }

    return (
      <div className="cti-stream-list">
        {streamEvents.map((event) => (
          <div key={event.id} className="cti-stream-item">
            <div
              className="cti-stream-icon"
              style={{ background: event.iconBackground, color: event.iconColor }}
            >
              <span className="material-symbols-outlined">{event.icon}</span>
            </div>
            <div className="cti-stream-message">{event.message}</div>
            <div className="cti-stream-time">{event.timestamp}</div>
          </div>
        ))}
      </div>
    );
  }, [loading, streamEvents]);

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

  return (
    <div className="cti-shell">
      <aside className="cti-sidebar">
        <div className="cti-sidebar-content">
          <div className="cti-profile">
            <div className="cti-avatar" aria-hidden="true" />
            <div>
              <div className="cti-profile-name">Analyst X</div>
              <div className="cti-profile-role">SOC Level 2</div>
            </div>
          </div>
          <nav className="cti-nav">
            <NavLink to="/intelligence/dashboard" className={({ isActive }) => `cti-nav-link ${isActive ? "active" : ""}`.trim()}>
              <span className="material-symbols-outlined filled">dashboard</span>
              <span>Dashboard</span>
            </NavLink>
            <NavLink to="/intelligence/search" className={({ isActive }) => `cti-nav-link ${isActive ? "active" : ""}`.trim()}>
              <span className="material-symbols-outlined">database</span>
              <span>Intelligence</span>
            </NavLink>
            <NavLink to="/workplans" className="cti-nav-link">
              <span className="material-symbols-outlined">briefcase_meal</span>
              <span>Cases</span>
            </NavLink>
            <NavLink to="/profile" className="cti-nav-link">
              <span className="material-symbols-outlined">settings</span>
              <span>Settings</span>
            </NavLink>
          </nav>
        </div>
        <div className="cti-sidebar-footer">
          <button type="button" className="cti-primary-button">
            <span className="material-symbols-outlined" style={{ fontSize: "var(--text-18)" }}>
              add
            </span>
            New Report
          </button>
        </div>
      </aside>

      <div className="cti-main">
        <header className="cti-topbar">
          <div className="cti-topbar-left">
            <span className="material-symbols-outlined" style={{ fontSize: "var(--text-28)", color: "var(--cti-primary)" }}>
              shield
            </span>
            <div className="cti-topbar-title">SIEM/XDR Console</div>
            <div className="cti-search">
              <span className="material-symbols-outlined">search</span>
              <input type="text" placeholder="Search IoCs, Cases, or Entities..." />
            </div>
          </div>
          <div className="cti-topbar-actions">
            <button type="button" className="cti-icon-button" aria-label="Notifications">
              <span className="material-symbols-outlined">notifications</span>
              <span className="cti-notification-ping" />
            </button>
            <button type="button" className="cti-icon-button" aria-label="Chat">
              <span className="material-symbols-outlined">chat_bubble</span>
            </button>
            <div className="cti-divider" />
            <div className="cti-org-avatar" aria-label="Organization logo" />
          </div>
        </header>

        <main className="cti-scroll">
          {error && <div className="cti-error">{error}</div>}

          <section className="cti-header">
            <div>
              <h1>Dashboard Overview</h1>
              <div className="cti-subtitle">Real-time threat intelligence monitoring and operations.</div>
            </div>
            <div className="cti-actions">
              <button type="button" className="cti-button">
                <span className="material-symbols-outlined" style={{ fontSize: "var(--text-16)" }}>
                  download
                </span>
                Import Feed
              </button>
              <button type="button" className="cti-button">
                <span className="material-symbols-outlined" style={{ fontSize: "var(--text-16)" }}>
                  add_circle
                </span>
                Add Observable
              </button>
              <button type="button" className="cti-button">
                <span className="material-symbols-outlined" style={{ fontSize: "var(--text-16)" }}>
                  auto_fix_high
                </span>
                Enrichment
              </button>
              <button type="button" className="cti-button primary">
                <span className="material-symbols-outlined" style={{ fontSize: "var(--text-16)" }}>
                  play_arrow
                </span>
                Run Playbook
              </button>
            </div>
          </section>

          <section className="cti-kpi-grid">
            {loading
              ? Array.from({ length: 5 }).map((_, index) => (
                  <div key={`kpi-skeleton-${index}`} className="cti-card">
                    <div className="cti-skeleton" style={{ height: 12, width: "60%", marginBottom: 10 }} />
                    <div className="cti-skeleton" style={{ height: 24, width: "40%", marginBottom: 10 }} />
                    <div className="cti-skeleton" style={{ height: 10, width: "50%" }} />
                  </div>
                ))
              : kpis.map((kpi) => (
                  <div key={kpi.id} className="cti-card">
                    <div className="cti-card-title">
                      <span>{kpi.label}</span>
                      <span className="material-symbols-outlined" style={{ color: "var(--cti-text-secondary)", fontSize: "var(--text-20)" }}>
                        {kpi.icon}
                      </span>
                    </div>
                    <div className="cti-card-value">{kpi.value}</div>
                    <div className={`cti-card-trend ${trendClass(kpi.trend.direction)}`}>
                      <span className="material-symbols-outlined" style={{ fontSize: "var(--text-14)" }}>
                        {trendIcon(kpi.trend.direction)}
                      </span>
                      <span>{kpi.trend.label}</span>
                    </div>
                  </div>
                ))}
          </section>

          <section className="cti-grid-main">
            <div className="cti-card cti-table-card">
              <div className="cti-card-header">
                <h3>Recent Intelligence</h3>
                <button type="button">View All</button>
              </div>
              {loading ? (
                <div style={{ padding: 20, display: "grid", gap: 12 }}>
                  {Array.from({ length: 4 }).map((_, index) => (
                    <div key={`intel-skeleton-${index}`} className="cti-skeleton" style={{ height: 48 }} />
                  ))}
                </div>
              ) : (
                <div style={{ overflowX: "auto" }}>
                  <table className="cti-table">
                    <thead>
                      <tr>
                        <th>Type</th>
                        <th>Name</th>
                        <th>Source</th>
                        <th>Confidence</th>
                        <th>Tags</th>
                        <th>Updated</th>
                      </tr>
                    </thead>
                    <tbody>
                      {recentIntel.map((item) => (
                        <tr key={item.id}>
                          <td>
                            <div
                              className="cti-type-icon"
                              style={{ background: item.iconBackground, color: item.iconColor }}
                            >
                              <span className="material-symbols-outlined" style={{ fontSize: "var(--text-18)" }}>
                                {item.icon}
                              </span>
                            </div>
                          </td>
                          <td style={{ color: "var(--palette-fff)", fontWeight: 600 }}>{item.name}</td>
                          <td style={{ color: "var(--cti-text-secondary)" }}>{item.source}</td>
                          <td>
                            <div className="cti-confidence-bar">
                              <div
                                className="cti-confidence-fill"
                                style={{ width: `${item.confidence.score}%`, background: item.confidence.barColor }}
                              />
                            </div>
                            <div style={{ fontSize: "var(--text-12)", color: "var(--cti-text-secondary)", marginTop: 4 }}>
                              {item.confidence.score}/100
                            </div>
                          </td>
                          <td>
                            <div className="cti-tags">
                              {item.tags.map((tag) => (
                                <span
                                  key={tag.label}
                                  className="cti-tag"
                                  style={{
                                    color: tag.textColor,
                                    background: tag.background,
                                    borderColor: tag.borderColor,
                                  }}
                                >
                                  {tag.label}
                                </span>
                              ))}
                            </div>
                          </td>
                          <td style={{ color: "var(--cti-text-secondary)" }}>{item.updatedAt}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div className="cti-card">
              <div className="cti-card-header">
                <h3>Top Techniques (ATT&amp;CK)</h3>
              </div>
              <div className="cti-technique-list">
                {loading
                  ? Array.from({ length: 5 }).map((_, index) => (
                      <div key={`tech-skeleton-${index}`} className="cti-skeleton" style={{ height: 18 }} />
                    ))
                  : topTechniques.map((technique) => (
                      <div key={technique.id} className="cti-technique-row">
                        <div className="cti-technique-head">
                          <span>{technique.label}</span>
                          <span style={{ fontSize: "var(--text-12)", color: "var(--cti-text-secondary)" }}>{technique.count}</span>
                        </div>
                        <div className="cti-technique-bar">
                          <div
                            className="cti-technique-fill"
                            style={{ width: `${Math.min(100, technique.intensity * 100)}%` }}
                          />
                        </div>
                      </div>
                    ))}
              </div>
            </div>
          </section>

          <section className="cti-card cti-stream-card">
            <div className="cti-card-header">
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span className="cti-live-indicator" aria-hidden="true" />
                <h3>Latest Stream Events</h3>
              </div>
              <button type="button" onClick={loadDashboard} aria-label="Refresh stream">
                <span className="material-symbols-outlined">refresh</span>
              </button>
            </div>
            {streamContent}
          </section>
        </main>
      </div>
    </div>
  );
};

export default IntelligenceDashboardPage;
