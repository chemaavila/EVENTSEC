import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import type { Alert, UserProfile, WarRoomNote } from "../../services/api";
import {
  blockSender,
  blockUrl,
  deleteAlert,
  createWarRoomNote,
  getAlert,
  listWarRoomNotes,
  isolateDevice,
  listUsers,
  revokeUserSession,
  escalateAlert,
  unblockSender,
  unblockUrl,
  updateAlert,
} from "../../services/api";
import { useConfirm } from "../../components/common/ConfirmDialog";
import { useToast } from "../../components/common/ToastProvider";

type TabKey = "info" | "warroom" | "utilities";

const AlertDetailPage = () => {
  const { alertId } = useParams();
  const navigate = useNavigate();
  const [alert, setAlert] = useState<Alert | null>(null);
  const [activeTab, setActiveTab] = useState<TabKey>("info");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [warRoomNotes, setWarRoomNotes] = useState<WarRoomNote[]>([]);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [escalationMessage, setEscalationMessage] = useState<string | null>(null);
  const [escalationTarget, setEscalationTarget] = useState("");
  const [escalationReason, setEscalationReason] = useState("");
  const [assigning, setAssigning] = useState(false);
  const [closing, setClosing] = useState(false);
  const [conclusion, setConclusion] = useState("");
  const [actionParams, setActionParams] = useState({
    url: "",
    sender: "",
    username: "",
    hostname: "",
  });
  const { confirm } = useConfirm();
  const { pushToast } = useToast();

  useEffect(() => {
    const idNum = Number(alertId);
    if (!Number.isFinite(idNum)) {
      setError("Invalid alert id");
      setLoading(false);
      return;
    }

    const run = async () => {
      try {
        const data = await getAlert(idNum);
        setAlert(data);
        setError(null);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Unexpected error while loading alert"
        );
      } finally {
        setLoading(false);
      }
    };

    run();
    listUsers()
      .then((res) => setUsers(res))
      .catch(() => {
        /* ignore */
      });
  }, [alertId]);

  useEffect(() => {
    if (!alert) return;
    listWarRoomNotes(alert.id)
      .then((notes) => setWarRoomNotes(notes))
      .catch(() => {
        /* ignore */
      });
  }, [alert]);

  const runAction = async (
    fn: (id: number, param: string) => Promise<void>,
    label: string,
    param: string,
    paramName: string
  ) => {
    if (!alert) return;
    if (!param || !param.trim()) {
      setActionMessage(`Error: ${paramName} is required`);
      return;
    }
    setActionMessage(null);
    try {
      await fn(alert.id, param);
      setActionMessage(`${label} executed successfully.`);
      // Clear the parameter after successful action
      setActionParams((prev) => ({ ...prev, [paramName.toLowerCase()]: "" }));
    } catch (err) {
      const details = err instanceof Error ? err.message : "Unknown error";
      setActionMessage(`Failed to execute ${label.toLowerCase()}.`);
      pushToast({
        title: `Failed to execute ${label}`,
        message: "Please review the details and try again.",
        details,
        variant: "error",
      });
    }
  };

  const handleDelete = async () => {
    if (!alert) return;
    const shouldDelete = await confirm({
      title: "Delete alert",
      message: `Are you sure you want to delete alert "${alert.title}"? This action cannot be undone.`,
      confirmLabel: "Delete",
      tone: "danger",
    });
    if (!shouldDelete) {
      return;
    }
    try {
      await deleteAlert(alert.id);
      setActionMessage("Alert deleted successfully.");
      setTimeout(() => {
        navigate("/alerts");
      }, 1000);
    } catch (err) {
      const details = err instanceof Error ? err.message : "Unknown error";
      setActionMessage("Failed to delete alert.");
      pushToast({
        title: "Failed to delete alert",
        message: "Please try again.",
        details,
        variant: "error",
      });
    }
  };

  const handleEscalate = async () => {
    if (!alert) return;
    if (!escalationTarget) {
      setEscalationMessage("Please select an analyst to escalate to.");
      return;
    }
    try {
      setEscalationMessage(null);
      await escalateAlert(alert.id, {
        escalated_to: Number(escalationTarget),
        reason: escalationReason,
      });
      setEscalationMessage("Alert escalated successfully.");
      setEscalationReason("");
    } catch (err) {
      const details = err instanceof Error ? err.message : "Unknown error";
      setEscalationMessage("Failed to escalate alert.");
      pushToast({
        title: "Failed to escalate alert",
        message: "Please try again.",
        details,
        variant: "error",
      });
    }
  };

  const handleAssignToMe = async () => {
    if (!alert || users.length === 0) return;
    const me = users.find((u) => u.email) || users[0];
    await handleAssign(me.id);
  };

  const handleAssign = async (userId: number) => {
    if (!alert) return;
    try {
      setAssigning(true);
      const updated = await updateAlert(alert.id, { assigned_to: userId, status: "in_progress" });
      setAlert(updated);
      setActionMessage("Alert assigned successfully.");
    } catch (err) {
      const details = err instanceof Error ? err.message : "Unknown error";
      setActionMessage("Failed to assign alert.");
      pushToast({
        title: "Failed to assign alert",
        message: "Please try again.",
        details,
        variant: "error",
      });
    } finally {
      setAssigning(false);
    }
  };

  const handleCloseWithConclusion = async () => {
    if (!alert) return;
    if (!conclusion.trim()) {
      setActionMessage("Conclusion is required to close the alert.");
      return;
    }
    try {
      setClosing(true);
      const updated = await updateAlert(alert.id, { status: "closed", conclusion: conclusion.trim() });
      setAlert(updated);
      setActionMessage("Alert closed.");
      setConclusion("");
    } catch (err) {
      const details = err instanceof Error ? err.message : "Unknown error";
      setActionMessage("Failed to close alert.");
      pushToast({
        title: "Failed to close alert",
        message: "Please try again.",
        details,
        variant: "error",
      });
    } finally {
      setClosing(false);
    }
  };

  const renderInfoTab = () => {
    if (!alert) return null;
    return (
      <>
        <div className="grid-2">
          <div className="stack-vertical">
            <div className="field-group">
              <div className="field-label">Title</div>
              <div style={{ fontSize: "1.25rem", fontWeight: "500" }}>{alert.title}</div>
            </div>
            <div className="field-group">
              <div className="field-label">Description</div>
              <div className="muted" style={{ fontSize: "1.1rem", lineHeight: "1.6" }}>{alert.description}</div>
            </div>
            <div className="field-group">
              <div className="field-label">Source</div>
              <div className="stack-horizontal">
                <span className="tag">{alert.source}</span>
                <span className="tag">{alert.category}</span>
              </div>
            </div>
            <div className="field-group">
              <div className="field-label">Severity & status</div>
              <div className="stack-horizontal">
                <span
                  className={[
                    "severity-pill",
                    `severity-${alert.severity}`,
                  ].join(" ")}
                >
                  {alert.severity.toUpperCase()}
                </span>
                <div
                  className={[
                    "status-pill",
                    alert.status === "in_progress"
                      ? "status-in-progress"
                      : alert.status === "closed"
                      ? "status-closed"
                      : "",
                  ].join(" ")}
                >
                  <span className="status-pill-dot" />
                  {alert.status.replace("_", " ")}
                </div>
              </div>
            </div>
          </div>

          <div className="stack-vertical">
            <div className="field-group">
              <div className="field-label">URL</div>
              <div className="muted" style={{ fontSize: "1.1rem" }}>
                {alert.url || "No URL associated to this alert."}
              </div>
            </div>
            <div className="field-group">
              <div className="field-label">Sender</div>
              <div className="muted" style={{ fontSize: "1.1rem" }}>
                {alert.sender || "No email sender associated to this alert."}
              </div>
            </div>
            <div className="field-group">
              <div className="field-label">User & host</div>
              <div className="stack-horizontal">
                <span className="tag">
                  User:
                  {" "}
                  {alert.username || "N/A"}
                </span>
                <span className="tag">
                  Host:
                  {" "}
                  {alert.hostname || "N/A"}
                </span>
              </div>
            </div>
            <div className="field-group">
              <div className="field-label">Timestamps</div>
              <div className="muted" style={{ fontSize: "1.1rem" }}>
                Created:
                {" "}
                {new Date(alert.created_at).toLocaleString()}
                <br />
                Updated:
                {" "}
                {new Date(alert.updated_at).toLocaleString()}
              </div>
            </div>
          </div>
        </div>

        <div className="card" style={{ marginTop: "1rem" }}>
          <div className="card-header">
            <div>
              <div className="card-title">Escalate alert</div>
              <div className="card-subtitle">Select a teammate or team lead to escalate this alert.</div>
            </div>
          </div>
          <div className="grid-2">
            <div className="field-group">
              <div className="field-label">Assign</div>
              <div className="stack-vertical" style={{ gap: "0.5rem" }}>
                <button type="button" className="btn btn-sm" onClick={handleAssignToMe} disabled={assigning}>
                  {assigning ? "Assigning…" : "Assign to me"}
                </button>
                <div className="stack-horizontal" style={{ gap: "0.5rem" }}>
                  <select
                    id="escalation-target"
                    className="field-control"
                    value={escalationTarget}
                    onChange={(e) => setEscalationTarget(e.target.value)}
                  >
                    <option value="">Select analyst</option>
                    {users.map((user) => (
                      <option key={user.id} value={user.id}>
                        {user.full_name}
                        {" "}
                        —
                        {" "}
                        {user.role}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    className="btn btn-ghost btn-sm"
                    onClick={() => escalationTarget && handleAssign(Number(escalationTarget))}
                    disabled={assigning || !escalationTarget}
                  >
                    {assigning ? "Assigning…" : "Assign selected"}
                  </button>
                </div>
              </div>
            </div>
            <div className="field-group">
              <label htmlFor="escalation-reason" className="field-label">
                Reason / context
              </label>
              <input
                id="escalation-reason"
                className="field-control"
                value={escalationReason}
                onChange={(e) => setEscalationReason(e.target.value)}
                placeholder="Add a note for the assignee"
              />
            </div>
          </div>
          {escalationMessage && (
            <div className="muted" style={{ color: escalationMessage.startsWith("Failed") ? "var(--danger)" : "var(--success)" }}>
              {escalationMessage}
            </div>
          )}
          <div style={{ textAlign: "right" }}>
            <button type="button" className="btn btn-sm" onClick={handleEscalate}>
              Escalate
            </button>
          </div>
        </div>

        <div className="card" style={{ marginTop: "1rem" }}>
          <div className="card-header">
            <div>
              <div className="card-title">{alert?.status === "closed" ? "Reopen alert" : "Close alert"}</div>
              <div className="card-subtitle">
                {alert?.status === "closed"
                  ? "Reopen the alert for further investigation."
                  : "Add a short conclusion to close this alert."}
              </div>
            </div>
            <div className="stack-horizontal" style={{ gap: "0.5rem", alignItems: "center" }}>
              {alert?.status !== "closed" && (
                <input
                  className="field-control"
                  placeholder="Conclusion / summary"
                  value={conclusion}
                  onChange={(e) => setConclusion(e.target.value)}
                />
              )}
              {alert?.status === "closed" ? (
                <button
                  type="button"
                  className="btn btn-primary btn-sm"
                  onClick={async () => {
                    if (!alert) return;
                    const updated = await updateAlert(alert.id, { status: "open" });
                    setAlert(updated);
                    setActionMessage("Alert reopened.");
                  }}
                >
                  Reopen alert
                </button>
              ) : (
                <button
                  type="button"
                  className="btn btn-danger btn-sm"
                  onClick={handleCloseWithConclusion}
                  disabled={closing}
                >
                  {closing ? "Closing…" : "Close alert"}
                </button>
              )}
            </div>
          </div>
          {alert?.conclusion && (
            <div className="muted">
              Last conclusion:
              {" "}
              {alert.conclusion}
            </div>
          )}
        </div>
      </>
    );
  };

  const [warRoomMessage, setWarRoomMessage] = useState<string | null>(null);
  const [warRoomContent, setWarRoomContent] = useState("");
  const [warRoomAttachment, setWarRoomAttachment] = useState("");

  const handleAddNote = async () => {
    if (!alert || !warRoomContent.trim()) {
      setWarRoomMessage("Content is required.");
      return;
    }
    try {
      const note = await createWarRoomNote({
        alert_id: alert.id,
        content: warRoomContent.trim(),
        attachments: warRoomAttachment ? [warRoomAttachment.trim()] : [],
      });
      setWarRoomNotes((prev) => [note, ...prev]);
      setWarRoomContent("");
      setWarRoomAttachment("");
      setWarRoomMessage("Note added to war room.");
    } catch (err) {
      setWarRoomMessage(
        `Failed to add note: ${err instanceof Error ? err.message : "Unknown error"}`
      );
    }
  };

  const renderWarRoomTab = () => (
    <div className="stack-vertical">
      <div className="field-group">
        <div className="field-label">Add note</div>
        <textarea
          className="field-control"
          rows={4}
          value={warRoomContent}
          onChange={(e) => setWarRoomContent(e.target.value)}
          placeholder="Shift handover, investigative notes, action items…"
        />
      </div>
      <div className="field-group">
        <label htmlFor="warroom-attachment" className="field-label">
          Attachment / document URL
        </label>
        <input
          id="warroom-attachment"
          className="field-control"
          value={warRoomAttachment}
          onChange={(e) => setWarRoomAttachment(e.target.value)}
          placeholder="https://docs.company.com/runbook.pdf"
        />
      </div>
      {warRoomMessage && (
        <div className="muted" style={{ color: warRoomMessage.startsWith("Failed") ? "var(--danger)" : "var(--success)" }}>
          {warRoomMessage}
        </div>
      )}
      <div style={{ textAlign: "right" }}>
        <button type="button" className="btn btn-sm" onClick={handleAddNote}>
          Add note
        </button>
      </div>
      <div className="stack-vertical" style={{ marginTop: "1rem" }}>
        {warRoomNotes.length === 0 ? (
          <div className="muted">No notes yet.</div>
        ) : (
          warRoomNotes.map((note) => (
            <div key={note.id} className="card sandbox-mini">
              <div className="muted small">
                {new Date(note.created_at).toLocaleString()}
                {" "}
                — author #
                {note.created_by}
              </div>
              <div>{note.content}</div>
              {note.attachments.length > 0 && (
                <div className="stack-horizontal" style={{ gap: "0.5rem", marginTop: "0.5rem" }}>
                  {note.attachments.map((attachment) => (
                    <a key={attachment} href={attachment} target="_blank" rel="noreferrer" className="link">
                      {attachment}
                    </a>
                  ))}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );

  const renderUtilitiesTab = () => (
    <div className="grid-2">
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">URL and sender controls</div>
            <div className="card-subtitle">
              Simulated containment actions for phishing & web-based incidents.
              All actions require parameters and are logged.
            </div>
          </div>
        </div>
        <div className="stack-vertical">
          <div className="field-group">
            <label htmlFor="action-url" className="field-label">
              URL
            </label>
            <input
              id="action-url"
              type="text"
              className="field-control"
              placeholder={alert?.url || "Enter URL to block/unblock"}
              value={actionParams.url}
              onChange={(e) =>
                setActionParams((prev) => ({ ...prev, url: e.target.value }))
              }
            />
          </div>
          <div className="stack-horizontal">
            <button
              type="button"
              className="btn btn-sm"
              onClick={() =>
                runAction(blockUrl, "Block URL", actionParams.url, "url")
              }
              disabled={!actionParams.url.trim()}
            >
              Block URL
            </button>
            <button
              type="button"
              className="btn btn-sm btn-ghost"
              onClick={() =>
                runAction(unblockUrl, "Unblock URL", actionParams.url, "url")
              }
              disabled={!actionParams.url.trim()}
            >
              Unblock URL
            </button>
          </div>

          <div className="field-group" style={{ marginTop: "1rem" }}>
            <label htmlFor="action-sender" className="field-label">
              Sender Email
            </label>
            <input
              id="action-sender"
              type="email"
              className="field-control"
              placeholder={alert?.sender || "Enter sender email to block/unblock"}
              value={actionParams.sender}
              onChange={(e) =>
                setActionParams((prev) => ({ ...prev, sender: e.target.value }))
              }
            />
          </div>
          <div className="stack-horizontal">
            <button
              type="button"
              className="btn btn-sm"
              onClick={() =>
                runAction(blockSender, "Block sender", actionParams.sender, "sender")
              }
              disabled={!actionParams.sender.trim()}
            >
              Block sender
            </button>
            <button
              type="button"
              className="btn btn-sm btn-ghost"
              onClick={() =>
                runAction(unblockSender, "Unblock sender", actionParams.sender, "sender")
              }
              disabled={!actionParams.sender.trim()}
            >
              Unblock sender
            </button>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">User & endpoint controls</div>
            <div className="card-subtitle">
              Simulated user session revocation and endpoint isolation.
              All actions require parameters and are logged.
            </div>
          </div>
        </div>
        <div className="stack-vertical">
          <div className="field-group">
            <label htmlFor="action-username" className="field-label">
              Username
            </label>
            <input
              id="action-username"
              type="text"
              className="field-control"
              placeholder={alert?.username || "Enter username to revoke session"}
              value={actionParams.username}
              onChange={(e) =>
                setActionParams((prev) => ({ ...prev, username: e.target.value }))
              }
            />
          </div>
          <div className="stack-horizontal">
            <button
              type="button"
              className="btn btn-sm"
              onClick={() =>
                runAction(
                  revokeUserSession,
                  "Revoke user session",
                  actionParams.username,
                  "username"
                )
              }
              disabled={!actionParams.username.trim()}
            >
              Revoke user session
            </button>
          </div>

          <div className="field-group" style={{ marginTop: "1rem" }}>
            <label htmlFor="action-hostname" className="field-label">
              Hostname
            </label>
            <input
              id="action-hostname"
              type="text"
              className="field-control"
              placeholder={alert?.hostname || "Enter hostname to isolate"}
              value={actionParams.hostname}
              onChange={(e) =>
                setActionParams((prev) => ({ ...prev, hostname: e.target.value }))
              }
            />
          </div>
          <div className="stack-horizontal">
            <button
              type="button"
              className="btn btn-sm btn-danger"
              onClick={() =>
                runAction(
                  isolateDevice,
                  "Isolate device",
                  actionParams.hostname,
                  "hostname"
                )
              }
              disabled={!actionParams.hostname.trim()}
            >
              Isolate device
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">Alert detail</div>
          <div className="page-subtitle">
            Full context, war room collaboration and containment actions for the selected alert.
          </div>
        </div>
        <div className="stack-horizontal">
          <button
            type="button"
            className="btn btn-danger btn-sm"
            onClick={handleDelete}
            disabled={!alert}
          >
            Delete Alert
          </button>
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={() => navigate(-1)}
          >
            Back
          </button>
        </div>
      </div>

      <div className="card">
        <div className="tabs">
          <button
            type="button"
            className={["tab", activeTab === "info" ? "tab-active" : ""].join(" ")}
            onClick={() => setActiveTab("info")}
          >
            Information
          </button>
          <button
            type="button"
            className={[
              "tab",
              activeTab === "warroom" ? "tab-active" : "",
            ].join(" ")}
            onClick={() => setActiveTab("warroom")}
          >
            War room
          </button>
          <button
            type="button"
            className={[
              "tab",
              activeTab === "utilities" ? "tab-active" : "",
            ].join(" ")}
            onClick={() => setActiveTab("utilities")}
          >
            Utilities
          </button>
        </div>

        {loading && <div className="muted">Loading alert…</div>}
        {error && (
          <div className="muted">
            Failed to load alert:
            {" "}
            {error}
          </div>
        )}
        {!loading && !error && !alert && (
          <div className="muted">Alert not found.</div>
        )}

        {!loading && !error && alert && (
          <>
            {activeTab === "info" && renderInfoTab()}
            {activeTab === "warroom" && renderWarRoomTab()}
            {activeTab === "utilities" && renderUtilitiesTab()}
          </>
        )}

        {actionMessage && (
          <div className="muted" style={{ marginTop: "0.75rem" }}>
            {actionMessage}
          </div>
        )}
      </div>
    </div>
  );
};

export default AlertDetailPage;
