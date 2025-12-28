# Email Protection Integration

This section explains how the integrated Email Protection service works, how to configure it, and how it interacts with the EventSec platform.

## Purpose

- Provides OAuth connectors for Gmail and Microsoft 365 so EventSec can pull user inbox data, sync recent messages, and run inline phishing heuristics (URLs, attachment extensions, reply-to mismatches).
- Stores refresh tokens securely in a local SQLite store (`email_protection/tokens.db`) for reuse across sync runs.
- Exposes endpoints that can be triggered manually from the UI or via automation (e.g. scheduled sync, hunting playbooks).

## Components

1. **FastAPI app (`email_protection/app.py`)** – Implements Google/Microsoft OAuth flows, sync endpoints (`/sync/google`, `/sync/microsoft`), webhook callbacks, and helper storage functions for tokens and state. Analysis results describe score/findings per message.
2. **Database** – Lightweight SQLite store with tokens table and key-value store for history IDs. Initialized on startup via `init_db()`.
3. **Docker service** – Built from `email_protection/Dockerfile`, configured in `docker-compose.yml`, and exposed on port `8100`. Environment variables are prefixed `EMAIL_PROTECT_*` (client secrets, redirect URIs, base URLs).

## Workflow

1. A SOC operator hits `/auth/google/start` or `/auth/microsoft/start` (links available in the docs or UI) to begin OAuth; callbacks persist refresh tokens in SQLite.
2. Once tokens exist, `/sync/google` or `/sync/microsoft` can be invoked (via UI button or automation) to pull messages, analyze them via `analyze_message`, and return verdicts with findings/score.
3. The service can also register webhook subscriptions (`/subscribe/*`) and receive push notifications from Microsoft Graph or Gmail Pub/Sub, storing history IDs to avoid duplicates.

## Configuration

- Set OAuth credentials in `.env` or via Compose env vars:
  - `EMAIL_PROTECT_GOOGLE_CLIENT_ID`, `_SECRET`, `_REDIRECT_URI`
  - `EMAIL_PROTECT_MS_CLIENT_ID`, `_SECRET`, `_TENANT`, `_REDIRECT_URI`
  - Optional: `EMAIL_PROTECT_APP_BASE_URL`, `EMAIL_PROTECT_PUBLIC_BASE_URL`, `EMAIL_PROTECT_GMAIL_PUBSUB_TOPIC`
- Ensure the service has network access to Gmail/Microsoft APIs from the Docker network.

## Testing

1. Start the stack: `docker compose up -d --build`.
2. Trigger login flow: open <http://localhost:8100/auth/google/start> and complete consent; inspect `email_protection/tokens.db` to confirm tokens.
3. Sync via curl: `curl -X POST "http://localhost:8100/sync/google?mailbox=<user>&top=10"`.
4. Use `docs/test_commands.txt` section `Email protection` for scriptable commands.

## Use Cases

- Pull inbox messages for analysts to enrich alerts or handover notes.
- Auto-run phishing analysis when the sandbox flags a suspicious email attachment.
- Integrate with playbooks to re-trigger sync after blocking campaigns.


