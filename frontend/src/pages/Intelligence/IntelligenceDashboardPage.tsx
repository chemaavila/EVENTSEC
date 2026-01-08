import { useCallback, useEffect, useMemo, useState } from "react";
import ctiAdapter from "../../services/cti";
import { CtiNotImplementedError } from "../../services/cti/apiAdapter";
import type { CtiDashboardData, CtiKpi, CtiStreamEvent } from "../../services/cti";
import CtiAdapterFallback from "../../components/cti/CtiAdapterFallback";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";

const trendIcon = (direction: CtiKpi["trend"]["direction"]) => {
  if (direction === "up") return "↑";
  if (direction === "down") return "↓";
  return "•";
};

const trendClass = (direction: CtiKpi["trend"]["direction"]) => {
  if (direction === "up") return "var(--success)";
  if (direction === "down") return "var(--danger)";
  return "var(--text-muted)";
};

const IntelligenceDashboardPage = () => {
  const [dashboard, setDashboard] = useState<CtiDashboardData | null>(null);
  const [streamEvents, setStreamEvents] = useState<CtiStreamEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [adapterUnavailable, setAdapterUnavailable] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await ctiAdapter.getDashboard();
      setDashboard(data);
      setStreamEvents(data.streamEvents);
      setLastUpdated(new Date().toLocaleTimeString());
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
      setStreamEvents((prev) => [event, ...prev].slice(0, 8));
    });
    return unsubscribe;
  }, [dashboard]);

  const kpis = dashboard?.kpis ?? [];
  const recentIntel = dashboard?.recentIntel ?? [];
  const topTechniques = dashboard?.topTechniques ?? [];

  const streamContent = useMemo(() => {
    if (loading) {
      return <LoadingState message="Loading intelligence stream…" />;
    }

    if (streamEvents.length === 0) {
      return <div className="muted">No stream events yet.</div>;
    }

    return (
      <div className="stack-vertical">
        {streamEvents.map((event) => (
          <div key={event.id} className="card-inline" style={{ gap: "0.75rem" }}>
            <div
              className="pill-dot"
              style={{ background: event.iconBackground, border: `1px solid ${event.iconColor}` }}
            />
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 600 }}>{event.message}</div>
              <div className="muted small">{event.timestamp}</div>
            </div>
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
    <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">Threat Intelligence Dashboard</div>
          <div className="page-subtitle">
            Unified view of live intelligence, tracked campaigns, and analyst signals.
          </div>
        </div>
        <div className="stack-horizontal">
          {lastUpdated && <span className="muted small">Updated {lastUpdated}</span>}
          <button
            type="button"
            className="btn btn-ghost"
            onClick={loadDashboard}
            disabled={loading}
          >
            {loading ? "Refreshing…" : "Refresh"}
          </button>
        </div>
      </div>

      {error && (
        <ErrorState
          message="Threat intelligence data is unavailable."
          details={error}
          onRetry={loadDashboard}
        />
      )}

      <div className="grid-4">
        {(loading ? Array.from({ length: 4 }) : kpis).map((kpi, index) => (
          <div key={"id" in (kpi ?? {}) ? kpi.id : `kpi-${index}`} className="card">
            {loading ? (
              <LoadingState message="Loading KPI…" />
            ) : (
              <>
                <div className="card-title">{(kpi as CtiKpi).label}</div>
                <div style={{ fontSize: "var(--text-2xl)", fontWeight: 600 }}>
                  {(kpi as CtiKpi).value}
                </div>
                <div className="muted small" style={{ color: trendClass((kpi as CtiKpi).trend.direction) }}>
                  {trendIcon((kpi as CtiKpi).trend.direction)} {(kpi as CtiKpi).trend.label}
                </div>
              </>
            )}
          </div>
        ))}
      </div>

      <div className="grid-2" style={{ marginTop: "1.5rem" }}>
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Live intelligence stream</div>
              <div className="card-subtitle">Real-time signals from active monitoring pipelines.</div>
            </div>
          </div>
          {streamContent}
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Recent intelligence</div>
              <div className="card-subtitle">Latest reports and analyst notes.</div>
            </div>
          </div>
          {loading ? (
            <LoadingState message="Loading recent intel…" />
          ) : recentIntel.length === 0 ? (
            <div className="muted">No intelligence reports available.</div>
          ) : (
            <div className="stack-vertical">
              {recentIntel.map((item) => (
                <div key={item.id} className="card-inline">
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600 }}>{item.title}</div>
                    <div className="muted small">{item.description}</div>
                  </div>
                  <span className="tag">{item.confidence}%</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="card" style={{ marginTop: "1.5rem" }}>
        <div className="card-header">
          <div>
            <div className="card-title">Top ATT&CK techniques</div>
            <div className="card-subtitle">Most frequent techniques in current intelligence set.</div>
          </div>
        </div>
        {loading ? (
          <LoadingState message="Loading techniques…" />
        ) : topTechniques.length === 0 ? (
          <div className="muted">No techniques ranked yet.</div>
        ) : (
          <div className="table-responsive">
            <table className="table">
              <thead>
                <tr>
                  <th>Technique</th>
                  <th>Frequency</th>
                  <th>Trend</th>
                </tr>
              </thead>
              <tbody>
                {topTechniques.map((technique) => (
                  <tr key={technique.id}>
                    <td>{technique.name}</td>
                    <td>{technique.count}</td>
                    <td className="muted small">{technique.trend}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default IntelligenceDashboardPage;
