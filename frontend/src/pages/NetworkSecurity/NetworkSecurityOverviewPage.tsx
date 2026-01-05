import { useEffect, useState } from "react";
import { getNetworkStats, listNetworkEvents } from "../../services/api";
import type { NetworkEvent, NetworkStats } from "../../services/api";
import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";

const NetworkSecurityOverviewPage = () => {
  const [stats, setStats] = useState<NetworkStats | null>(null);
  const [events, setEvents] = useState<NetworkEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadOverview = async () => {
    try {
      setLoading(true);
      const [statsData, eventsData] = await Promise.all([
        getNetworkStats(),
        listNetworkEvents({ size: 5 }),
      ]);
      setStats(statsData);
      setEvents(eventsData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load network stats");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOverview();
  }, []);

  return (
    <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">Network Security Overview</div>
          <div className="page-subtitle">
            Suricata + Zeek telemetry, detections, and response orchestration.
          </div>
        </div>
        <div className="stack-horizontal">
          <button type="button" className="btn btn-ghost" onClick={loadOverview}>
            Refresh
          </button>
        </div>
      </div>

      {loading && <LoadingState message="Loading network overview…" />}
      {error && <ErrorState message={error} />}

      {!loading && !error && stats && (
        <>
          <div className="grid-3">
            <div className="card">
              <div className="card-header">
                <div>
                  <div className="card-title">Events (24h)</div>
                  <div className="card-subtitle">Indexed IDS telemetry</div>
                </div>
              </div>
              <div className="card-value">{stats.events_last_24h}</div>
            </div>
            <div className="card">
              <div className="card-header">
                <div>
                  <div className="card-title">Top signatures</div>
                  <div className="card-subtitle">Suricata alert hits</div>
                </div>
              </div>
              <div className="stack-vertical">
                {stats.top_signatures.length === 0 && (
                  <div className="muted">No signature data yet.</div>
                )}
                {stats.top_signatures.map((bucket) => (
                  <div
                    key={String(bucket.key)}
                    className="stack-horizontal"
                    style={{ justifyContent: "space-between" }}
                  >
                    <span>{String(bucket.key)}</span>
                    <span>{bucket.doc_count as number}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="card">
              <div className="card-header">
                <div>
                  <div className="card-title">Top destinations</div>
                  <div className="card-subtitle">Most targeted IPs</div>
                </div>
              </div>
              <div className="stack-vertical">
                {stats.top_destinations.length === 0 && (
                  <div className="muted">No destination data yet.</div>
                )}
                {stats.top_destinations.map((bucket) => (
                  <div
                    key={String(bucket.key)}
                    className="stack-horizontal"
                    style={{ justifyContent: "space-between" }}
                  >
                    <span>{String(bucket.key)}</span>
                    <span>{bucket.doc_count as number}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <div>
                <div className="card-title">Recent IDS events</div>
                <div className="card-subtitle">Latest normalized events</div>
              </div>
            </div>
            {events.length === 0 ? (
              <EmptyState message="No network events ingested yet." />
            ) : (
              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>Time</th>
                      <th>Source</th>
                      <th>Type</th>
                      <th>Src</th>
                      <th>Dst</th>
                      <th>Severity</th>
                    </tr>
                  </thead>
                  <tbody>
                    {events.map((event) => (
                      <tr key={event.id}>
                        <td>{new Date(event.ts).toLocaleString()}</td>
                        <td>{event.source}</td>
                        <td>{event.event_type}</td>
                        <td>
                          {event.src_ip}
                          {event.src_port ? `:${event.src_port}` : ""}
                        </td>
                        <td>
                          {event.dst_ip}
                          {event.dst_port ? `:${event.dst_port}` : ""}
                        </td>
                        <td>{event.severity ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default NetworkSecurityOverviewPage;
