# Email Protection Operations Runbook

## Daily checks

- Gateway health: `/email-protection/health?tenant_id=...`
- Queue depth (SMTP backlog)
- Quarantine backlog and release SLA
- SIEM export status (last event timestamp)

## Incident response

1. Identify suspicious campaign (report or SIEM event).
2. Search quarantine and message logs.
3. Trigger retroactive purge (Graph API) if enabled.
4. Add block policy for sender/domain/URL.
5. Notify tenant admin and record audit.

## Maintenance

- Rotate tenant KMS keys annually or per policy.
- Validate MTA-STS/TLS-RPT reports.
- Review DLP false positives monthly.

## Security controls

- Ensure mTLS between gateway ↔ advanced analyzer.
- Ensure vault-backed secrets only (no hardcoded credentials).
- Validate CSP/CSRF for Admin Console.

## Backup & retention

- Postgres snapshots daily.
- Object storage lifecycle: default 30 days unless overridden.
- WORM storage optional for regulated tenants.

## Escalation contacts

- Tier 1 SOC: soc@eventsec.local
- Tier 2 Email Protection: email-sre@eventsec.local
- On-call: PagerDuty `EmailProtection`
