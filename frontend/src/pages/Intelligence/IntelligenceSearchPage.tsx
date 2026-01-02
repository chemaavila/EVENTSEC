import { useEffect, useMemo, useState } from "react";
import CtiAdapterFallback from "../../components/cti/CtiAdapterFallback";
import ctiAdapter from "../../services/cti";
import { CtiNotImplementedError } from "../../services/cti/apiAdapter";
import type { CtiSearchData, CtiSearchResult } from "../../services/cti";
import "../../components/cti/cti.css";

type FilterState = {
  entityTypes: Record<string, boolean>;
  confidence: number;
  reliability: string;
  tlp: string;
  source: string;
  timeframe: string;
};

const defaultFilters: FilterState = {
  entityTypes: {
    "IP Address": true,
    Domain: true,
    "File Hash": false,
    URL: false,
  },
  confidence: 75,
  reliability: "A - Completely Reliable",
  tlp: "RED",
  source: "",
  timeframe: "Last 24h",
};

const savedQueries = [
  {
    id: "soc-1",
    icon: "star",
    title: "High Conf Ransomware",
    description: "Indicators > 80%",
    emphasized: true,
  },
  {
    id: "soc-2",
    icon: "star",
    title: "APT29 Campaign",
    description: "Source: CrowdStrike",
    emphasized: true,
  },
  {
    id: "my-1",
    icon: "history",
    title: "New Domains (24h)",
    description: "Created < 1 day",
  },
  {
    id: "my-2",
    icon: "history",
    title: "Suspicious Emails",
    description: "Hash match",
  },
  {
    id: "my-3",
    icon: "history",
    title: "External IP Scans",
    description: "Firewall Logs",
  },
];

const isKqlValid = (query: string) => {
  const stack: string[] = [];
  for (const char of query) {
    if (char === "(") stack.push(char);
    if (char === ")") {
      if (!stack.length) return false;
      stack.pop();
    }
  }
  return stack.length === 0;
};

const IntelligenceSearchPage = () => {
  const [searchData, setSearchData] = useState<CtiSearchData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState(defaultFilters);
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [adapterUnavailable, setAdapterUnavailable] = useState(false);

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedQuery(query), 400);
    return () => window.clearTimeout(timer);
  }, [query]);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    setError(null);
    ctiAdapter
      .getSearchResults()
      .then((data) => {
        if (mounted) setSearchData(data);
      })
      .catch((err) => {
        console.error(err);
        if (mounted && err instanceof CtiNotImplementedError) {
          setAdapterUnavailable(true);
          return;
        }
        if (mounted) setError("Unable to load intelligence results.");
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  const results = searchData?.results ?? [];
  const total = searchData?.total ?? 0;
  const duration = searchData?.durationSeconds ?? 0;
  const kqlError = debouncedQuery.length > 0 && !isKqlValid(debouncedQuery);

  const appliedFilters = useMemo(() => {
    const types = Object.entries(filters.entityTypes)
      .filter(([, value]) => value)
      .map(([key]) => key);
    return [
      { label: `Type: ${types.join(", ")}`, key: "types" },
      { label: `Conf: > ${filters.confidence}`, key: "confidence" },
    ];
  }, [filters]);

  const handleTypeToggle = (label: string) => {
    setFilters((prev) => ({
      ...prev,
      entityTypes: {
        ...prev.entityTypes,
        [label]: !prev.entityTypes[label],
      },
    }));
  };

  const renderTlpDot = (tlp: CtiSearchResult["tlp"]) => {
    if (tlp === "red") return "#ef4444";
    if (tlp === "amber") return "#f59e0b";
    if (tlp === "green") return "#22c55e";
    return "#94a3b8";
  };

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
    <div className="cti-search-shell">
      <header className="cti-search-topbar">
        <div className="cti-search-topbar-left">
          <div className="cti-search-brand">
            <div className="cti-search-brand-icon">
              <span className="material-symbols-outlined">shield_moon</span>
            </div>
            <div className="cti-search-brand-title">SIEM/XDR Console</div>
          </div>
          <nav className="cti-top-tabs">
            <a href="/intelligence/dashboard">Dashboard</a>
            <a className="active" href="/intelligence/search">
              Threat Intel
            </a>
            <a href="/alerts">Incidents</a>
            <a href="/advanced-search">Hunting</a>
          </nav>
        </div>
        <div className="cti-search-topbar-right">
          <div className="cti-search-topbar-input">
            <label className="cti-input-wrapper">
              <span className="material-symbols-outlined">search</span>
              <input placeholder="Global Search..." />
            </label>
          </div>
          <div className="cti-search-topbar-actions">
            <button className="cti-search-notification" type="button">
              <span className="material-symbols-outlined">notifications</span>
              <span className="cti-search-notification-dot" />
            </button>
            <div className="cti-search-avatar" aria-label="User avatar" />
          </div>
        </div>
      </header>

      <div className="cti-search-layout">
        <aside className="cti-search-sidebar">
          <div className="cti-search-sidebar-header">
            <div className="cti-search-sidebar-title">Filters</div>
            <button type="button" onClick={() => setFilters(defaultFilters)}>
              Reset All
            </button>
          </div>
          <div className="cti-search-sidebar-body">
            <div className="cti-filter-section">
              <h4>Entity Type</h4>
              <div style={{ display: "grid", gap: 8 }}>
                {Object.keys(filters.entityTypes).map((label) => (
                  <label key={label} className="cti-checkbox">
                    <input
                      type="checkbox"
                      checked={filters.entityTypes[label]}
                      onChange={() => handleTypeToggle(label)}
                    />
                    <span>{label}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="cti-filter-section">
              <div className="cti-slider-header">
                <h4>Confidence</h4>
                <span>{filters.confidence}+</span>
              </div>
              <input
                className="cti-range"
                type="range"
                min={0}
                max={100}
                value={filters.confidence}
                onChange={(event) =>
                  setFilters((prev) => ({ ...prev, confidence: Number(event.target.value) }))
                }
              />
              <div className="cti-range-labels">
                <span>0</span>
                <span>50</span>
                <span>100</span>
              </div>
            </div>

            <div className="cti-filter-section">
              <h4>Reliability</h4>
              <div className="cti-select">
                <select
                  value={filters.reliability}
                  onChange={(event) =>
                    setFilters((prev) => ({ ...prev, reliability: event.target.value }))
                  }
                >
                  <option>A - Completely Reliable</option>
                  <option>B - Usually Reliable</option>
                  <option>C - Fairly Reliable</option>
                  <option>All Levels</option>
                </select>
                <span className="material-symbols-outlined">expand_more</span>
              </div>
            </div>

            <div className="cti-filter-section">
              <h4>TLP Marker</h4>
              <div className="cti-tlp-row">
                {[
                  { label: "RED", className: "red" },
                  { label: "AMB", className: "amber" },
                  { label: "GRN", className: "green" },
                  { label: "WHT", className: "white" },
                ].map((tlp) => (
                  <button
                    key={tlp.label}
                    type="button"
                    className={`cti-tlp-button ${tlp.className}`}
                    onClick={() => setFilters((prev) => ({ ...prev, tlp: tlp.label }))}
                  >
                    {tlp.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="cti-filter-section">
              <h4>Source</h4>
              <label className="cti-source-input">
                <span className="material-symbols-outlined" style={{ fontSize: 16, color: "#94a3b8" }}>
                  filter_alt
                </span>
                <input
                  placeholder="Filter sources..."
                  value={filters.source}
                  onChange={(event) => setFilters((prev) => ({ ...prev, source: event.target.value }))}
                />
              </label>
            </div>

            <div className="cti-filter-section cti-timeframe">
              <h4>Timeframe</h4>
              <div className="cti-timeframe-grid">
                {["Last 24h", "7 Days", "30 Days", "Custom"].map((value) => (
                  <button
                    key={value}
                    type="button"
                    className={`cti-timeframe-button ${filters.timeframe === value ? "active" : ""}`}
                    onClick={() => setFilters((prev) => ({ ...prev, timeframe: value }))}
                  >
                    {value}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </aside>

        <main className="cti-search-main">
          <div className="cti-search-main-header">
            <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", gap: 16 }}>
              <div>
                <h1 className="cti-search-main-title">Intelligence Search</h1>
                <div className="cti-search-main-subtitle">
                  Central operations for threat hunting and analysis.
                </div>
              </div>
              <div className="cti-search-actions">
                <button className="cti-search-action-button" type="button">
                  <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
                    upload
                  </span>
                  Export
                </button>
                <button className="cti-search-action-button primary" type="button">
                  <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
                    add
                  </span>
                  New Investigation
                </button>
              </div>
            </div>

            <div className="cti-search-input">
              <span className="material-symbols-outlined">search</span>
              <input
                type="text"
                placeholder="Search Indicators (IP, Hash, Domain, URL, CVE)..."
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
              <span className="cti-kql-badge">KQL Supported</span>
            </div>
            {kqlError && <div className="cti-kql-error">Unbalanced parentheses in KQL query.</div>}

            <div className="cti-applied-row">
              <div className="cti-applied-filters">
                <span className="cti-applied-label">Applied:</span>
                {appliedFilters.map((filter) => (
                  <span key={filter.key} className="cti-chip">
                    {filter.label}
                    <button type="button" aria-label={`Remove ${filter.label}`}>
                      <span className="material-symbols-outlined" style={{ fontSize: 14 }}>
                        close
                      </span>
                    </button>
                  </span>
                ))}
              </div>
              <span className="cti-results-meta">
                {total.toLocaleString()} results found ({duration.toFixed(2)}s)
              </span>
            </div>
          </div>

          <div className="cti-results-table">
            {error && <div className="cti-error">{error}</div>}
            <div className="cti-table-shell">
              <table className="cti-search-table">
                <thead>
                  <tr>
                    <th style={{ width: 48 }}>Type</th>
                    <th>Indicator Value</th>
                    <th style={{ width: 160 }}>Confidence</th>
                    <th style={{ width: 160 }}>Reliability</th>
                    <th style={{ width: 90 }}>TLP</th>
                    <th>Source</th>
                    <th style={{ textAlign: "right" }}>Last Seen</th>
                    <th style={{ width: 40 }} />
                  </tr>
                </thead>
                <tbody>
                  {loading && (
                    <tr>
                      <td colSpan={8} style={{ padding: 24 }}>
                        <div className="cti-skeleton" style={{ height: 16, marginBottom: 8 }} />
                        <div className="cti-skeleton" style={{ height: 16, marginBottom: 8 }} />
                        <div className="cti-skeleton" style={{ height: 16 }} />
                      </td>
                    </tr>
                  )}
                  {!loading && results.length === 0 && (
                    <tr>
                      <td colSpan={8} style={{ padding: 24, color: "#94a3b8", textAlign: "center" }}>
                        No results match the current filters.
                      </td>
                    </tr>
                  )}
                  {!loading &&
                    results.map((result) => (
                      <tr key={result.id}>
                        <td>
                          <div
                            className="cti-type-icon"
                            style={{ background: result.typeIconBackground, color: result.typeIconColor }}
                          >
                            <span className="material-symbols-outlined" style={{ fontSize: 20 }}>
                              {result.typeIcon}
                            </span>
                          </div>
                        </td>
                        <td>
                          <div className="cti-result-value">{result.value}</div>
                          <div className="cti-result-sub">{result.summary}</div>
                        </td>
                        <td>
                          <span
                            className="cti-pill"
                            style={{
                              background: result.confidence.background,
                              color: result.confidence.textColor,
                              borderColor: result.confidence.borderColor,
                            }}
                          >
                            {result.confidence.label}
                          </span>
                        </td>
                        <td>
                          <span className="cti-reliability">{result.reliability}</span>
                        </td>
                        <td>
                          <span
                            style={{
                              display: "inline-flex",
                              width: 12,
                              height: 12,
                              borderRadius: 999,
                              background: renderTlpDot(result.tlp),
                              boxShadow: `0 0 8px ${renderTlpDot(result.tlp)}80`,
                            }}
                          />
                        </td>
                        <td style={{ color: "#94a3b8" }}>{result.source}</td>
                        <td style={{ textAlign: "right", color: "#94a3b8", fontFamily: "ui-monospace, monospace" }}>
                          {result.lastSeen}
                        </td>
                        <td className="cti-td-actions">
                          <div className="cti-hover-actions">
                            {[
                              { icon: "visibility", label: "View Details" },
                              { icon: "call_split", label: "Pivot" },
                              { icon: "auto_awesome", label: "Enrich" },
                              { icon: "briefcase_meal", label: "Create Case" },
                            ].map((action) => (
                              <button key={action.icon} type="button" title={action.label}>
                                <span className="material-symbols-outlined" style={{ fontSize: 20 }}>
                                  {action.icon}
                                </span>
                              </button>
                            ))}
                          </div>
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>

            <div className="cti-pagination">
              <div className="cti-pagination-info">
                Showing <span>1</span> to <span>10</span> of <span>{total.toLocaleString()}</span> results
              </div>
              <div className="cti-pagination-nav">
                <button className="cti-pagination-icon" type="button">
                  <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
                    chevron_left
                  </span>
                </button>
                <button className="cti-pagination-button active" type="button">
                  1
                </button>
                <button className="cti-pagination-button" type="button">
                  2
                </button>
                <button className="cti-pagination-button" type="button">
                  3
                </button>
                <span style={{ color: "#94a3b8" }}>...</span>
                <button className="cti-pagination-icon" type="button">
                  <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
                    chevron_right
                  </span>
                </button>
              </div>
            </div>
          </div>
        </main>

        <aside className="cti-search-rightbar">
          <div className="cti-search-rightbar-header">
            <div className="cti-search-rightbar-title">Saved Queries</div>
            <button type="button" className="cti-icon-button">
              <span className="material-symbols-outlined" style={{ fontSize: 20 }}>
                bookmark_add
              </span>
            </button>
          </div>
          <div className="cti-search-rightbar-body">
            <div>
              <div style={{ fontSize: 11, color: "#94a3b8", textTransform: "uppercase", marginBottom: 8 }}>
                SOC Favorites
              </div>
              <div style={{ display: "grid", gap: 8 }}>
                {savedQueries
                  .filter((queryItem) => queryItem.emphasized)
                  .map((queryItem) => (
                    <a key={queryItem.id} className="cti-query-card" href="#">
                      <span className="material-symbols-outlined" style={{ color: "#94a3b8", fontSize: 20 }}>
                        {queryItem.icon}
                      </span>
                      <div>
                        <h5>{queryItem.title}</h5>
                        <p>{queryItem.description}</p>
                      </div>
                    </a>
                  ))}
              </div>
            </div>
            <div>
              <div style={{ fontSize: 11, color: "#94a3b8", textTransform: "uppercase", marginBottom: 8 }}>
                My Queries
              </div>
              <div style={{ display: "grid", gap: 8 }}>
                {savedQueries
                  .filter((queryItem) => !queryItem.emphasized)
                  .map((queryItem) => (
                    <a key={queryItem.id} className="cti-query-card muted" href="#">
                      <span className="material-symbols-outlined" style={{ color: "#94a3b8", fontSize: 20 }}>
                        {queryItem.icon}
                      </span>
                      <div>
                        <h5>{queryItem.title}</h5>
                        <p>{queryItem.description}</p>
                      </div>
                    </a>
                  ))}
              </div>
            </div>
          </div>
          <div className="cti-save-search">
            <button type="button">
              <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
                save
              </span>
              Save Current Search
            </button>
          </div>
        </aside>
      </div>
    </div>
  );
};

export default IntelligenceSearchPage;
