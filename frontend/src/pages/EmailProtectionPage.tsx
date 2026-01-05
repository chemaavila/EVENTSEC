import { useEffect, useMemo, useState } from "react";
import { useLocation } from "react-router-dom";
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
  const [wizardOpen, setWizardOpen] = useState(false);
  const [contextAlertId, setContextAlertId] = useState("");
  const [contextCaseId, setContextCaseId] = useState("");
  const [iocInputs, setIocInputs] = useState({
    url: "",
    domain: "",
    ip: "",
    hash: "",
    email: "",
  });
  const [keywords, setKeywords] = useState("");
  const [generatedQuery, setGeneratedQuery] = useState("");
  const { pushToast } = useToast();
  const location = useLocation();

  useEffect(() => {
    setStatus("ready");
    const params = new URLSearchParams(location.search);
    const alertId = params.get("alert_id") ?? "";
    const caseId = params.get("case_id") ?? "";
    if (alertId) setContextAlertId(alertId);
    if (caseId) setContextCaseId(caseId);
    if (alertId || caseId) {
      setWizardOpen(true);
    }
  }, [location.search]);

  const queryParts = useMemo(() => {
    const parts: string[] = [];
    if (contextAlertId.trim()) parts.push(`alert_id:${contextAlertId.trim()}`);
    if (contextCaseId.trim()) parts.push(`case_id:${contextCaseId.trim()}`);
    Object.entries(iocInputs).forEach(([type, value]) => {
      value
        .split(/\n|,/)
        .map((entry) => entry.trim())
        .filter(Boolean)
        .forEach((entry) => parts.push(`${type}:${entry}`));
    });
    if (keywords.trim()) parts.push(keywords.trim());
    return parts;
  }, [contextAlertId, contextCaseId, iocInputs, keywords]);

  const googleLinks = useMemo(() => {
    const query = queryParts.join(" ");
    const encoded = encodeURIComponent(query);
    return {
      query,
      google: `https://www.google.com/search?q=${encoded}`,
      gmail: `https://mail.google.com/mail/u/0/#search/${encoded}`,
      drive: `https://drive.google.com/drive/search?q=${encoded}`,
    };
  }, [queryParts]);

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

      <div className="card">
        <div className="stack-horizontal" style={{ justifyContent: "space-between" }}>
          <h3>Quick links wizard (Google first)</h3>
          <button
            type="button"
            className="btn btn-ghost"
            onClick={() => setWizardOpen((prev) => !prev)}
          >
            {wizardOpen ? "Hide wizard" : "Open wizard"}
          </button>
        </div>

        {wizardOpen && (
          <div className="stack-vertical">
            <div className="grid-2">
              <div className="field-group">
                <label className="field-label">Alert ID</label>
                <input
                  className="field-control"
                  value={contextAlertId}
                  onChange={(event) => setContextAlertId(event.target.value)}
                  placeholder="e.g. 1042"
                />
              </div>
              <div className="field-group">
                <label className="field-label">Case ID</label>
                <input
                  className="field-control"
                  value={contextCaseId}
                  onChange={(event) => setContextCaseId(event.target.value)}
                  placeholder="e.g. CASE-7781"
                />
              </div>
            </div>

            <div className="grid-2">
              <div className="field-group">
                <label className="field-label">URLs</label>
                <textarea
                  className="field-control"
                  rows={3}
                  value={iocInputs.url}
                  onChange={(event) =>
                    setIocInputs((prev) => ({ ...prev, url: event.target.value }))
                  }
                  placeholder="https://example.com"
                />
              </div>
              <div className="field-group">
                <label className="field-label">Domains</label>
                <textarea
                  className="field-control"
                  rows={3}
                  value={iocInputs.domain}
                  onChange={(event) =>
                    setIocInputs((prev) => ({ ...prev, domain: event.target.value }))
                  }
                  placeholder="example.com"
                />
              </div>
            </div>

            <div className="grid-2">
              <div className="field-group">
                <label className="field-label">IPs</label>
                <textarea
                  className="field-control"
                  rows={2}
                  value={iocInputs.ip}
                  onChange={(event) =>
                    setIocInputs((prev) => ({ ...prev, ip: event.target.value }))
                  }
                  placeholder="192.168.1.10"
                />
              </div>
              <div className="field-group">
                <label className="field-label">Hashes</label>
                <textarea
                  className="field-control"
                  rows={2}
                  value={iocInputs.hash}
                  onChange={(event) =>
                    setIocInputs((prev) => ({ ...prev, hash: event.target.value }))
                  }
                  placeholder="SHA256..."
                />
              </div>
            </div>

            <div className="grid-2">
              <div className="field-group">
                <label className="field-label">Email addresses</label>
                <textarea
                  className="field-control"
                  rows={2}
                  value={iocInputs.email}
                  onChange={(event) =>
                    setIocInputs((prev) => ({ ...prev, email: event.target.value }))
                  }
                  placeholder="user@example.com"
                />
              </div>
              <div className="field-group">
                <label className="field-label">Keywords</label>
                <input
                  className="field-control"
                  value={keywords}
                  onChange={(event) => setKeywords(event.target.value)}
                  placeholder="invoice, urgent, password reset"
                />
              </div>
            </div>

            <button
              type="button"
              className="btn btn-sm"
              onClick={() => {
                if (!queryParts.length) {
                  pushToast({
                    title: "Add context first",
                    message: "Provide at least one IOC, keyword, or context id.",
                    variant: "warning",
                  });
                  return;
                }
                setGeneratedQuery(googleLinks.query);
              }}
            >
              Generate Google links
            </button>

            {generatedQuery && (
              <div className="stack-vertical">
                <div className="muted">Query: {generatedQuery}</div>
                <div className="stack-horizontal">
                  <button
                    type="button"
                    className="btn btn-ghost"
                    onClick={async () => {
                      try {
                        await navigator.clipboard.writeText(generatedQuery);
                        pushToast({
                          title: "Query copied",
                          message: "Search query copied to clipboard.",
                          variant: "success",
                        });
                      } catch (err) {
                        pushToast({
                          title: "Copy failed",
                          message: "Unable to copy query.",
                          details: err instanceof Error ? err.message : "Unknown error",
                          variant: "error",
                        });
                      }
                    }}
                  >
                    Copy query
                  </button>
                  <a
                    className="btn btn-sm"
                    href={googleLinks.google}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Google search
                  </a>
                  <a
                    className="btn btn-sm"
                    href={googleLinks.gmail}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Gmail search
                  </a>
                  <a
                    className="btn btn-sm"
                    href={googleLinks.drive}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Drive search
                  </a>
                  <button type="button" className="btn btn-ghost" disabled>
                    Microsoft 365 (coming next)
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default EmailProtectionPage;
