import { useEffect, useState } from "react";
import type { Handover, HandoverCreatePayload } from "../../services/api";
import { createHandover, listHandovers } from "../../services/api";

const emptyForm: HandoverCreatePayload = {
  shift_start: "",
  shift_end: "",
  analyst: "",
  notes: "",
  alerts_summary: "",
};

const HandoverPage = () => {
  const [handovers, setHandovers] = useState<Handover[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<HandoverCreatePayload>(emptyForm);
  const [creating, setCreating] = useState(false);

  const loadHandovers = async () => {
    try {
      setLoading(true);
      const data = await listHandovers();
      setHandovers(data);
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
      await createHandover(form);
      setForm(emptyForm);
      await loadHandovers();
    } catch (err) {
      // eslint-disable-next-line no-alert
      alert(
        `Failed to create handover: ${
          err instanceof Error ? err.message : "Unknown error"
        }`
      );
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
                value={form.analyst}
                onChange={handleChange}
                placeholder="Name or initials of the analyst"
                required
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
              <label htmlFor="notes" className="field-label">
                Notes to next shift
              </label>
              <textarea
                id="notes"
                name="notes"
                className="field-control"
                rows={4}
                value={form.notes}
                onChange={handleChange}
                placeholder="Context, pending actions, customers on maintenance windows, known false positives…"
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
            {loading && <div className="muted">Loading handovers…</div>}
            {error && (
              <div className="muted">
                Failed to load handovers:
                {" "}
                {error}
              </div>
            )}
            {!loading && !error && handovers.length === 0 && (
              <div className="muted">No handovers documented yet.</div>
            )}
            {!loading &&
              !error &&
              handovers.map((handover) => (
                <div key={handover.id} className="alert-row">
                  <div className="alert-row-main">
                    <div className="alert-row-title">
                      {handover.analyst}
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
                    {handover.notes || "No additional notes."}
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
