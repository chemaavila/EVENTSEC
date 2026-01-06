from __future__ import annotations

from datetime import datetime
from typing import Iterable, List

from ... import models
from ...config import settings


def _format_row(
    finding: models.AssetVulnerability,
    vuln: models.VulnerabilityRecord,
    component: models.SoftwareComponent,
) -> str:
    cve_or_osv = vuln.cve_id or vuln.osv_id or "N/A"
    cvss = f"{vuln.cvss_score:.1f}" if vuln.cvss_score is not None else "-"
    epss = f"{vuln.epss_score:.2f}" if vuln.epss_score is not None else "-"
    kev = "YES" if vuln.kev else "NO"
    first_seen = finding.first_seen_at.date().isoformat()
    return (
        f"{component.asset_id} | {component.name} | {component.version} | "
        f"{cve_or_osv} | {cvss} | {epss} | {kev} | {finding.risk_label} | {first_seen}"
    )


def _build_table(findings: Iterable[models.AssetVulnerability]) -> str:
    header = "Asset | Software | Version | CVE/OSV | CVSS | EPSS | KEV | Risk | First seen"
    rows = [header, "-" * len(header)]
    for finding in findings:
        vuln = finding.vulnerability  # type: ignore[assignment]
        component = finding.software_component  # type: ignore[assignment]
        if not vuln or not component:
            continue
        rows.append(_format_row(finding, vuln, component))
    return "\n".join(rows)


def build_immediate_email(
    tenant_id: str, findings: List[models.AssetVulnerability]
) -> dict:
    subject = f"[EVENTSEC] CRITICAL Vulnerabilities detected — {tenant_id}"
    body = "\n".join(
        [
            f"Tenant: {tenant_id}",
            "",
            _build_table(findings),
            "",
            f"UI: {settings.ui_base_url.rstrip('/')}/vulnerabilities",
        ]
    )
    return {"subject": subject, "body": body}


def build_digest_email(
    tenant_id: str, findings: List[models.AssetVulnerability]
) -> dict:
    subject = f"[EVENTSEC] Daily Vulnerability Digest — {tenant_id}"
    body = "\n".join(
        [
            f"Tenant: {tenant_id}",
            f"Generated at: {datetime.now().isoformat(timespec='seconds')}",
            "",
            _build_table(findings),
            "",
            f"UI: {settings.ui_base_url.rstrip('/')}/vulnerabilities",
        ]
    )
    return {"subject": subject, "body": body}
