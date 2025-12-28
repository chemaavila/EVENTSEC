import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { startGoogleOAuthUrl, syncGoogle, type SyncResult } from "../../lib/emailProtectionApi";

type IntegrationState = {
  mailbox: string | null;
  lastSyncOk: boolean;
  lastSyncAt: number | null;
  error: string | null;
};

function lsGet(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function lsSet(key: string, value: string) {
  try {
    localStorage.setItem(key, value);
  } catch {}
}

function mailboxKey(): string | null {
  return lsGet("email_protect_mailbox");
}

function markSync(ok: boolean) {
  lsSet("email_protect_last_sync_ok", ok ? "1" : "0");
  lsSet("email_protect_last_sync_at", String(Date.now()));
}

function threatLabel(item: SyncResult): { label: string; cls: string } {
  if (item.attachments?.length > 0) return { label: "Malware", cls: "severity-pill severity-high" };
  if (item.urls?.length > 0) return { label: "Phishing", cls: "severity-pill severity-critical" };
  if ((item.score ?? 0) > 0 || (item.verdict || "").toLowerCase() !== "low") return { label: "Suspicious", cls: "severity-pill severity-medium" };
  return { label: "Low", cls: "severity-pill severity-low" };
}

function actionLabel(item: SyncResult): string {
  const score = item.score ?? 0;
  if (score >= 70) return "Blocked";
  if (score >= 40) return "Quarantined";
  return "Filtered";
}

export default function EmailSecurityDashboardPage() {
  const [rows, setRows] = useState<SyncResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [integration, setIntegration] = useState<IntegrationState>(() => ({
    mailbox: mailboxKey(),
    lastSyncOk: lsGet("email_protect_last_sync_ok") === "1",
    lastSyncAt: (() => {
      const v = lsGet("email_protect_last_sync_at");
      return v ? Number(v) : null;
    })(),
    error: null,
  }));

  const connected = Boolean(integration.mailbox) && integration.lastSyncOk;

  const doSync = useCallback(async () => {
    const mailbox = mailboxKey();
    if (!mailbox) return;
    setLoading(true);
    try {
      const res = await syncGoogle(mailbox, 10);
      setRows(res.results || []);
      markSync(true);
      setIntegration((s) => ({ ...s, mailbox, lastSyncOk: true, lastSyncAt: Date.now(), error: null }));
    } catch (e: any) {
      markSync(false);
      setIntegration((s) => ({
        ...s,
        mailbox,
        lastSyncOk: false,
        lastSyncAt: Date.now(),
        error: String(e?.message || e),
      }));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (mailboxKey()) void doSync();
  }, [doSync]);

  const processed24h = rows.length;
  const blocked = useMemo(() => rows.filter((r) => (r.score ?? 0) >= 70).length, [rows]);
  const mostTargeted = useMemo(() => (integration.mailbox ? [{ email: integration.mailbox, count: rows.length }] : []), [integration.mailbox, rows.length]);

  return (
    <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">Email security</div>
          <div className="page-subtitle">
            Google OAuth + mailbox sync via the Email Protection service.
          </div>
        </div>
        <div className="stack-horizontal">
          <Link to="/email-security/settings" className="btn btn-ghost btn-sm">
            Settings
          </Link>
          {integration.mailbox ? (
            <button className="btn btn-sm" type="button" onClick={doSync} disabled={loading}>
              {loading ? "Syncing…" : "Sync"}
            </button>
          ) : (
            <button className="btn btn-sm" type="button" onClick={() => (window.location.href = startGoogleOAuthUrl())}>
              Connect Google
            </button>
          )}
        </div>
      </div>

      <div className="grid-4">
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Processed emails (24h)</div>
              <div className="card-subtitle">From last sync results</div>
            </div>
          </div>
          <div className="card-value">{processed24h}</div>
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Blocked</div>
              <div className="card-subtitle">Score ≥ 70</div>
            </div>
          </div>
          <div className="card-value">{blocked}</div>
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Most targeted users</div>
              <div className="card-subtitle">Mailbox (demo)</div>
            </div>
          </div>
          <div className="stack-vertical">
            {mostTargeted.length ? (
              mostTargeted.map((u) => (
                <div key={u.email} className="stack-horizontal" style={{ justifyContent: "space-between" }}>
                  <span className="muted">{u.email}</span>
                  <span className="badge">{u.count}</span>
                </div>
              ))
            ) : (
              <div className="muted">No mailbox linked.</div>
            )}
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Integration</div>
              <div className="card-subtitle">Google workspace</div>
            </div>
          </div>
          <div className="stack-vertical">
            <div className="stack-horizontal">
              <div className="pill">
                <span className="pill-dot" />
                {connected ? "Connected" : "Disconnected"}
              </div>
              {integration.mailbox ? <span className="tag">{integration.mailbox}</span> : null}
            </div>
            {integration.error ? <div className="muted">Last error: {integration.error}</div> : null}
            {!integration.mailbox ? (
              <button className="btn btn-sm" type="button" onClick={() => (window.location.href = startGoogleOAuthUrl())}>
                Connect Google
              </button>
            ) : null}
          </div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Threat volume</div>
              <div className="card-subtitle">Simple trend (SVG)</div>
            </div>
          </div>
          <svg width="100%" height="140" viewBox="0 0 600 140" preserveAspectRatio="none">
            <defs>
              <linearGradient id="epChart" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor="rgba(59,130,246,0.35)" />
                <stop offset="100%" stopColor="rgba(59,130,246,0)" />
              </linearGradient>
            </defs>
            <path d="M0,90 C60,20 120,120 180,70 C240,20 300,120 360,65 C420,25 480,90 540,45 C560,35 580,45 600,50 L600,140 L0,140 Z" fill="url(#epChart)" />
            <path d="M0,90 C60,20 120,120 180,70 C240,20 300,120 360,65 C420,25 480,90 540,45 C560,35 580,45 600,50" stroke="rgba(59,130,246,0.95)" strokeWidth="3" fill="none" strokeLinecap="round" />
          </svg>
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Spoofing attempts</div>
              <div className="card-subtitle">Score & verdict based</div>
            </div>
          </div>
          <div className="card-value">{rows.filter((r) => (r.score ?? 0) > 0).length}</div>
          <div className="muted small">Derived from synced messages.</div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">Recent activity</div>
            <div className="card-subtitle">Last synced messages</div>
          </div>
          <div className="stack-horizontal">
            {integration.mailbox ? (
              <button className="btn btn-ghost btn-sm" type="button" onClick={doSync} disabled={loading}>
                {loading ? "Syncing…" : "Refresh"}
              </button>
            ) : null}
          </div>
        </div>

        {!integration.mailbox ? (
          <div className="muted">
            No mailbox linked. Go to <Link to="/email-security/settings">Settings</Link> to save mailbox after OAuth.
          </div>
        ) : null}

        {integration.error ? <div className="muted">Error: {integration.error}</div> : null}

        <div className="table-responsive">
          <table className="table">
            <thead>
              <tr>
                <th>From</th>
                <th>Recipient</th>
                <th>Subject</th>
                <th>Threat</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {rows.length ? (
                rows.map((item) => {
                  const threat = threatLabel(item);
                  return (
                    <tr key={item.message_id}>
                      <td>{item.from}</td>
                      <td>{integration.mailbox}</td>
                      <td>{item.subject}</td>
                      <td>
                        <span className={threat.cls}>{threat.label}</span>
                      </td>
                      <td>
                        <span className="badge">{actionLabel(item)}</span>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={5} className="muted">
                    {loading ? "Loading…" : "No messages yet. Click Sync."}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}


