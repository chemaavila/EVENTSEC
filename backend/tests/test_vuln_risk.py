from backend.app.services.vuln_intel import risk


def test_risk_scoring_kev() -> None:
    label, score = risk.score_risk(cvss_score=5.0, epss_score=0.01, kev=True)
    assert label == "CRITICAL"
    assert score >= 0.2


def test_risk_scoring_high() -> None:
    label, _ = risk.score_risk(cvss_score=7.5, epss_score=0.1, kev=False)
    assert label == "HIGH"


def test_risk_scoring_medium() -> None:
    label, _ = risk.score_risk(cvss_score=4.5, epss_score=0.02, kev=False)
    assert label == "MEDIUM"
