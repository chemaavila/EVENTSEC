const DEFAULT_BASE = "http://localhost:8100";

export const EMAIL_PROTECT_BASE_URL =
  (import.meta as any).env?.VITE_EMAIL_PROTECT_BASE_URL || DEFAULT_BASE;

export type SyncResult = {
  provider: string;
  mailbox: string;
  message_id: string;
  subject: string;
  from: string;
  reply_to?: string | null;
  urls: string[];
  attachments: string[];
  score: number;
  verdict: string;
  findings: string[];
};

export type SyncResponse = {
  count: number;
  results: SyncResult[];
};

export function startGoogleOAuthUrl(): string {
  return `${EMAIL_PROTECT_BASE_URL}/auth/google/start`;
}

export function startMicrosoftOAuthUrl(): string {
  return `${EMAIL_PROTECT_BASE_URL}/auth/microsoft/start`;
}

export async function syncGoogle(mailbox: string, top = 10): Promise<SyncResponse> {
  const url = new URL(`${EMAIL_PROTECT_BASE_URL}/sync/google`);
  url.searchParams.set("mailbox", mailbox);
  url.searchParams.set("top", String(top));

  const res = await fetch(url.toString(), { method: "POST" });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Sync failed (${res.status}): ${text || res.statusText}`);
  }
  return (await res.json()) as SyncResponse;
}

export async function syncMicrosoft(mailbox: string, top = 10): Promise<SyncResponse> {
  const url = new URL(`${EMAIL_PROTECT_BASE_URL}/sync/microsoft`);
  url.searchParams.set("mailbox", mailbox);
  url.searchParams.set("top", String(top));

  const res = await fetch(url.toString(), { method: "POST" });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Sync failed (${res.status}): ${text || res.statusText}`);
  }
  return (await res.json()) as SyncResponse;
}

