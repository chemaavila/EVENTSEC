# Email Protection UI (EventSec Frontend)

This repo includes an **Email Security** UI that connects to the existing `email_protection` FastAPI service, using the **same frontend design system** (existing CSS tokens + components).

## Service URL

The frontend talks to:
- `http://localhost:8100` (default)

Override with:
- `VITE_EMAIL_PROTECT_BASE_URL=http://localhost:8100`

## Pages / Routes

- `/email-security` — Email Protection Dashboard (pixel-perfect UI)
- `/email-security/settings` — Email Configuration (pixel-perfect UI)

## OAuth (Google)

1. Open **Settings** (`/email-security/settings`)
2. Click **Connect / Link Google** (opens `GET /auth/google/start` in the same tab)
3. After OAuth completes, the backend redirects to `GET /auth/google/callback?...` and shows JSON in the browser.
4. Copy the `mailbox` value from that JSON and paste it into the **Mailbox** field in Settings.
5. Click **Save** (stores it in localStorage)

The mailbox is stored in:
- `localStorage["email_protect_mailbox"]`

## Sync behavior

- Dashboard auto-syncs on page load **only if** `email_protect_mailbox` exists.
- You can also click **Sync** (top-right) or **Refresh** in the “Recent activity” card.

Sync call:
- `POST {BASE}/sync/google?mailbox=<email>&top=10`

The “Recent activity” table is rendered from `results[]`:
- Remitente = `from`
- Destinatario = mailbox
- Asunto = `subject`
- Amenaza badge:
  - attachments > 0 → Malware
  - urls > 0 → Phishing
  - score > 0 or verdict != "low" → Suspicious
  - else → Low
- Acción:
  - score >= 70 → Blocked
  - score >= 40 → Quarantined
  - else → Filtered

## Local-only UI config fields

These are saved to `localStorage` for UI display only (backend uses docker env vars):
- `email_protect_client_id`
- `email_protect_client_secret`
- `email_protect_tenant_id`


