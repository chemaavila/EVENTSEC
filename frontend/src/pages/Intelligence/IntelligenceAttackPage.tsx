import { useEffect, useMemo, useState } from "react";
import CtiAdapterFallback from "../../components/cti/CtiAdapterFallback";
import ctiAdapter from "../../services/cti";
import { CtiNotImplementedError } from "../../services/cti/apiAdapter";
import type { CtiAttackData, CtiAttackTechnique } from "../../services/cti";
import "../../components/cti/cti.css";

const getTechniqueClasses = (technique: CtiAttackTechnique) => {
  if (technique.highlighted) return "cti-attack-card highlighted";
  if (!technique.active) return "cti-attack-card inactive";
  if (technique.severity === "high") return "cti-attack-card active";
  if (technique.severity === "medium") return "cti-attack-card medium";
  if (technique.severity === "low") return "cti-attack-card low";
  return "cti-attack-card";
};

const IntelligenceAttackPage = () => {
  const [attackData, setAttackData] = useState<CtiAttackData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [adapterUnavailable, setAdapterUnavailable] = useState(false);

  useEffect(() => {
    let mounted = true;
    ctiAdapter
      .getAttackMatrix()
      .then((data) => {
        if (mounted) setAttackData(data);
      })
      .catch((err) => {
        console.error(err);
        if (mounted && err instanceof CtiNotImplementedError) {
          setAdapterUnavailable(true);
          return;
        }
        if (mounted) setError("Unable to load ATT&CK matrix data.");
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

  const selected = attackData?.selected;
  const legend = useMemo(
    () => [
      { label: "High (10+)", color: "var(--palette-ef4444)" },
      { label: "Medium (5-9)", color: "var(--palette-fb923c)" },
      { label: "Low (1-4)", color: "var(--palette-facc15)" },
    ],
    []
  );

  if (!attackData) {
    return (
      <div className="cti-attack-shell">
        <div className="cti-placeholder">
          <h1>ATT&amp;CK Matrix</h1>
          <p>{error ?? "Loading matrix data..."}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="cti-attack-shell">
      <header className="cti-attack-topbar">
        <div className="cti-attack-topbar-left">
          <div className="cti-attack-brand">
            <div className="cti-attack-brand-icon">
              <span className="material-symbols-outlined" style={{ fontSize: "var(--text-32)" }}>
                security
              </span>
            </div>
            <div className="cti-attack-brand-title">Consola SIEM</div>
          </div>
          <div className="cti-attack-search">
            <label className="cti-input-wrapper">
              <span className="material-symbols-outlined">search</span>
              <input placeholder="Search resources..." />
            </label>
          </div>
        </div>
        <div className="cti-attack-topbar-right">
          <nav className="cti-attack-nav">
            <a href="/intelligence/dashboard">Dashboard</a>
            <a href="/alerts">Alerts</a>
            <a className="active" href="/intelligence/attack">
              Threat Intel
            </a>
            <a href="/workplans">Cases</a>
          </nav>
          <div className="cti-divider" />
          <button type="button">
            <span className="material-symbols-outlined" style={{ fontSize: "var(--text-22)" }}>
              notifications
            </span>
          </button>
          <button type="button">
            <span className="material-symbols-outlined" style={{ fontSize: "var(--text-22)" }}>
              settings
            </span>
          </button>
          <div className="cti-attack-avatar" aria-label="User avatar" />
        </div>
      </header>

      <div className="cti-attack-layout">
        <main className="cti-attack-main">
          <div className="cti-attack-header">
            <div className="cti-attack-breadcrumbs">
              <a href="/intelligence/dashboard">Home</a>
              <span>/</span>
              <a href="/intelligence/dashboard">Threat Intelligence</a>
              <span>/</span>
              <span className="current">ATT&amp;CK Matrix</span>
            </div>

            <div className="cti-attack-title-row">
              <div className="cti-attack-title">
                <h1>ATT&amp;CK Matrix</h1>
                <p>
                  Visualize detected adversary tactics and techniques. Click on any highlighted technique to analyze
                  linked threat data.
                </p>
              </div>
              <div className="cti-attack-title-actions">
                <button className="cti-attack-button light" type="button">
                  <span className="material-symbols-outlined" style={{ fontSize: "var(--text-20)" }}>
                    tune
                  </span>
                  Customize View
                </button>
                <button className="cti-attack-button primary" type="button">
                  <span className="material-symbols-outlined" style={{ fontSize: "var(--text-20)" }}>
                    download
                  </span>
                  Export Matrix
                </button>
              </div>
            </div>

            <div className="cti-attack-filters">
              {[
                { label: "Date", value: "Last 30 Days" },
                { label: "Confidence", value: "High & Medium" },
                { label: "Threat Actor", value: "All" },
                { label: "Source", value: "Endpoint & Network" },
              ].map((filter) => (
                <button key={filter.label} className="cti-attack-filter" type="button">
                  {filter.label}: <strong>{filter.value}</strong>
                  <span className="material-symbols-outlined" style={{ fontSize: "var(--text-18)" }}>
                    expand_more
                  </span>
                </button>
              ))}
              <div className="cti-divider" />
              <button className="cti-attack-filter clear" type="button">
                <span className="material-symbols-outlined" style={{ fontSize: "var(--text-20)" }}>
                  filter_list_off
                </span>
                Clear
              </button>
            </div>
          </div>

          <section className="cti-attack-matrix">
            <div className="cti-attack-scroll">
              <div className="cti-attack-columns">
                {attackData.tactics.map((tactic) => (
                  <div key={tactic.id} className="cti-attack-column">
                    <div className="cti-attack-column-header">
                      <h3>{tactic.name}</h3>
                      <span>{tactic.detectedCount} Techniques Detected</span>
                    </div>
                    <div className="cti-attack-column-body">
                      {tactic.techniques.map((technique) => (
                        <div key={technique.id} className={getTechniqueClasses(technique)}>
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                            <span
                              className="cti-attack-card-code"
                              style={{ color: technique.highlighted ? "var(--palette-7cb7ff)" : undefined }}
                            >
                              {technique.id}
                            </span>
                            {technique.count ? (
                              <span
                                className={`cti-attack-count ${
                                  technique.highlighted
                                    ? "highlighted"
                                    : technique.severity === "medium"
                                    ? "medium"
                                    : technique.severity === "low"
                                    ? "low"
                                    : ""
                                }`}
                              >
                                {technique.count}
                              </span>
                            ) : null}
                          </div>
                          <h4 className={technique.active ? undefined : "muted"}>{technique.name}</h4>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="cti-attack-legend">
              <span style={{ fontWeight: 700, color: "var(--palette-94a3b8)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
                Legend
              </span>
              {legend.map((item) => (
                <span key={item.label}>
                  <span className="cti-attack-legend-dot" style={{ background: item.color }} />
                  {item.label}
                </span>
              ))}
            </div>
          </section>
        </main>

        <aside className="cti-attack-drawer">
          <div className="cti-attack-drawer-header">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <span className="cti-attack-drawer-code">{selected?.code}</span>
              <button type="button" style={{ background: "transparent", border: "none", color: "var(--palette-94a3b8)" }}>
                <span className="material-symbols-outlined" style={{ fontSize: "var(--text-24)" }}>
                  close
                </span>
              </button>
            </div>
            <div className="cti-attack-drawer-title">{selected?.title}</div>
            <div className="cti-attack-drawer-badges">
              <span className="cti-attack-drawer-badge high">
                <span className="material-symbols-outlined" style={{ fontSize: "var(--text-14)" }}>
                  warning
                </span>
                {selected?.confidenceLabel}
              </span>
              <span className="cti-attack-drawer-badge alerts">{selected?.alertsCount} Alerts</span>
            </div>
          </div>

          <div className="cti-attack-drawer-body">
            <div className="cti-attack-section">
              <h3>Description</h3>
              <p>{selected?.description}</p>
              <a className="cti-attack-link" href="#">
                View on MITRE ATT&amp;CK
                <span className="material-symbols-outlined" style={{ fontSize: "var(--text-14)" }}>
                  open_in_new
                </span>
              </a>
            </div>

            <div className="cti-attack-section">
              <h3>Linked Threat Intel</h3>
              <div style={{ display: "grid", gap: 12 }}>
                {selected?.linkedIntel.map((intel) => (
                  <div key={intel.id} className="cti-attack-intel-card">
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                      <span style={{ fontSize: "var(--text-12)", fontWeight: 700, color: "var(--palette-e2e8f0)" }}>{intel.title}</span>
                      <span style={{ fontSize: "var(--text-10)", textTransform: "uppercase", color: "var(--palette-94a3b8)", border: "1px solid var(--palette-475569)", padding: "0 4px", borderRadius: 4 }}>
                        {intel.category}
                      </span>
                    </div>
                    {intel.relevance ? (
                      <>
                        <div className="bar">
                          <span />
                        </div>
                        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "var(--text-10)" }}>
                          <span className="relevance">Relevance</span>
                          <span style={{ color: intel.relevance === "high" ? "var(--palette-ef4444)" : "var(--palette-94a3b8)", fontWeight: 700 }}>
                            {intel.relevance === "high" ? "High" : "Medium"}
                          </span>
                        </div>
                      </>
                    ) : (
                      <p style={{ fontSize: "var(--text-12)", color: "var(--palette-94a3b8)" }}>{intel.note}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div className="cti-attack-section">
              <h3>Latest Sightings</h3>
              <div className="cti-attack-sighting">
                {selected?.sightings.map((sighting) => (
                  <div key={sighting.id} className={`cti-attack-sighting-item ${sighting.high ? "high" : ""}`}>
                    <div className="time">{sighting.timestamp}</div>
                    <div className="title">{sighting.title}</div>
                    <div className="host">{sighting.host}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="cti-attack-drawer-footer">
            <button className="primary" type="button">
              <span className="material-symbols-outlined" style={{ fontSize: "var(--text-20)" }}>
                add_box
              </span>
              Create Case from Technique
            </button>
            <button className="secondary" type="button">
              <span className="material-symbols-outlined" style={{ fontSize: "var(--text-20)" }}>
                share
              </span>
              Export Indicators
            </button>
          </div>
        </aside>
      </div>
    </div>
  );
};

export default IntelligenceAttackPage;
