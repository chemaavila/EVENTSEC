# EventSec Documentation - Email Protection Integration

This section explains how the integrated Email Protection service works, how to configure it, and how it interacts with the EventSec platform.

## Purpose

- Provides OAuth connectors for Gmail and Microsoft 365 so EventSec can pull user inbox data, sync recent messages, and run inline phishing heuristics (URLs, attachment extensions, reply-to mismatches).
- Stores refresh tokens securely in a local SQLite store (`email_protection/tokens.db`) for reuse across sync runs.
- Exposes endpoints that can be triggered manually from the UI or via automation (e.g. scheduled sync, hunting playbooks).

## Components

1. **FastAPI app (`email_protection/app.py`)** – Implements Google/Microsoft OAuth flows, sync endpoints (`/sync/google`, `/sync/microsoft`), webhook callbacks, and helper storage functions for tokens and state. Analysis results describe score/findings per message.
2. **Database** – Lightweight SQLite store with tokens table and key-value store for history IDs. Initialized on startup via `init_db()`.
3. **Docker service** – Built from `email_protection/Dockerfile`, configured in `docker-compose.yml`, and exposed on port `8100`. Environment variables are prefixed `EMAIL_PROTECT_*` (client secrets, redirect URIs, base URLs). Legacy keys without the prefix are accepted.

## Workflow

1. A SOC operator hits `/auth/google/start` or `/auth/microsoft/start` (links available in the docs or UI) to begin OAuth; callbacks persist refresh tokens in SQLite.
2. Once tokens exist, `/sync/google` or `/sync/microsoft` can be invoked (via UI button or automation) to pull messages, analyze them via `analyze_message`, and return verdicts with findings/score.
3. The service can also register webhook subscriptions (`/subscribe/*`) and receive push notifications from Microsoft Graph or Gmail Pub/Sub, storing history IDs to avoid duplicates.

UI note: use `/email-security/settings` to save the mailbox address (localStorage) so the dashboard can trigger syncs.

## Configuration

### Required environment variables

Edit `email_protection/.env.example` (used by Docker Compose) or set env vars directly:

- Gmail:
  - `EMAIL_PROTECT_GOOGLE_CLIENT_ID`
  - `EMAIL_PROTECT_GOOGLE_CLIENT_SECRET`
  - `EMAIL_PROTECT_GOOGLE_REDIRECT_URI` (default: `http://localhost:8100/auth/google/callback`)
- Microsoft:
  - `EMAIL_PROTECT_MS_CLIENT_ID`
  - `EMAIL_PROTECT_MS_CLIENT_SECRET`
  - `EMAIL_PROTECT_MS_TENANT` (tenant ID or `common`)
  - `EMAIL_PROTECT_MS_REDIRECT_URI` (default: `http://localhost:8100/auth/microsoft/callback`)
- Base URLs:
  - `EMAIL_PROTECT_APP_BASE_URL` (default `http://localhost:8100`)
  - `EMAIL_PROTECT_PUBLIC_BASE_URL` (public URL reachable by webhooks)
- Optional:
  - `EMAIL_PROTECT_GMAIL_PUBSUB_TOPIC` (Gmail push notifications)
  - `EMAIL_PROTECT_TOKEN_DB_PATH` (default `tokens.db`)

> Legacy keys without the `EMAIL_PROTECT_` prefix are still accepted if you have existing deployments.

Ensure the service has outbound access to Gmail/Microsoft APIs from the Docker network.

### Gmail setup (summary)

1. Create a Google Cloud project and enable the **Gmail API**.
2. Configure the OAuth consent screen (External/Internal).
3. Create OAuth credentials (Web application) with redirect URI:
   - `http://localhost:8100/auth/google/callback`
4. Copy the Client ID/secret into `EMAIL_PROTECT_GOOGLE_CLIENT_ID` and
   `EMAIL_PROTECT_GOOGLE_CLIENT_SECRET`.

Optional push notifications:
- Create a Pub/Sub topic and set `EMAIL_PROTECT_GMAIL_PUBSUB_TOPIC`.
- Grant Gmail API permission to publish (see Google "Gmail push notifications" docs).

### Microsoft 365 setup (summary)

1. Register an app in **Azure Entra ID** (App registrations).
2. Add a **Web** platform with redirect URI:
   - `http://localhost:8100/auth/microsoft/callback`
3. Create a client secret and copy the **Application (client) ID** and secret to
   `EMAIL_PROTECT_MS_CLIENT_ID` and `EMAIL_PROTECT_MS_CLIENT_SECRET`.
4. Set `EMAIL_PROTECT_MS_TENANT` to your tenant ID or `common` (multi-tenant).
5. Ensure delegated permissions include:
   - `offline_access`, `User.Read`, `Mail.Read`

## Testing

1. Start the stack: `docker compose up -d --build`.
2. Trigger login flow:
   - Gmail: <http://localhost:8100/auth/google/start>
   - Microsoft: <http://localhost:8100/auth/microsoft/start>
3. Confirm `email_protection/tokens.db` contains tokens for the mailbox.
4. Sync via curl:
   - Gmail: `curl -X POST "http://localhost:8100/sync/google?mailbox=<user>&top=10"`
   - Microsoft: `curl -X POST "http://localhost:8100/sync/microsoft?mailbox=<user>&top=10"`
5. Use `docs/test_commands.txt` section `Email protection` for scriptable commands.

## Use Cases

- Pull inbox messages for analysts to enrich alerts or handover notes.
- Auto-run phishing analysis when the sandbox flags a suspicious email attachment.
- Integrate with playbooks to re-trigger sync after blocking campaigns.
