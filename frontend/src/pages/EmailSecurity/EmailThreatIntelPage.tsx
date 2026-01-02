import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { syncGoogle, syncMicrosoft } from "../../lib/emailProtectionApi";

type Provider = "google" | "microsoft";
type TabKey = "quarantine" | "blocked" | "spoofing" | "all";
type ScoreFilter = "all" | "40" | "70";
type EmailRow = Record<string, any>;

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

function normalizeProvider(v: string | null): Provider {
  return v === "microsoft" ? "microsoft" : "google";
}

function safeDateLabel(row: EmailRow): string {
  const raw = row?.received_at || row?.parsed_at || row?.ts || row?.date;
  const d = raw ? new Date(raw) : null;
  if (!d || Number.isNaN(d.getTime())) return "—";
  return d.toLocaleString();
}

function scoreOf(row: EmailRow): number {
  const n = Number(row?.score ?? 0);
  return Number.isFinite(n) ? n : 0;
}

function includesCI(haystack: unknown, needle: string): boolean {
  if (!needle) return true;
  if (typeof haystack !== "string") return false;
  return haystack.toLowerCase().includes(needle.toLowerCase());
}

function threatType(row: EmailRow): "Malware" | "Phishing" | "Spoofing" | "Suspicious" | "Low" {
  const verdict = String(row?.verdict ?? "").toLowerCase();
  const urls = row?.urls;
  const attachments = row?.attachments;

  if (Array.isArray(attachments) && attachments.length > 0) return "Malware";
  if (verdict.includes("malware")) return "Malware";

  if (Array.isArray(urls) && urls.length > 0) return "Phishing";
  if (verdict.includes("phish")) return "Phishing";

  if (verdict.includes("spoof")) return "Spoofing";

  if (scoreOf(row) > 0 || verdict.length > 0) return "Suspicious";
  return "Low";
}

// Usa clases existentes si están (si no, queda visual básico igualmente).
function scoreClass(score: number): string {
  if (score >= 70) return "severity-pill severity-critical";
  if (score >= 40) return "severity-pill severity-high";
  if (score > 0) return "severity-pill severity-medium";
  return "severity-pill severity-low";
}

export default function EmailThreatIntelPage() {
  const mailbox = lsGet("email_protect_mailbox");
  const provider = normalizeProvider(lsGet("email_protect_provider"));
  const lastSyncAt = lsGet("email_protect_last_sync_at");

  const [rows, setRows] = useState<EmailRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState<TabKey>("quarantine");
  const [search, setSearch] = useState("");
  const [scoreFilter, setScoreFilter] = useState<ScoreFilter>("all");
  const [status, setStatus] = useState<{ ok: boolean; msg: string } | null>(null);

  const extractRows = (res: any): EmailRow[] => {
    // Contrato esperado: res.results = array
    // Si tu API devuelve otra clave, ajústala aquí SIN romper el resto del componente.
    const arr = res?.results ?? res?.rows ?? [];
    return Array.isArray(arr) ? arr : [];
  };

  const doSync = useCallback(async () => {
    if (!mailbox) return;
    setLoading(true);
    setStatus(null);

    try {
      const res =
        provider === "microsoft"
          ? await syncMicrosoft(mailbox, 50)
          : await syncGoogle(mailbox, 50);

      const next = extractRows(res);
      setRows(next);

      lsSet("email_protect_last_sync_ok", "1");
      lsSet("email_protect_last_sync_at", String(Date.now()));
      setStatus({ ok: true, msg: "Sync OK. Results updated." });
    } catch (e: any) {
      lsSet("email_protect_last_sync_ok", "0");
      lsSet("email_protect_last_sync_at", String(Date.now()));
      setRows([]);
      setStatus({ ok: false, msg: `Sync failed: ${String(e?.message || e)}` });
    } finally {
      setLoading(false);
    }
  }, [mailbox, provider]);

  useEffect(() => {
    if (mailbox) void doSync();
  }, [mailbox, doSync]);

  const filtered = useMemo(() => {
    let data = [...rows];

    // tab filter
    if (tab === "quarantine") {
      data = data.filter((r) => {
        const s = scoreOf(r);
        return s >= 40 && s < 70;
      });
    } else if (tab === "blocked") {
      data = data.filter((r) => scoreOf(r) >= 70);
    } else if (tab === "spoofing") {
      data = data.filter((r) => threatType(r) === "Spoofing");
    }

    // score filter
    if (scoreFilter === "40") data = data.filter((r) => scoreOf(r) >= 40);
    if (scoreFilter === "70") data = data.filter((r) => scoreOf(r) >= 70);

    // search
    const q = search.trim();
    if (q) {
      data = data.filter((r) => {
        return (
          includesCI(r?.subject, q) ||
          includesCI(r?.from, q) ||
          includesCI(r?.to, q)
        );
      });
    }

    // newest first if parseable
    data.sort((a, b) => {
      const da = Date.parse(String(a?.received_at || a?.parsed_at || a?.ts || ""));
      const db = Date.parse(String(b?.received_at || b?.parsed_at || b?.ts || ""));
      const A = Number.isFinite(da) ? da : 0;
      const B = Number.isFinite(db) ? db : 0;
      return B - A;
    });

    return data;
  }, [rows, tab, search, scoreFilter]);

  const kpiTotal = rows.length;
  const kpiQuarantine = useMemo(
    () => rows.filter((r) => scoreOf(r) >= 40 && scoreOf(r) < 70).length,
    [rows]
  );
  const kpiBlocked = useMemo(() => rows.filter((r) => scoreOf(r) >= 70).length, [rows]);
  const kpiSpoof = useMemo(() => rows.filter((r) => threatType(r) === "Spoofing").length, [rows]);

  const handleAction = async (action: "Quarantine" | "Release" | "Block sender", id: unknown) => {
    const sid = typeof id === "string" || typeof id === "number" ? String(id) : "";
    if (!sid) return;

    const ok = window.confirm(`${action}: are you sure?\n\nID: ${sid}`);
    if (!ok) return;

    // GAP: no backend endpoints yet for quarantine/release/block sender.
    // Mock-first optimistic update: remove row locally.
    setRows((prev) => prev.filter((r) => String(r?.id ?? "") !== sid));
    setStatus({ ok: true, msg: `${action} applied (mock).` });
  };

  if (!mailbox) {
    return (
      <div className="page-root">
        <div className="page-header">
          <div className="page-title-group">
            <div className="page-title">Email Threat Intelligence</div>
            <div className="page-subtitle">Mailbox not configured. Configure Email Security first.</div>
          </div>
        </div>

        <div className="card">
          <div className="card-title">Configuration required</div>
          <div className="muted" style={{ marginTop: 8 }}>
            No mailbox configured. Go to Email Security settings and configure mailbox/provider.
          </div>
          <div className="stack-horizontal" style={{ marginTop: 12, gap: 8 }}>
            <Link to="/email-security/settings" className="btn btn-sm">
              Go to Email Security settings
            </Link>
            <Link to="/email-security" className="btn btn-ghost btn-sm">
              Back to Email Security dashboard
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">Email Threat Intelligence</div>
          <div className="page-subtitle">
            Quarantine • Spoofing • Investigations • Provider: <strong>{provider}</strong>
            {lastSyncAt ? (
              <span className="muted"> • Last sync: {new Date(Number(lastSyncAt)).toLocaleString()}</span>
            ) : null}
          </div>
        </div>

        <div className="stack-horizontal" style={{ gap: 8 }}>
          <Link to="/email-security" className="btn btn-ghost btn-sm">
            Back
          </Link>
          <button className="btn btn-sm" type="button" onClick={doSync} disabled={loading}>
            {loading ? "Syncing…" : "Sync"}
          </button>
        </div>
      </div>

      {status ? (
        <div className="card">
          <div className="stack-horizontal" style={{ justifyContent: "space-between" }}>
            <div className="card-title">{status.ok ? "Success" : "Error"}</div>
            <span className="badge">{status.ok ? "OK" : "FAIL"}</span>
          </div>
          <div className="muted" style={{ marginTop: 8 }}>
            {status.msg}
          </div>
        </div>
      ) : null}

      <div className="grid-4">
        <div className="card condensed-card">
          <div className="muted small">Total (last sync)</div>
          <div className="kpi-value">{kpiTotal}</div>
          <div className="muted small">Messages analyzed</div>
        </div>
        <div className="card condensed-card">
          <div className="muted small">Quarantinable</div>
          <div className="kpi-value">{kpiQuarantine}</div>
          <div className="muted small">Score 40–69</div>
        </div>
        <div className="card condensed-card">
          <div className="muted small">Blocked</div>
          <div className="kpi-value">{kpiBlocked}</div>
          <div className="muted small">Score ≥ 70</div>
        </div>
        <div className="card condensed-card">
          <div className="muted small">Spoofing</div>
          <div className="kpi-value">{kpiSpoof}</div>
          <div className="muted small">Verdict contains spoof</div>
        </div>
      </div>

      <div className="card">
        <div
          className="stack-horizontal"
          style={{ justifyContent: "space-between", flexWrap: "wrap", gap: "0.75rem" }}
        >
          <div className="stack-horizontal" style={{ gap: "0.5rem", flexWrap: "wrap" }}>
            <button
              type="button"
              className={`btn btn-sm ${tab === "quarantine" ? "btn-primary" : "btn-ghost"}`}
              onClick={() => setTab("quarantine")}
            >
              Quarantine
            </button>
            <button
              type="button"
              className={`btn btn-sm ${tab === "blocked" ? "btn-primary" : "btn-ghost"}`}
              onClick={() => setTab("blocked")}
            >
              Blocked
            </button>
            <button
              type="button"
              className={`btn btn-sm ${tab === "spoofing" ? "btn-primary" : "btn-ghost"}`}
              onClick={() => setTab("spoofing")}
            >
              Spoofing
            </button>
            <button
              type="button"
              className={`btn btn-sm ${tab === "all" ? "btn-primary" : "btn-ghost"}`}
              onClick={() => setTab("all")}
            >
              All
            </button>
          </div>

          <div className="stack-horizontal" style={{ gap: "0.6rem", flexWrap: "wrap" }}>
            <input
              className="field-control"
              type="text"
              placeholder="Search subject/from/to…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ minWidth: 260 }}
            />
            <select
              className="field-control"
              value={scoreFilter}
              onChange={(e) => setScoreFilter(e.target.value as ScoreFilter)}
              style={{ minWidth: 180 }}
            >
              <option value="all">Score: All</option>
              <option value="40">Score: ≥ 40</option>
              <option value="70">Score: ≥ 70</option>
            </select>
          </div>
        </div>

        <div style={{ marginTop: 12 }}>
          <table className="table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Score</th>
                <th>From → To</th>
                <th>Subject</th>
                <th>Type</th>
                <th style={{ width: 260 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} className="muted small">
                    Syncing…
                  </td>
                </tr>
              ) : filtered.length ? (
                filtered.map((r, idx) => {
                  const id = String(r?.id ?? idx);
                  const s = scoreOf(r);
                  const t = threatType(r);
                  return (
                    <tr key={id}>
                      <td className="muted small">{safeDateLabel(r)}</td>
                      <td>
                        <span className={scoreClass(s)}>{Math.round(s)}</span>
                      </td>
                      <td className="muted small">
                        {String(r?.from ?? "—")} → {String(r?.to ?? "—")}
                      </td>
                      <td>{String(r?.subject ?? "—")}</td>
                      <td>{t}</td>
                      <td>
                        <div className="stack-horizontal" style={{ gap: 8, flexWrap: "wrap" }}>
                          <button
                            type="button"
                            className="btn btn-ghost btn-sm"
                            onClick={() => handleAction("Quarantine", r?.id)}
                          >
                            Quarantine
                          </button>
                          <button
                            type="button"
                            className="btn btn-ghost btn-sm"
                            onClick={() => handleAction("Release", r?.id)}
                          >
                            Release
                          </button>
                          <button
                            type="button"
                            className="btn btn-ghost btn-sm"
                            onClick={() => handleAction("Block sender", r?.id)}
                          >
                            Block sender
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={6} className="muted small">
                    No results for current filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="muted small" style={{ marginTop: 10 }}>
          GAP: acciones son mock-first (no endpoints). Ajustar cuando existan endpoints reales.
        </div>
      </div>
    </div>
  );
}
