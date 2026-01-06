from datetime import datetime, timezone

import pytest

from backend.app import models
from backend.app.jobs import vuln_matcher


@pytest.mark.asyncio
async def test_matcher_deduplicates_findings(db_session, monkeypatch) -> None:
    agent = models.Agent(
        name="asset-1",
        os="linux",
        ip_address="10.0.0.1",
        status="online",
        api_key="key-1",
    )
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    component = models.SoftwareComponent(
        tenant_id="default",
        asset_id=agent.id,
        name="openssl",
        version="1.1.1w",
        vendor="OpenSSL",
        purl="pkg:generic/openssl@1.1.1w",
        collected_at=datetime.now(timezone.utc),
        last_seen_at=datetime.now(timezone.utc),
    )
    db_session.add(component)
    db_session.commit()

    async def fake_osv(*_args, **_kwargs):
        return {
            "vulns": [
                {
                    "id": "OSV-2024-0001",
                    "summary": "Test vuln",
                    "details": "Details",
                    "aliases": ["CVE-2024-0001"],
                }
            ]
        }

    async def fake_nvd(*_args, **_kwargs):
        return {"vulnerabilities": []}

    async def fake_epss(*_args, **_kwargs):
        return 0.4

    monkeypatch.setattr(vuln_matcher, "_query_osv", fake_osv)
    monkeypatch.setattr(vuln_matcher, "_query_nvd", fake_nvd)
    monkeypatch.setattr(vuln_matcher, "_query_epss", fake_epss)

    await vuln_matcher.match_and_score(db_session, [component])
    await vuln_matcher.match_and_score(db_session, [component])

    findings = db_session.query(models.AssetVulnerability).all()
    assert len(findings) == 1
    assert findings[0].risk_label in {"CRITICAL", "HIGH"}
