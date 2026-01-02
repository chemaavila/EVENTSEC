import { API_BASE_URL, EMAIL_PROTECT_BASE_URL, resolveWsUrl } from "../../config/endpoints";

const debugEnabled = (import.meta.env.VITE_UI_DEBUG ?? "false") === "true";

export const DebugPanel = () => {
  if (!debugEnabled) return null;

  return (
    <div className="debug-panel">
      <div className="debug-panel-title">UI Debug</div>
      <div className="debug-panel-row">
        <span>API Base</span>
        <code>{API_BASE_URL}</code>
      </div>
      <div className="debug-panel-row">
        <span>ThreatMap WS</span>
        <code>{resolveWsUrl("/ws/threatmap")}</code>
      </div>
      <div className="debug-panel-row">
        <span>Email Protect</span>
        <code>{EMAIL_PROTECT_BASE_URL}</code>
      </div>
    </div>
  );
};
