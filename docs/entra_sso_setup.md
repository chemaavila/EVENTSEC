# Entra ID SSO + Provisioning Setup

## OIDC SSO

1. In Entra ID → App registrations → New registration.
2. Add redirect URI:
   - `https://<console-domain>/auth/callback`
3. Copy **Client ID** and **Tenant ID**.
4. Create a client secret.
5. In EventSec Admin Console → Identity → Entra ID:
   - Issuer: `https://login.microsoftonline.com/<tenant-id>/v2.0`
   - Client ID / Client secret
   - Scopes: `openid profile email offline_access`
6. Assign users/groups to the app.

## Role mapping

- `Global Admin` → full tenant + global configuration
- `Tenant Admin` → policies, connectors, quarantine
- `Analyst` → investigations, quarantine release
- `ReadOnly` → dashboards, reports

## Provisioning (Graph API)

1. Add Microsoft Graph API permissions:
   - `User.Read.All`, `Group.Read.All`, `Directory.Read.All`
2. Grant admin consent.
3. Configure EventSec sync job with client credentials.
4. Optional: enable SCIM endpoint (EventSec) for user provisioning.

## Verification checklist

- [ ] OIDC login succeeds and issues session
- [ ] Role mapping works
- [ ] Sync job imports users/groups
- [ ] Audit log records access
