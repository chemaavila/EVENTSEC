# Software Inventory + Vulnerability Intelligence

EventSec supports software inventory ingestion per asset and automatic vulnerability matching using NVD, OSV, EPSS, and KEV signals. Findings are scored, surfaced in the UI, and notified to tenant admins.

## Architecture

1. **Agent/Collector** posts software inventory per asset (`/api/inventory/assets/{asset_id}/software`).
2. **Backend** stores software components.
3. **Worker job** `match_and_score`:
   - Uses purl/cpe to query OSV/NVD.
   - Enriches with EPSS and KEV signals.
   - Persists findings and risk score/label.
4. **Notification job** `notify_admins`:
   - Immediate email for CRITICAL/KEV findings.
   - Optional daily digest for HIGH/MEDIUM.
   - Deduplicates via `last_notified_at` and `notified_risk_label`.
5. **Frontend** displays inventory risk and vulnerabilities dashboards.

## Environment variables

| Variable | Default | Description |
| --- | --- | --- |
| `VULN_INTEL_ENABLED` | `true` | Enable vuln intelligence pipeline. |
| `VULN_INTEL_WORKER_ROLE` | `api` | `api` or `worker` to control scheduler. |
| `NVD_API_KEY` | _(optional)_ | NVD API key header. |
| `NVD_BASE_URL` | `https://services.nvd.nist.gov/rest/json/cves/2.0` | NVD CVE API base. |
| `NVD_CPE_BASE_URL` | `https://services.nvd.nist.gov/rest/json/cpes/2.0` | NVD CPE API base. |
| `OSV_BASE_URL` | `https://api.osv.dev/v1/query` | OSV query API. |
| `OSV_BATCH_URL` | `https://api.osv.dev/v1/querybatch` | OSV batch API. |
| `EPSS_BASE_URL` | `https://api.first.org/data/v1/epss` | EPSS API. |
| `VULN_INTEL_HTTP_TIMEOUT_SECONDS` | `15` | HTTP timeout seconds. |
| `VULN_INTEL_HTTP_RETRIES` | `3` | HTTP retries with backoff. |
| `VULN_INTEL_CACHE_TTL_HOURS` | `24` | Cache TTL for OSV/NVD/EPSS. |
| `VULN_INTEL_NOTIFY_IMMEDIATE_MIN_RISK` | `CRITICAL` | Minimum label for immediate email. |
| `VULN_INTEL_NOTIFY_DIGEST_ENABLED` | `true` | Daily digest enabled. |
| `VULN_INTEL_NOTIFY_DIGEST_HOUR_LOCAL` | `9` | Digest hour (local). |
| `VULN_INTEL_TIMEZONE` | `Europe/Madrid` | Digest timezone. |
| `VULN_INTEL_CREATE_ALERTS_FOR_CRITICAL` | `true` | Create alerts for CRITICAL/KEV. |

## API endpoints

### POST `/api/inventory/assets/{asset_id}/software`

Bulk upsert software components.

**Payload**

```json
{
  "collected_at": "2025-03-12T08:15:00Z",
  "items": [
    {
      "name": "openssl",
      "version": "1.1.1w",
      "vendor": "OpenSSL",
      "purl": "pkg:generic/openssl@1.1.1w",
      "cpe": "cpe:2.3:a:openssl:openssl:1.1.1w:*:*:*:*:*:*:*",
      "raw": {"source": "agent"}
    }
  ]
}
```

**Response**

```json
{
  "inserted": 1,
  "updated": 0,
  "asset_risk": {
    "asset_id": 3,
    "critical_count": 1,
    "high_count": 0,
    "medium_count": 0,
    "low_count": 0,
    "top_risk_label": "CRITICAL",
    "last_scan_at": "2025-03-12T08:16:00Z"
  }
}
```

### GET `/api/inventory/assets`

Return assets + risk summaries for the current tenant.

### GET `/api/inventory/assets/{asset_id}`

Return asset detail + software list + risk summary.

### GET `/api/inventory/assets/{asset_id}/vulnerabilities`

List findings for an asset. Filters: `status`, `min_risk`, `kev`, `search`.

### GET `/api/vulnerabilities`

Global vulnerability view across assets. Filters: `min_risk`, `kev`, `epss_min`, `cve_id`, `software_name`.

### POST `/api/inventory/assets/{asset_id}/vulnerabilities/{finding_id}/status`

Update finding status (`open`, `mitigated`, `accepted`, `false_positive`).

## Worker

Run the worker service to periodically match and score:

```bash
python -m app.worker
```

## Risk labels

- **CRITICAL**: KEV or CVSS ≥ 9.0 and EPSS ≥ 0.30
- **HIGH**: CVSS ≥ 7.0 or EPSS ≥ 0.20
- **MEDIUM**: CVSS ≥ 4.0 or EPSS ≥ 0.05
- **LOW**: remaining findings
