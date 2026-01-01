# Email Protection Connectors (Gmail + Microsoft 365)

This service provides OAuth connectors for Gmail and Microsoft 365, stores tokens in SQLite (`tokens.db`), syncs inbox messages, and runs a lightweight phishing analyzer before exposing the findings via JSON.

## Running locally

1. `cd email_protection`
2. `python -m venv .venv`
3. `source .venv/bin/activate`
4. `pip install -r requirements.txt`
5. Update `email_protection/.env.example` (used by Docker Compose) or copy it to `.env` and adjust `docker-compose.yml`:
   - Gmail: `EMAIL_PROTECT_GOOGLE_CLIENT_ID`, `EMAIL_PROTECT_GOOGLE_CLIENT_SECRET`,
     `EMAIL_PROTECT_GOOGLE_REDIRECT_URI`
   - Microsoft: `EMAIL_PROTECT_MS_CLIENT_ID`, `EMAIL_PROTECT_MS_CLIENT_SECRET`,
     `EMAIL_PROTECT_MS_TENANT`, `EMAIL_PROTECT_MS_REDIRECT_URI`
   - Base URLs: `EMAIL_PROTECT_APP_BASE_URL`, `EMAIL_PROTECT_PUBLIC_BASE_URL`
   - Optional: `EMAIL_PROTECT_GMAIL_PUBSUB_TOPIC`, `EMAIL_PROTECT_TOKEN_DB_PATH`
   - (Legacy keys without the `EMAIL_PROTECT_` prefix are still accepted.)
6. Run `uvicorn app:app --reload --port 8100`.

## Gmail configuration (summary)

1. Create a Google Cloud project and enable the **Gmail API**.
2. Configure the OAuth consent screen (External or Internal).
3. Create an **OAuth Client ID (Web application)** and set the authorized redirect URI:
   - `http://localhost:8100/auth/google/callback`
4. Copy the client ID/secret into `EMAIL_PROTECT_GOOGLE_CLIENT_ID` and
   `EMAIL_PROTECT_GOOGLE_CLIENT_SECRET` in `.env`.

Optional (push notifications):
- Create a Pub/Sub topic, grant Gmail API permissions to publish, and set
  `EMAIL_PROTECT_GMAIL_PUBSUB_TOPIC`.

## Microsoft 365 configuration (summary)

1. Register an app in **Azure Entra ID** (App registrations).
2. Add a **Web** platform with redirect URI:
   - `http://localhost:8100/auth/microsoft/callback`
3. Create a client secret and copy the **Application (client) ID** and secret to
   `EMAIL_PROTECT_MS_CLIENT_ID` and `EMAIL_PROTECT_MS_CLIENT_SECRET`.
4. Set `EMAIL_PROTECT_MS_TENANT` to your tenant ID or `common` for multi-tenant.
5. Ensure the app has delegated permissions:
   - `offline_access`, `User.Read`, `Mail.Read`

## Docker deployment

- Build inside the EventSec stack (see `docker-compose.yml`) to expose on port `8100`.
- The service can be hit directly for sync/webhook flows and is also available to call from the EventSec frontend.

## Endpoints

- `/auth/google/start`, `/auth/microsoft/start`: launch OAuth flows.
- `/sync/google`, `/sync/microsoft`: pull the latest inbox messages.
- `/subscribe/...`, `/webhook/...`: manage Graph/Gmail subscriptions and webhooks.
