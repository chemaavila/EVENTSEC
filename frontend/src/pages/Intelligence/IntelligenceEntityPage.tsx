import { useEffect, useState } from "react";
import CtiAdapterFallback from "../../components/cti/CtiAdapterFallback";
import ctiAdapter from "../../services/cti";
import { CtiNotImplementedError } from "../../services/cti/apiAdapter";
import type { CtiEntityDetail } from "../../services/cti";
import "../../components/cti/cti.css";

const IntelligenceEntityPage = () => {
  const [entity, setEntity] = useState<CtiEntityDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [adapterUnavailable, setAdapterUnavailable] = useState(false);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    setError(null);
    ctiAdapter
      .getEntityDetail()
      .then((data) => {
        if (mounted) setEntity(data);
      })
      .catch((err) => {
        console.error(err);
        if (mounted && err instanceof CtiNotImplementedError) {
          setAdapterUnavailable(true);
          return;
        }
        if (mounted) setError("Unable to load entity details.");
      })
      .finally(() => {
        if (mounted) setLoading(false);
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

  if (loading) {
    return (
      <div className="cti-entity-shell">
        <div className="cti-placeholder">
          <h1>Loading entity...</h1>
          <p>Fetching entity details.</p>
        </div>
      </div>
    );
  }

  if (error || !entity) {
    return (
      <div className="cti-entity-shell">
        <div className="cti-placeholder">
          <h1>Entity Detail</h1>
          <p>{error ?? "No entity data found."}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="cti-entity-shell">
      <header className="cti-entity-topbar">
        <div className="cti-entity-topbar-left">
          <div className="cti-entity-brand">
            <div className="cti-entity-brand-icon">
              <span className="material-symbols-outlined" style={{ fontSize: 32 }}>
                shield_lock
              </span>
            </div>
            <div className="cti-entity-brand-title">Consola SIEM/XDR</div>
          </div>
          <div className="cti-entity-search">
            <label className="cti-input-wrapper">
              <span className="material-symbols-outlined">search</span>
              <input placeholder="Search IPs, hashes, domains, or cases..." />
              <div className="cti-entity-search-kbd">
                <span>⌘ K</span>
              </div>
            </label>
          </div>
        </div>
        <div className="cti-entity-topbar-actions">
          <button className="cti-entity-icon-button" type="button">
            <span className="material-symbols-outlined" style={{ fontSize: 24 }}>
              notifications
            </span>
            <span className="cti-entity-notification-dot" />
          </button>
          <button className="cti-entity-icon-button" type="button">
            <span className="material-symbols-outlined" style={{ fontSize: 24 }}>
              settings
            </span>
          </button>
          <div className="cti-divider" />
          <div className="cti-entity-user">
            <div className="cti-entity-avatar" />
            <div className="cti-search-brand-title" style={{ fontSize: 14 }}>
              Analyst User
            </div>
          </div>
        </div>
      </header>

      <main className="cti-entity-main">
        <nav className="cti-breadcrumbs">
          <a href="/intelligence/dashboard">
            <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
              public
            </span>
            Threat Intelligence
          </a>
          <span>/</span>
          <a href="/intelligence/search">Entities</a>
          <span>/</span>
          <span className="current">{entity.id}</span>
        </nav>

        <section className="cti-entity-header">
          <div className="cti-entity-title">
            <div className="cti-entity-title-row">
              <div className="cti-entity-icon">
                <span className="material-symbols-outlined" style={{ fontSize: 36, color: "var(--cti-primary)" }}>
                  dns
                </span>
              </div>
              <div>
                <div style={{ display: "flex", alignItems: "baseline", gap: 12 }}>
                  <h1>{entity.id}</h1>
                  <span className="cti-entity-type">{entity.typeLabel}</span>
                </div>
                <div className="cti-entity-status">
                  <span className="cti-entity-status-dot" />
                  {entity.statusText}
                  <span style={{ color: "#3a4450" }}>•</span>
                  {entity.firstSeenLabel}
                </div>
              </div>
            </div>
            <div className="cti-entity-chips">
              <div className="cti-entity-chip malicious">
                <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
                  gpp_bad
                </span>
                Malicious
              </div>
              <div className="cti-entity-chip confidence">
                <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
                  verified
                </span>
                High Confidence
              </div>
              <div className="cti-entity-chip tlp">
                <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
                  lock
                </span>
                TLP:AMBER
              </div>
              <div className="cti-entity-chip add">
                <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
                  sell
                </span>
                Add Tag
              </div>
            </div>
          </div>
          <div className="cti-entity-actions">
            {[
              { icon: "hub", label: "Pivot Graph" },
              { icon: "edit", label: "Edit" },
              { icon: "download", label: "STIX 2.1" },
            ].map((action) => (
              <button key={action.label} className="cti-entity-action light" type="button">
                <span className="material-symbols-outlined" style={{ fontSize: 20 }}>
                  {action.icon}
                </span>
                {action.label}
              </button>
            ))}
            <div className="cti-entity-action-divider" />
            <button className="cti-entity-action light" type="button">
              <span className="material-symbols-outlined" style={{ fontSize: 20 }}>
                assignment_add
              </span>
              Create Case
            </button>
            <button className="cti-entity-action primary" type="button">
              <span className="material-symbols-outlined" style={{ fontSize: 20 }}>
                play_arrow
              </span>
              Run Playbook
            </button>
          </div>
        </section>

        <div className="cti-entity-body">
          <div className="cti-entity-left">
            <div className="cti-entity-tabs">
              <button className="active" type="button">
                Overview
              </button>
              <button type="button">
                Relationships <span className="cti-entity-badge-count">12</span>
              </button>
              <button type="button">
                Sightings <span className="cti-entity-badge-count">45</span>
              </button>
              <button type="button">Enrichment</button>
              <button type="button">History</button>
            </div>

            <div className="cti-entity-body">
              <div className="cti-entity-card cti-entity-description">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <h3>Description</h3>
                  <button
                    type="button"
                    style={{ color: "var(--cti-primary)", border: "none", background: "transparent", cursor: "pointer" }}
                  >
                    Edit
                  </button>
                </div>
                <p>
                  This IP address has been identified as a Command and Control (C2) node associated with the{" "}
                  <a href="/intelligence/entity/apt29">APT29</a> threat group. It has been observed scanning internal
                  subnets for vulnerabilities in the SMB protocol. Initially detected via firewall logs indicating
                  outbound traffic on non-standard ports.
                </p>
                <div className="cti-entity-divider">
                  <h4
                    style={{
                      fontSize: 11,
                      letterSpacing: "0.08em",
                      textTransform: "uppercase",
                      color: "#9dabb9",
                      marginBottom: 12,
                    }}
                  >
                    External References
                  </h4>
                  <div className="cti-entity-references">
                    {entity.externalReferences.map((reference) => (
                      <span key={reference}>
                        <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
                          open_in_new
                        </span>
                        {reference}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              <div className="cti-entity-card">
                <h3>Technical Details</h3>
                <div className="cti-entity-technical">
                  <div>
                    <span>ASN</span>
                    <strong>{entity.technicalDetails.asn}</strong>
                  </div>
                  <div>
                    <span>Country</span>
                    <strong>
                      {entity.technicalDetails.country}{" "}
                      <span style={{ color: "#9dabb9", fontSize: 12 }}>
                        {entity.technicalDetails.countryCode}
                      </span>
                    </strong>
                  </div>
                  <div>
                    <span>First Seen</span>
                    <strong>{entity.technicalDetails.firstSeen}</strong>
                  </div>
                  <div>
                    <span>Last Seen</span>
                    <strong>{entity.technicalDetails.lastSeen}</strong>
                  </div>
                  <div className="cti-entity-reverse">
                    <span>Reverse DNS</span>
                    <code>{entity.technicalDetails.reverseDns}</code>
                  </div>
                </div>
              </div>

              <div className="cti-entity-card">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
                  <h3>Provenance Timeline</h3>
                  <button type="button" className="cti-entity-icon-button">
                    <span className="material-symbols-outlined">filter_list</span>
                  </button>
                </div>
                <div className="cti-entity-timeline">
                  {entity.timeline.map((item, index) => (
                    <div key={item.id} className="cti-entity-timeline-item">
                      <div style={{ position: "relative" }}>
                        <div className="cti-entity-timeline-dot" style={{ background: item.dotColor }} />
                        {index < entity.timeline.length - 1 && <div className="cti-entity-timeline-line" />}
                      </div>
                      <div className="cti-entity-timeline-content">
                        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                          <h4>{item.title}</h4>
                          <span>{item.timestamp}</span>
                        </div>
                        <p>{item.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <aside className="cti-entity-right">
            <div className="cti-entity-card" style={{ padding: 0 }}>
              <div style={{ padding: 16, borderBottom: "1px solid #283039", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <h3>Linked Entities</h3>
                <span className="cti-entity-badge-count">{entity.linkedEntities.length}</span>
              </div>
              <div className="cti-entity-list" style={{ padding: 16 }}>
                {entity.linkedEntities.map((item) => (
                  <a key={item.id} href="#">
                    <span className="material-symbols-outlined" style={{ color: item.iconColor }}>
                      {item.icon}
                    </span>
                    <div style={{ minWidth: 0 }}>
                      <div className="title">{item.title}</div>
                      <div className="subtitle">{item.subtitle}</div>
                    </div>
                  </a>
                ))}
              </div>
            </div>

            <div className="cti-entity-card" style={{ padding: 0 }}>
              <div className="cti-mitre-header" style={{ padding: 16, borderBottom: "1px solid #283039" }}>
                <h3>MITRE ATT&amp;CK</h3>
                <div className="cti-mitre-logo" aria-hidden="true" />
              </div>
              <div style={{ padding: 16 }}>
                <div className="cti-mitre-tags">
                  {entity.mitreTechniques.map((technique) => (
                    <span key={technique}>{technique}</span>
                  ))}
                </div>
                <div className="cti-mitre-description">{entity.mitreDescription}</div>
              </div>
            </div>

            <div className="cti-entity-card" style={{ padding: 0 }}>
              <div style={{ padding: 16, borderBottom: "1px solid #283039" }}>
                <h3>Linked Cases</h3>
              </div>
              {entity.linkedCases.map((caseItem) => (
                <div key={caseItem.id} className="cti-case-row">
                  <div className="cti-case-header">
                    <div className="cti-case-id">{caseItem.id}</div>
                    <div className="cti-case-severity" style={{ background: caseItem.severityColor }}>
                      {caseItem.severity}
                    </div>
                  </div>
                  <div className="cti-case-summary">{caseItem.summary}</div>
                  {caseItem.updatedAt && (
                    <div className="cti-case-updated">
                      {caseItem.showClock && (
                        <span className="material-symbols-outlined" style={{ fontSize: 14 }}>
                          schedule
                        </span>
                      )}
                      {caseItem.updatedAt}
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div className="cti-entity-map">
              <div className="cti-entity-map-content">
                <p className="cti-entity-map-label">Geo-Location</p>
                <p className="cti-entity-map-location">
                  <span className="material-symbols-outlined" style={{ color: "#ef4444" }}>
                    location_on
                  </span>
                  {entity.locationLabel}
                </p>
              </div>
            </div>
          </aside>
        </div>
      </main>
    </div>
  );
};

export default IntelligenceEntityPage;
