from __future__ import annotations

from fastapi import APIRouter

from ..config import settings

router = APIRouter(tags=["features"])


@router.get("/features")
def get_features() -> dict:
    return {
        "feature_intel_enabled": settings.feature_intel_enabled,
        "feature_ot_enabled": settings.feature_ot_enabled,
        "feature_email_actions_enabled": settings.feature_email_actions_enabled,
        "vuln_intel_enabled": settings.vuln_intel_enabled,
        "threatmap_fallback_coords": settings.threatmap_fallback_coords,
        "detection_queue_mode": settings.detection_queue_mode,
    }
