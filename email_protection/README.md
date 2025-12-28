# Email Protection Connectors (Gmail + Microsoft 365)

This service provides OAuth connectors for Gmail and Microsoft 365, stores tokens in SQLite (`tokens.db`), syncs inbox messages, and runs a lightweight phishing analyzer before exposing the findings via JSON.

## Running locally

1. `cd email_protection`
2. `python -m venv .venv`
3. `source .venv/bin/activate`
4. `pip install -r requirements.txt`
5. Create a `.env` file from `.env.example` (not included) and define:
   - `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`
   - `MS_CLIENT_ID`, `MS_CLIENT_SECRET`, `MS_TENANT`, `MS_REDIRECT_URI`
   - `APP_BASE_URL` (e.g., `http://localhost:8100`)
   - Optional: `PUBLIC_BASE_URL`, `GMAIL_PUBSUB_TOPIC`, `TOKEN_DB_PATH`
6. Run `uvicorn app:app --reload --port 8100`.

## Docker deployment

- Build inside the EventSec stack (see `docker-compose.yml`) to expose on port `8100`.
- The service can be hit directly for sync/webhook flows and is also available to call from the EventSec frontend.

## Endpoints

- `/auth/google/start`, `/auth/microsoft/start`: launch OAuth flows.
- `/sync/google`, `/sync/microsoft`: pull the latest inbox messages.
- `/subscribe/...`, `/webhook/...`: manage Graph/Gmail subscriptions and webhooks.


