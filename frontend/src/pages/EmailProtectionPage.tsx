import { useEffect, useState } from "react";
import {
  startGoogleOAuthUrl,
  startMicrosoftOAuthUrl,
  syncGoogle,
} from "../lib/emailProtectionApi";
import { useToast } from "../components/common/ToastProvider";

const EmailProtectionPage = () => {
  const [status, setStatus] = useState("idle");
  const [mailbox, setMailbox] = useState("demo@gmail.com");
  const [syncing, setSyncing] = useState(false);
  const { pushToast } = useToast();

  useEffect(() => {
    setStatus("ready");
  }, []);

  return (
    <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">Email Protection</div>
          <div className="page-subtitle">
            OAuth connectors for Gmail and Microsoft 365 plus phishing analysis.
          </div>
        </div>
      </div>

      <div className="card">
        <h3>How it works</h3>
        <p>
          The Email Protection service runs as a companion FastAPI container on port 8100. It holds
          refresh tokens for Gmail/Microsoft, exposes sync endpoints, and returns phishing verdicts for
          each message by scoring URLs, attachments, and reply-to mismatches.
        </p>
        <p>
          Use the OAuth flows under <code>/auth/google/start</code> and <code>/auth/microsoft/start</code>
          to seed tokens, then hit <code>/sync/google</code> or <code>/sync/microsoft</code> to fetch
          recent inbox data. The service also supports webhook subscriptions and Pub/Sub callbacks.
        </p>
      </div>

      <div className="card">
        <h3>Configuration</h3>
        <ul>
          <li>Set <code>EMAIL_PROTECT_GOOGLE_CLIENT_ID</code> / <code>_CLIENT_SECRET</code> and redirect URI.</li>
          <li>Set <code>EMAIL_PROTECT_MS_CLIENT_ID</code> / <code>_CLIENT_SECRET</code> / <code>_TENANT</code>.</li>
          <li>Optionally override <code>EMAIL_PROTECT_APP_BASE_URL</code> / <code>EMAIL_PROTECT_PUBLIC_BASE_URL</code>.</li>
        </ul>
        <p>
          Environment variables can be supplied via <code>docker compose</code>; see
          <code>docker-compose.yml</code> for the full list.
        </p>
      </div>

      <div className="card">
        <h3>Quick links</h3>
        <ul>
          <li>
            <a href={startGoogleOAuthUrl()} target="_blank" rel="noopener noreferrer">
              Start Google OAuth flow
            </a>
          </li>
          <li>
            <a href={startMicrosoftOAuthUrl()} target="_blank" rel="noopener noreferrer">
              Start Microsoft OAuth flow
            </a>
          </li>
        </ul>
        <div className="stack-vertical" style={{ marginTop: "1rem" }}>
          <div className="field-group">
            <label htmlFor="email-protect-mailbox" className="field-label">
              Mailbox for sync
            </label>
            <input
              id="email-protect-mailbox"
              className="field-control"
              value={mailbox}
              onChange={(event) => setMailbox(event.target.value)}
              placeholder="analyst@company.com"
            />
          </div>
          <button
            type="button"
            className="btn btn-sm"
            disabled={syncing || !mailbox.trim()}
            onClick={async () => {
              try {
                setSyncing(true);
                const response = await syncGoogle(mailbox.trim(), 5);
                setStatus(`Last sync: ${response.count} message(s)`);
              } catch (err) {
                const details = err instanceof Error ? err.message : "Unknown error";
                pushToast({
                  title: "Gmail sync failed",
                  message: "Please verify mailbox and connector configuration.",
                  details,
                  variant: "error",
                });
              } finally {
                setSyncing(false);
              }
            }}
          >
            {syncing ? "Syncing…" : "Trigger Gmail sync"}
          </button>
        </div>
        <p>Status: {status}</p>
      </div>
    </div>
  );
};

export default EmailProtectionPage;
