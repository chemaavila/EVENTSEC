import { EMAIL_PROTECT_BASE_URL } from "../config/endpoints";
import { apiFetch } from "../services/http";

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
  return apiFetch({
    baseUrl: EMAIL_PROTECT_BASE_URL,
    path: "/sync/google",
    method: "POST",
    query: { mailbox, top },
  });
}

export async function syncMicrosoft(mailbox: string, top = 10): Promise<SyncResponse> {
  return apiFetch({
    baseUrl: EMAIL_PROTECT_BASE_URL,
    path: "/sync/microsoft",
    method: "POST",
    query: { mailbox, top },
  });
}
