# Email Protection Deployment (MX + M365/Exchange)

## MX cutover (inbound)

1. **Add domain** in Admin Console and get TXT verification token.
2. Add TXT record: `eventsec-verify=<token>`.
3. Verify domain in console.
4. Update MX records:
   - `mx1.<ourdomain>` priority 10
   - `mx2.<ourdomain>` priority 20
5. Validate DNS propagation.

## Microsoft 365 inbound connector

1. Exchange Admin Center → Mail Flow → Connectors → New.
2. **From**: Partner organization → **To**: Microsoft 365.
3. Restrict by IP: allow EventSec Gateway IPs.
4. Require TLS; optional certificate pinning.
5. Validate by sending test email.

## Microsoft 365 outbound connector (recommended)

1. Exchange Admin Center → Mail Flow → Connectors → New.
2. **From**: Microsoft 365 → **To**: Partner organization.
3. Smart host: `smtp.<ourdomain>`.
4. Require TLS; add connector certificate or domain validation.
5. Configure EventSec to DKIM-sign on behalf of tenant (if enabled).

## SPF/DKIM/DMARC alignment

- SPF: include EventSec gateway IPs or include mechanism.
- DKIM: either re-sign on EventSec (preferred for outbound) or delegate to M365.
- DMARC: align domain with DKIM/SPF; enforce `p=quarantine` or `p=reject` after validation.

## Verification checklist

- [ ] MX resolves to EventSec
- [ ] Inbound connector accepts TLS
- [ ] Outbound connector routes through EventSec
- [ ] SPF includes EventSec
- [ ] DKIM signatures validated
- [ ] DMARC reports received
