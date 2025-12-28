import type { ThreatWsMessage } from "./ws_types";

export type WsStatus = "OFFLINE" | "CONNECTING" | "LIVE" | "STALE";

export type ThreatWsClient = {
  close: () => void;
  send: (obj: unknown) => void;
};

export function connectThreatWs(args: {
  url: string;
  onMessage: (msg: ThreatWsMessage) => void;
  onStatus?: (s: WsStatus) => void;
}) : ThreatWsClient {
  const { url, onMessage, onStatus } = args;
  let ws: WebSocket | null = null;
  let stopped = false;
  let retries = 0;

  const connect = () => {
    if (stopped) return;
    onStatus?.("CONNECTING");
    ws = new WebSocket(url);

    ws.onopen = () => {
      retries = 0;
      onStatus?.("LIVE");
    };

    ws.onclose = () => {
      if (stopped) return;
      onStatus?.("OFFLINE");
      const backoff = Math.min(12_000, 500 + retries * 800);
      retries += 1;
      setTimeout(connect, backoff);
    };

    ws.onerror = () => {
      // allow close handler to drive reconnect
    };

    ws.onmessage = (ev) => {
      try {
        const obj = JSON.parse(ev.data) as ThreatWsMessage;
        onMessage(obj);
      } catch {
        // ignore malformed messages
      }
    };
  };

  connect();

  return {
    close: () => {
      stopped = true;
      try { ws?.close(); } catch {}
    },
    send: (obj: unknown) => {
      try {
        if (ws?.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify(obj));
        }
      } catch {}
    }
  };
}


