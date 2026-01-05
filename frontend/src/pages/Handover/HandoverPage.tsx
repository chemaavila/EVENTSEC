import { useEffect, useMemo, useState } from "react";
import type { Handover, HandoverCreatePayload, UserProfile } from "../../services/api";
import { createHandover, listHandovers, listUsers } from "../../services/api";
import type { ApiError } from "../../services/http";
import { useToast } from "../../components/common/ToastProvider";
import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import { useAuth } from "../../contexts/AuthContext";

const emptyForm: HandoverCreatePayload = {
  shift_start: "",
  shift_end: "",
  alerts_summary: "",
  notes_to_next_shift: "",
};

const HandoverPage = () => {
  const [handovers, setHandovers] = useState<Handover[]>([]);
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<HandoverCreatePayload>(emptyForm);
  const [creating, setCreating] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [linksInput, setLinksInput] = useState("");
  const { pushToast } = useToast();
  const { user } = useAuth();

  const userLookup = useMemo(() => {
    return new Map(users.map((entry) => [entry.id, entry.full_name]));
  }, [users]);

  const loadHandovers = async () => {
    try {
      setLoading(true);
      const [data, userData] = await Promise.all([listHandovers(), listUsers()]);
      setHandovers(data);
      setUsers(userData);
      setError(null);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unexpected error while loading handovers"
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHandovers();
  }, []);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    try {
      setCreating(true);
      setFieldErrors({});
      const links = linksInput
        .split(",")
        .map((entry) => entry.trim())
        .filter(Boolean)
        .map((url) => ({ url }));
      await createHandover({
        ...form,
        analyst_user_id: user?.id,
        links: links.length > 0 ? links : undefined,
      });
      setForm(emptyForm);
      setLinksInput("");
      await loadHandovers();
    } catch (err) {
      const apiError = err as ApiError;
      if (apiError?.status === 422 && apiError.bodySnippet) {
        try {
          const parsed = JSON.parse(apiError.bodySnippet);
          if (Array.isArray(parsed.detail)) {
            const nextErrors: Record<string, string> = {};
            parsed.detail.forEach((entry: { loc?: string[]; msg?: string }) => {
              const field = entry.loc?.[1];
              if (field && entry.msg) {
                nextErrors[field] = entry.msg;
              }
            });
            setFieldErrors(nextErrors);
          }
        } catch (parseErr) {
          console.warn("Failed to parse validation errors", parseErr);
        }
      }
      const details = err instanceof Error ? err.message : "Unknown error";
      pushToast({
        title: "Failed to create handover",
        message: "Please review the details and try again.",
        details,
        variant: "error",
      });
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">Handover</div>
          <div className="page-subtitle">
            Register shift handovers with time window and key alerts handled.
          </div>
        </div>
        <div className="stack-horizontal">
          <div className="pill">
            <span className="pill-dot" />
            Shift documentation
          </div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Create handover</div>
              <div className="card-subtitle">
                Document the time covered, analyst and alerts handled in this shift.
              </div>
            </div>
          </div>

          <form className="stack-vertical" onSubmit={handleSubmit}>
            <div className="grid-2">
              <div className="field-group">
                <label htmlFor="shift_start" className="field-label">
                  Shift start
                </label>
                <input
                  id="shift_start"
                  name="shift_start"
                  type="datetime-local"
                  className="field-control"
                  value={form.shift_start}
                  onChange={handleChange}
                  required
                />
                {fieldErrors.shift_start && (
                  <div className="field-error">{fieldErrors.shift_start}</div>
                )}
              </div>
              <div className="field-group">
                <label htmlFor="shift_end" className="field-label">
                  Shift end
                </label>
                <input
                  id="shift_end"
                  name="shift_end"
                  type="datetime-local"
                  className="field-control"
                  value={form.shift_end}
                  onChange={handleChange}
                  required
                />
                {fieldErrors.shift_end && (
                  <div className="field-error">{fieldErrors.shift_end}</div>
                )}
              </div>
            </div>

            <div className="field-group">
              <label htmlFor="analyst" className="field-label">
                Analyst
              </label>
              <input
                id="analyst"
                name="analyst"
                className="field-control"
                value={user?.full_name ?? "Current analyst"}
                readOnly
              />
            </div>

            <div className="field-group">
              <label htmlFor="alerts_summary" className="field-label">
                Alerts summary
              </label>
              <textarea
                id="alerts_summary"
                name="alerts_summary"
                className="field-control"
                rows={3}
                value={form.alerts_summary}
                onChange={handleChange}
                placeholder="E.g. 3 phishing alerts, 1 malware incident, 2 WAF anomalies…"
              />
            </div>

            <div className="field-group">
              <label htmlFor="notes_to_next_shift" className="field-label">
                Notes to next shift
              </label>
              <textarea
                id="notes_to_next_shift"
                name="notes_to_next_shift"
                className="field-control"
                rows={4}
                value={form.notes_to_next_shift}
                onChange={handleChange}
                placeholder="Context, pending actions, customers on maintenance windows, known false positives…"
              />
              {fieldErrors.notes_to_next_shift && (
                <div className="field-error">{fieldErrors.notes_to_next_shift}</div>
              )}
            </div>

            <div className="field-group">
              <label htmlFor="links" className="field-label">
                Links
              </label>
              <input
                id="links"
                name="links"
                className="field-control"
                value={linksInput}
                onChange={(event) => setLinksInput(event.target.value)}
                placeholder="Add links separated by commas"
              />
            </div>

            <div className="stack-horizontal" style={{ justifyContent: "flex-end" }}>
              <button
                type="submit"
                className="btn btn-sm"
                disabled={creating}
              >
                {creating ? "Saving…" : "Save handover"}
              </button>
            </div>
          </form>
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Recent handovers</div>
              <div className="card-subtitle">
                Latest shifts documented in the platform.
              </div>
            </div>
          </div>

          <div className="stack-vertical">
            {loading && <LoadingState message="Loading handovers…" />}
            {error && (
              <ErrorState
                message="Failed to load handovers."
                details={error}
                onRetry={() => loadHandovers()}
              />
            )}
            {!loading && !error && handovers.length === 0 && (
              <EmptyState
                title="No handovers documented yet"
                message="Capture your first shift handover to share context."
              />
            )}
            {!loading &&
              !error &&
              handovers.map((handover) => (
                <div key={handover.id} className="alert-row">
                  <div className="alert-row-main">
                    <div className="alert-row-title">
                      {userLookup.get(handover.analyst_user_id ?? -1) ??
                        `Analyst #${handover.analyst_user_id ?? "—"}`}
                      {" "}
                      —{" "}
                      {new Date(handover.shift_start).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                      {" "}
                      to{" "}
                      {new Date(handover.shift_end).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </div>
                    <div className="alert-row-meta">
                      <span className="tag">
                        {new Date(handover.shift_start).toLocaleDateString()}
                      </span>
                      {handover.alerts_summary && (
                        <span className="tag">{handover.alerts_summary}</span>
                      )}
                    </div>
                  </div>
                  <div className="muted" style={{ maxWidth: "220px" }}>
                    {handover.notes_to_next_shift || "No additional notes."}
                  </div>
                </div>
              ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default HandoverPage;
