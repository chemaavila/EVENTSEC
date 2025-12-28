import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { startGoogleOAuthUrl, syncGoogle } from "../../lib/emailProtectionApi";

function lsGet(key: string): string {
  try {
    return localStorage.getItem(key) || "";
  } catch {
    return "";
  }
}

function lsSet(key: string, value: string) {
  try {
    localStorage.setItem(key, value);
  } catch {}
}

function lsDel(key: string) {
  try {
    localStorage.removeItem(key);
  } catch {}
}

export default function EmailSecuritySettingsPage() {
  const [clientId, setClientId] = useState(() => lsGet("email_protect_client_id"));
  const [clientSecret, setClientSecret] = useState(() => lsGet("email_protect_client_secret"));
  const [mailbox, setMailbox] = useState(() => lsGet("email_protect_mailbox"));
  const [status, setStatus] = useState<{ ok: boolean; msg: string } | null>(null);
  const [testing, setTesting] = useState(false);

  const connected = Boolean(mailbox);
  const lastSync = useMemo(() => {
    const v = lsGet("email_protect_last_sync_at");
    const n = v ? Number(v) : 0;
    return n ? new Date(n).toLocaleString() : "—";
  }, [status]);

  async function testConnection() {
    if (!mailbox) {
      window.location.href = startGoogleOAuthUrl();
      return;
    }
    setTesting(true);
    try {
      await syncGoogle(mailbox, 1);
      lsSet("email_protect_last_sync_ok", "1");
      lsSet("email_protect_last_sync_at", String(Date.now()));
      setStatus({ ok: true, msg: "Connection OK. Sync top=1 succeeded." });
    } catch (e: any) {
      lsSet("email_protect_last_sync_ok", "0");
      lsSet("email_protect_last_sync_at", String(Date.now()));
      setStatus({ ok: false, msg: `Connection failed: ${String(e?.message || e)}` });
    } finally {
      setTesting(false);
    }
  }

  function saveConfig() {
    lsSet("email_protect_client_id", clientId);
    lsSet("email_protect_client_secret", clientSecret);
    lsSet("email_protect_mailbox", mailbox);
    setStatus({ ok: true, msg: "Saved to localStorage." });
  }

  function deleteIntegration() {
    lsDel("email_protect_mailbox");
    lsDel("email_protect_last_sync_ok");
    lsDel("email_protect_last_sync_at");
    setMailbox("");
    setStatus({ ok: true, msg: "Integration removed." });
  }

  return (
    <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">Email security settings</div>
          <div className="page-subtitle">
            OAuth linking + mailbox selection for the Email Protection service.
          </div>
        </div>
        <div className="stack-horizontal">
          <Link className="btn btn-ghost btn-sm" to="/email-security">
            Back to dashboard
          </Link>
        </div>
      </div>

      {status ? (
        <div className="card">
          <div className="stack-horizontal" style={{ justifyContent: "space-between" }}>
            <div className="card-title">{status.ok ? "Success" : "Error"}</div>
            <span className="badge">{connected ? "Linked" : "Not linked"}</span>
          </div>
          <div className="muted" style={{ marginTop: 8 }}>
            {status.msg}
          </div>
        </div>
      ) : null}

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Google (UI-only)</div>
              <div className="card-subtitle">Stored in localStorage (backend uses env vars)</div>
            </div>
          </div>

          <div className="stack-vertical">
            <label className="field">
              <span>Client ID</span>
              <input value={clientId} onChange={(e) => setClientId(e.target.value)} placeholder="email_protect_client_id" />
            </label>
            <label className="field">
              <span>Client Secret</span>
              <input value={clientSecret} onChange={(e) => setClientSecret(e.target.value)} placeholder="email_protect_client_secret" type="password" />
            </label>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Link + mailbox</div>
              <div className="card-subtitle">OAuth callback shows JSON; paste mailbox here</div>
            </div>
          </div>

          <div className="stack-vertical">
            <label className="field">
              <span>Mailbox</span>
              <input value={mailbox} onChange={(e) => setMailbox(e.target.value)} placeholder="user@company.com" />
            </label>
            <div className="muted small">
              Status: {connected ? "Mailbox saved" : "No mailbox"} • Last sync: {lastSync}
            </div>

            <div className="stack-horizontal">
              <button className="btn btn-sm" type="button" onClick={() => (window.location.href = startGoogleOAuthUrl())}>
                Connect / Link Google
              </button>
              <button className="btn btn-ghost btn-sm" type="button" onClick={testConnection} disabled={testing}>
                {testing ? "Testing…" : "Test connection"}
              </button>
            </div>

            <div className="stack-horizontal">
              <button className="btn btn-sm" type="button" onClick={saveConfig}>
                Save
              </button>
              <button className="btn btn-danger btn-sm" type="button" onClick={deleteIntegration}>
                Delete integration
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


