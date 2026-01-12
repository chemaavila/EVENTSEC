# Email Protection Test Plan

## Unit tests

- Policy evaluation (allow/quarantine/reject)
- DLP matching (IBAN/DNI/NIE/CC)
- URL reputation and rewrite behavior

## Integration tests

- SMTP ingest → policy evaluation → quarantine creation
- Entra ID config persistence
- SIEM event emission on message ingest

## End-to-end tests

- Inbound clean message: delivered verdict
- EICAR attachment: quarantine or block
- Malicious URL: rewritten and flagged
- Outbound DLP: blocked/encrypted per policy

## Resilience tests

- Gateway unavailable: retry queue drains once restored
- Queue saturation: backpressure and alerting
- Analyzer unavailable: async retry with mTLS health checks
