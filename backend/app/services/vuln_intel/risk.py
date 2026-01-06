from __future__ import annotations

from typing import Optional, Tuple


def normalize_cvss(score: Optional[float]) -> float:
    if score is None:
        return 0.0
    return max(min(score / 10.0, 1.0), 0.0)


def normalize_epss(score: Optional[float]) -> float:
    if score is None:
        return 0.0
    return max(min(score, 1.0), 0.0)


def compute_risk_label(
    *, cvss_score: Optional[float], epss_score: Optional[float], kev: bool
) -> str:
    if kev or ((cvss_score or 0) >= 9.0 and (epss_score or 0) >= 0.30):
        return "CRITICAL"
    if (cvss_score or 0) >= 7.0 or (epss_score or 0) >= 0.20:
        return "HIGH"
    if (cvss_score or 0) >= 4.0 or (epss_score or 0) >= 0.05:
        return "MEDIUM"
    return "LOW"


def compute_risk_score(
    *, cvss_score: Optional[float], epss_score: Optional[float], kev: bool
) -> float:
    cvss_norm = normalize_cvss(cvss_score)
    epss_norm = normalize_epss(epss_score)
    kev_boost = 0.2 if kev else 0.0
    score = (0.7 * cvss_norm) + (0.3 * epss_norm) + kev_boost
    return max(min(score, 1.0), 0.0)


def score_risk(
    *, cvss_score: Optional[float], epss_score: Optional[float], kev: bool
) -> Tuple[str, float]:
    return (
        compute_risk_label(
            cvss_score=cvss_score, epss_score=epss_score, kev=kev
        ),
        compute_risk_score(
            cvss_score=cvss_score, epss_score=epss_score, kev=kev
        ),
    )
