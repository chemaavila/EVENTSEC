import { useCallback, useEffect, useMemo, useState } from "react";
import CtiAdapterFallback from "../../components/cti/CtiAdapterFallback";
import ctiAdapter from "../../services/cti";
import { CtiNotImplementedError } from "../../services/cti/apiAdapter";
import type { CtiSearchData, CtiSearchResult } from "../../services/cti";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";

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
    title: "High Conf Ransomware",
    description: "Indicators > 80%",
  },
  {
    id: "soc-2",
    title: "APT29 Campaign",
    description: "Source: CrowdStrike",
  },
  {
    id: "my-1",
    title: "New Domains (24h)",
    description: "Created < 1 day",
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

const typeLabelForIcon = (icon: string) => {
  const mapping: Record<string, string> = {
    public: "IP Address",
    language: "Domain",
    fingerprint: "File Hash",
    alternate_email: "Email",
    link: "URL",
  };
  return mapping[icon] ?? "Indicator";
};

const IntelligenceSearchPage = () => {
  const [searchData, setSearchData] = useState<CtiSearchData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState(defaultFilters);
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [adapterUnavailable, setAdapterUnavailable] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedQuery(query), 400);
    return () => window.clearTimeout(timer);
  }, [query]);

  const loadSearch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await ctiAdapter.getSearchResults();
      setSearchData(data);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err) {
      console.error(err);
      if (err instanceof CtiNotImplementedError) {
        setAdapterUnavailable(true);
        return;
      }
      setError("Unable to load intelligence results.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSearch();
  }, [loadSearch]);

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
    if (tlp === "red") return "var(--palette-ef4444)";
    if (tlp === "amber") return "var(--palette-f59e0b)";
    if (tlp === "green") return "var(--palette-22c55e)";
    return "var(--palette-94a3b8)";
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
    <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">Threat Intelligence Search</div>
          <div className="page-subtitle">
            Search and triage intelligence entities across sources and confidence bands.
          </div>
        </div>
        <div className="stack-horizontal">
          {lastUpdated && <span className="muted small">Updated {lastUpdated}</span>}
          <button type="button" className="btn btn-ghost" onClick={loadSearch} disabled={loading}>
            {loading ? "Refreshing…" : "Refresh"}
          </button>
        </div>
      </div>

      {error && (
        <ErrorState
          message="Unable to load intelligence results."
          details={error}
          onRetry={loadSearch}
        />
      )}

      <div className="grid-2">
        <div className="stack-vertical">
          <div className="card">
            <div className="card-header">
              <div>
                <div className="card-title">Search query</div>
                <div className="card-subtitle">Use KQL-inspired syntax to filter results.</div>
              </div>
            </div>
            <div className="stack-vertical">
              <input
                className="field-control"
                placeholder="Search entities, campaigns, or indicators..."
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
              {kqlError && (
                <div className="muted" style={{ color: "var(--danger)" }}>
                  Query contains unmatched parentheses.
                </div>
              )}
              <div className="stack-horizontal" style={{ flexWrap: "wrap" }}>
                {appliedFilters.map((filter) => (
                  <span key={filter.key} className="tag">
                    {filter.label}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <div>
                <div className="card-title">Saved queries</div>
                <div className="card-subtitle">Quick access to analyst workflows.</div>
              </div>
            </div>
            <div className="stack-vertical">
              {savedQueries.map((queryItem) => (
                <div key={queryItem.id} className="card-inline">
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600 }}>{queryItem.title}</div>
                    <div className="muted small">{queryItem.description}</div>
                  </div>
                  <button type="button" className="btn btn-sm btn-ghost">
                    Run
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <div>
                <div className="card-title">Filters</div>
                <div className="card-subtitle">Tune relevance and enrichment sources.</div>
              </div>
              <button type="button" className="btn btn-sm btn-ghost" onClick={() => setFilters(defaultFilters)}>
                Reset
              </button>
            </div>
            <div className="stack-vertical">
              <div className="field-group">
                <div className="field-label">Entity type</div>
                <div className="stack-vertical">
                  {Object.keys(filters.entityTypes).map((label) => (
                    <label key={label} className="checkbox">
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

              <div className="field-group">
                <div className="field-label">Confidence threshold</div>
                <input
                  className="field-control"
                  type="range"
                  min={0}
                  max={100}
                  value={filters.confidence}
                  onChange={(event) =>
                    setFilters((prev) => ({ ...prev, confidence: Number(event.target.value) }))
                  }
                />
                <div className="muted small">Current: {filters.confidence}%</div>
              </div>

              <div className="field-group">
                <label className="field-label" htmlFor="cti-source">
                  Source
                </label>
                <input
                  id="cti-source"
                  className="field-control"
                  value={filters.source}
                  onChange={(event) =>
                    setFilters((prev) => ({ ...prev, source: event.target.value }))
                  }
                  placeholder="CrowdStrike, Mandiant..."
                />
              </div>

              <div className="grid-2">
                <div className="field-group">
                  <label className="field-label" htmlFor="cti-reliability">
                    Reliability
                  </label>
                  <select
                    id="cti-reliability"
                    className="field-control"
                    value={filters.reliability}
                    onChange={(event) =>
                      setFilters((prev) => ({ ...prev, reliability: event.target.value }))
                    }
                  >
                    <option>A - Completely Reliable</option>
                    <option>B - Usually Reliable</option>
                    <option>C - Fairly Reliable</option>
                  </select>
                </div>
                <div className="field-group">
                  <label className="field-label" htmlFor="cti-tlp">
                    TLP
                  </label>
                  <select
                    id="cti-tlp"
                    className="field-control"
                    value={filters.tlp}
                    onChange={(event) => setFilters((prev) => ({ ...prev, tlp: event.target.value }))}
                  >
                    <option>RED</option>
                    <option>AMBER</option>
                    <option>GREEN</option>
                    <option>CLEAR</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Search results</div>
              <div className="card-subtitle">
                {loading
                  ? "Fetching intelligence results…"
                  : `${total} results in ${duration.toFixed(2)}s`}
              </div>
            </div>
          </div>

          {loading ? (
            <LoadingState message="Loading results…" />
          ) : results.length === 0 ? (
            <div className="muted">No results match the current filters.</div>
          ) : (
            <div className="table-responsive">
              <table className="table">
                <thead>
                  <tr>
                    <th>Entity</th>
                    <th>Type</th>
                    <th>Confidence</th>
                    <th>TLP</th>
                    <th>Source</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((result) => (
                    <tr key={result.id}>
                      <td>
                        <div style={{ fontWeight: 600 }}>{result.value}</div>
                        <div className="muted small">{result.summary}</div>
                      </td>
                      <td>{typeLabelForIcon(result.typeIcon)}</td>
                      <td>{result.confidence.label}</td>
                      <td>
                        <span className="tag" style={{ borderColor: renderTlpDot(result.tlp) }}>
                          {result.tlp.toUpperCase()}
                        </span>
                      </td>
                      <td>{result.source}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default IntelligenceSearchPage;
