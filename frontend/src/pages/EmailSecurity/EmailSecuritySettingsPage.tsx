import { useEffect, useMemo, useState } from "react";
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

function lsGetList(key: string): string[] {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.filter((v) => typeof v === "string") : [];
  } catch {
    return [];
  }
}

function normalizeMailbox(value: string): string {
  return value.trim().toLowerCase();
}

export default function EmailSecuritySettingsPage() {
  const [clientId, setClientId] = useState(() => lsGet("email_protect_client_id"));
  const [clientSecret, setClientSecret] = useState(() => lsGet("email_protect_client_secret"));
  const [mailbox, setMailbox] = useState(() => lsGet("email_protect_mailbox"));
  const [mailboxes, setMailboxes] = useState<string[]>(() => lsGetList("email_protect_mailboxes"));
  const [newMailbox, setNewMailbox] = useState("");
  const [status, setStatus] = useState<{ ok: boolean; msg: string } | null>(null);
  const [testing, setTesting] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const connected = Boolean(mailbox);
  const lastSync = useMemo(() => {
    const v = lsGet("email_protect_last_sync_at");
    const n = v ? Number(v) : 0;
    return n ? new Date(n).toLocaleString() : "—";
  }, [status]);

  useEffect(() => {
    const normalized = normalizeMailbox(mailbox);
    if (normalized && !mailboxes.includes(normalized)) {
      storeMailboxes([...mailboxes, normalized]);
    }
  }, [mailbox, mailboxes]);

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

  function storeMailboxes(next: string[]) {
    const unique = Array.from(new Set(next));
    setMailboxes(unique);
    lsSet("email_protect_mailboxes", JSON.stringify(unique));
  }

  function addMailbox() {
    const normalized = normalizeMailbox(newMailbox);
    if (!normalized) {
      setStatus({ ok: false, msg: "Enter an email to add." });
      return;
    }
    const next = Array.from(new Set([...mailboxes, normalized]));
    storeMailboxes(next);
    lsSet("email_protect_mailbox", normalized);
    setMailbox(normalized);
    setNewMailbox("");
    setStatus({ ok: true, msg: `Added ${normalized} as the active mailbox.` });
  }

  function activateMailbox(value: string) {
    lsSet("email_protect_mailbox", value);
    setMailbox(value);
    setStatus({ ok: true, msg: `Active mailbox set to ${value}.` });
  }

  function removeMailbox(value: string) {
    const next = mailboxes.filter((item) => item !== value);
    storeMailboxes(next);
    if (mailbox === value) {
      const fallback = next[0] || "";
      lsSet("email_protect_mailbox", fallback);
      setMailbox(fallback);
    }
    setStatus({ ok: true, msg: `Removed ${value}.` });
  }

  function saveConfig() {
    lsSet("email_protect_client_id", clientId);
    lsSet("email_protect_client_secret", clientSecret);
    const normalized = normalizeMailbox(mailbox);
    if (normalized) {
      const next = Array.from(new Set([...mailboxes, normalized]));
      storeMailboxes(next);
      lsSet("email_protect_mailbox", normalized);
      setMailbox(normalized);
    }
    setStatus({ ok: true, msg: "Settings saved." });
  }

  function deleteIntegration() {
    lsDel("email_protect_mailbox");
    lsDel("email_protect_last_sync_ok");
    lsDel("email_protect_last_sync_at");
    lsDel("email_protect_mailboxes");
    setMailbox("");
    setMailboxes([]);
    setStatus({ ok: true, msg: "Integration removed." });
  }

  return (
    <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">Email security settings</div>
          <div className="page-subtitle">
            Connect Google once, then add people by email.
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
              <div className="card-title">People protected</div>
              <div className="card-subtitle">Add mailboxes and choose who to sync</div>
            </div>
            <button className="btn btn-ghost btn-sm" type="button" onClick={() => setShowAdvanced((v) => !v)}>
              {showAdvanced ? "Hide advanced" : "Show advanced"}
            </button>
          </div>

          <div className="stack-vertical">
            <label className="field">
              <span>Add person (email)</span>
              <div className="stack-horizontal">
                <input value={newMailbox} onChange={(e) => setNewMailbox(e.target.value)} placeholder="person@company.com" />
                <button className="btn btn-sm" type="button" onClick={addMailbox}>
                  Add
                </button>
              </div>
            </label>
            {mailboxes.length ? (
              <div className="stack-vertical">
                {mailboxes.map((item) => (
                  <div key={item} className="stack-horizontal" style={{ justifyContent: "space-between" }}>
                    <span className="muted">{item}</span>
                    <div className="stack-horizontal">
                      {mailbox === item ? <span className="badge">Active</span> : null}
                      {mailbox !== item ? (
                        <button className="btn btn-ghost btn-sm" type="button" onClick={() => activateMailbox(item)}>
                          Make active
                        </button>
                      ) : null}
                      <button className="btn btn-ghost btn-sm" type="button" onClick={() => removeMailbox(item)}>
                        Remove
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="muted small">No people added yet.</div>
            )}
            <div className="muted small">
              Active mailbox: {mailbox || "Not selected"} • Last sync: {lastSync}
            </div>
            <div className="stack-horizontal">
              <button className="btn btn-sm" type="button" onClick={() => (window.location.href = startGoogleOAuthUrl())}>
                Connect Google
              </button>
              <button className="btn btn-ghost btn-sm" type="button" onClick={testConnection} disabled={testing}>
                {testing ? "Testing…" : "Test connection"}
              </button>
            </div>
            <div className="stack-horizontal">
              <button className="btn btn-sm" type="button" onClick={saveConfig}>
                Save settings
              </button>
              <button className="btn btn-danger btn-sm" type="button" onClick={deleteIntegration}>
                Delete integration
              </button>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Advanced (optional)</div>
              <div className="card-subtitle">Only needed for custom OAuth apps</div>
            </div>
          </div>

          {showAdvanced ? (
            <div className="stack-vertical">
              <label className="field">
                <span>Client ID</span>
                <input value={clientId} onChange={(e) => setClientId(e.target.value)} placeholder="email_protect_client_id" />
              </label>
              <label className="field">
                <span>Client Secret</span>
                <input value={clientSecret} onChange={(e) => setClientSecret(e.target.value)} placeholder="email_protect_client_secret" type="password" />
              </label>
              <label className="field">
                <span>Manual mailbox</span>
                <input value={mailbox} onChange={(e) => setMailbox(e.target.value)} placeholder="user@company.com" />
              </label>
              <div className="muted small">
                Use this only if you need to paste a mailbox directly from OAuth JSON.
              </div>
            </div>
          ) : (
            <div className="muted small">Advanced settings are hidden to keep setup simple.</div>
          )}
        </div>
      </div>
    </div>
  );
}
