from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy.orm import Session

from .. import crud, models
from ..config import settings
from ..services.vuln_intel.cache import get_cached_payload, set_cached_payload
from ..services.vuln_intel.http_client import VulnIntelHttpClient
from ..services.vuln_intel.risk import score_risk


def _hash_key(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _extract_cvss(cve: Dict[str, Any]) -> tuple[Optional[float], Optional[str]]:
    metrics = cve.get("metrics", {})
    candidates = []
    for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        for entry in metrics.get(key, []) or []:
            data = entry.get("cvssData", {})
            score = data.get("baseScore")
            vector = data.get("vectorString")
            if score is not None:
                candidates.append((float(score), vector))
    if not candidates:
        return None, None
    return max(candidates, key=lambda item: item[0])


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _parse_nvd(cve_item: Dict[str, Any]) -> Dict[str, Any]:
    cve = cve_item.get("cve", {})
    cve_id = cve.get("id")
    descriptions = cve.get("descriptions", [])
    summary = None
    for entry in descriptions:
        if entry.get("lang") == "en":
            summary = entry.get("value")
            break
    cvss_score, cvss_vector = _extract_cvss(cve)
    kev = bool(cve_item.get("cisaExploitAdd"))
    return {
        "cve_id": cve_id,
        "title": cve.get("sourceIdentifier"),
        "summary": summary,
        "cvss_score": cvss_score,
        "cvss_vector": cvss_vector,
        "kev": kev,
        "published_at": _parse_datetime(cve.get("published")),
        "modified_at": _parse_datetime(cve.get("lastModified")),
        "references": {"references": cve.get("references", [])},
    }


def _parse_osv(vuln: Dict[str, Any]) -> Dict[str, Any]:
    aliases = vuln.get("aliases", [])
    cve_id = next((alias for alias in aliases if str(alias).startswith("CVE-")), None)
    return {
        "osv_id": vuln.get("id"),
        "cve_id": cve_id,
        "title": vuln.get("summary"),
        "summary": vuln.get("details"),
        "references": {"references": vuln.get("references", [])},
        "published_at": _parse_datetime(vuln.get("published")),
        "modified_at": _parse_datetime(vuln.get("modified")),
    }


async def _query_osv(
    db: Session, http: VulnIntelHttpClient, *, purl: str, version: str
) -> Dict[str, Any]:
    key = _hash_key(f"osv:{purl}:{version}")
    cached = get_cached_payload(db, source="osv", key=key)
    if cached is not None:
        return cached
    payload = {"package": {"purl": purl}, "version": version}
    response = await http.post_json(settings.osv_base_url, payload)
    set_cached_payload(db, source="osv", key=key, payload=response)
    return response


async def _query_nvd(
    db: Session, http: VulnIntelHttpClient, *, cpe: str
) -> Dict[str, Any]:
    key = _hash_key(f"nvd:{cpe}")
    cached = get_cached_payload(db, source="nvd", key=key)
    if cached is not None:
        return cached
    response = await http.get_json(settings.nvd_base_url, params={"cpeName": cpe})
    set_cached_payload(db, source="nvd", key=key, payload=response)
    return response


async def _query_epss(
    db: Session, http: VulnIntelHttpClient, *, cve_id: str
) -> Optional[float]:
    key = _hash_key(f"epss:{cve_id}")
    cached = get_cached_payload(db, source="epss", key=key)
    if cached is not None:
        return cached.get("epss")
    response = await http.get_json(settings.epss_base_url, params={"cve": cve_id})
    data = (response.get("data") or [{}])[0]
    epss_value = data.get("epss")
    payload = {"epss": float(epss_value)} if epss_value is not None else {}
    set_cached_payload(db, source="epss", key=key, payload=payload)
    return payload.get("epss")


async def match_and_score(
    db: Session, components: Iterable[models.SoftwareComponent]
) -> List[models.AssetVulnerability]:
    http = VulnIntelHttpClient()
    findings: List[models.AssetVulnerability] = []
    now = datetime.now(timezone.utc)
    for component in components:
        matches: List[Dict[str, Any]] = []
        if component.purl and component.version:
            osv_payload = await _query_osv(
                db, http, purl=component.purl, version=component.version
            )
            for vuln in osv_payload.get("vulns", []) or []:
                matches.append({"source": "OSV", "data": _parse_osv(vuln)})
        if component.cpe:
            nvd_payload = await _query_nvd(db, http, cpe=component.cpe)
            for vuln in nvd_payload.get("vulnerabilities", []) or []:
                matches.append({"source": "NVD", "data": _parse_nvd(vuln)})

        for match in matches:
            data = match["data"]
            record = crud.get_vulnerability_record(
                db,
                source=match["source"],
                cve_id=data.get("cve_id"),
                osv_id=data.get("osv_id"),
            )
            if record:
                record.title = data.get("title") or record.title
                record.summary = data.get("summary") or record.summary
                record.cvss_score = data.get("cvss_score") or record.cvss_score
                record.cvss_vector = data.get("cvss_vector") or record.cvss_vector
                record.kev = bool(data.get("kev") or record.kev)
                record.published_at = data.get("published_at") or record.published_at
                record.modified_at = data.get("modified_at") or record.modified_at
                record.references = data.get("references") or record.references
            else:
                record = models.VulnerabilityRecord(
                    source=match["source"],
                    cve_id=data.get("cve_id"),
                    osv_id=data.get("osv_id"),
                    title=data.get("title"),
                    summary=data.get("summary"),
                    cvss_score=data.get("cvss_score"),
                    cvss_vector=data.get("cvss_vector"),
                    kev=bool(data.get("kev")),
                    published_at=data.get("published_at"),
                    modified_at=data.get("modified_at"),
                    references=data.get("references"),
                )
            record = crud.create_or_update_vulnerability_record(db, record)

            if record.cve_id:
                record.epss_score = await _query_epss(db, http, cve_id=record.cve_id)
                record = crud.create_or_update_vulnerability_record(db, record)

            risk_label, risk_score = score_risk(
                cvss_score=record.cvss_score,
                epss_score=record.epss_score,
                kev=record.kev,
            )
            confidence = 1.0 if component.purl or component.cpe else 0.6
            finding = crud.get_asset_vulnerability(
                db,
                tenant_id=component.tenant_id,
                asset_id=component.asset_id,
                software_component_id=component.id,
                vulnerability_id=record.id,
            )
            if finding:
                finding.last_seen_at = now
                finding.details = finding.details or {}
                if finding.risk_label != risk_label:
                    finding.risk_label = risk_label
                finding.risk_score = risk_score
                finding.confidence = confidence
            else:
                finding = models.AssetVulnerability(
                    tenant_id=component.tenant_id,
                    asset_id=component.asset_id,
                    software_component_id=component.id,
                    vulnerability_id=record.id,
                    status="open",
                    risk_label=risk_label,
                    risk_score=risk_score,
                    confidence=confidence,
                    first_seen_at=now,
                    last_seen_at=now,
                    details={"match": match["source"]},
                )
            finding = crud.create_or_update_asset_vulnerability(db, finding)
            finding.vulnerability = record
            finding.software_component = component
            findings.append(finding)
    return findings
