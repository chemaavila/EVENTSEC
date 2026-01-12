import re
from typing import Any, Dict, Iterable, List, Tuple

from email_security.models import IngestMessage, PolicyAction

EICAR_SIGNATURE = "EICAR-STANDARD-ANTIVIRUS-TEST-FILE"

IBAN_PATTERN = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b")
DNI_PATTERN = re.compile(r"\b\d{8}[A-Z]\b")
NIE_PATTERN = re.compile(r"\b[XYZ]\d{7}[A-Z]\b")
CC_PATTERN = re.compile(r"\b(?:\d[ -]*?){13,16}\b")

MALICIOUS_HINTS = ("phish", "malware", "evil", "ransom")


def scan_attachments(message: IngestMessage) -> List[str]:
    detections: List[str] = []
    for attachment in message.attachments:
        content = attachment.decoded_bytes()
        if content and EICAR_SIGNATURE.encode() in content:
            detections.append(f"eicar:{attachment.filename}")
    return detections


def detect_dlp(body: str) -> List[str]:
    hits: List[str] = []
    if IBAN_PATTERN.search(body):
        hits.append("iban")
    if DNI_PATTERN.search(body) or NIE_PATTERN.search(body):
        hits.append("dni")
    if CC_PATTERN.search(body):
        hits.append("credit_card")
    return hits


def analyze_urls(urls: Iterable[str]) -> List[str]:
    detections: List[str] = []
    for url in urls:
        lowered = url.lower()
        if any(hint in lowered for hint in MALICIOUS_HINTS):
            detections.append(url)
    return detections


def rewrite_urls(urls: Iterable[str], base: str) -> Dict[str, str]:
    rewritten: Dict[str, str] = {}
    for url in urls:
        rewritten[url] = f"{base}?u={url}"
    return rewritten


def evaluate_policies(
    message: IngestMessage,
    policies: Iterable[Dict[str, Any]],
    url_defense_base: str,
) -> Tuple[int, str, List[PolicyAction], Dict[str, Any]]:
    reasons: List[str] = []
    score = 0
    detections: Dict[str, Any] = {}
    body = message.body or ""

    attachment_hits = scan_attachments(message)
    if attachment_hits:
        detections["attachments"] = attachment_hits
        score += 60
        reasons.append("attachment_malicious")

    dlp_hits = detect_dlp(body)
    if dlp_hits:
        detections["dlp"] = dlp_hits
        score += 30
        reasons.append("dlp_match")

    url_hits = analyze_urls([u.url for u in message.urls])
    if url_hits:
        detections["urls"] = url_hits
        score += 40
        reasons.append("url_malicious")

    actions: List[PolicyAction] = []
    for policy in policies:
        if not policy.get("enabled", True):
            continue
        if policy.get("direction") and policy["direction"] != message.direction:
            continue
        conditions = policy.get("conditions", [])
        if not _policy_conditions_match(message, conditions, detections):
            continue
        for action in policy.get("actions", []):
            actions.append(PolicyAction(**action))

    if any(action.type == "quarantine" for action in actions):
        verdict = "quarantined"
    elif any(action.type == "reject" for action in actions):
        verdict = "blocked"
    elif score >= 70:
        verdict = "blocked"
        actions.append(PolicyAction(type="reject", value="score>=70"))
    elif score >= 40:
        verdict = "quarantined"
        actions.append(PolicyAction(type="quarantine", value="score>=40"))
    else:
        verdict = "allowed"

    if any(action.type == "rewrite_urls" for action in actions) and message.urls:
        detections["url_rewrites"] = rewrite_urls([u.url for u in message.urls], url_defense_base)

    if reasons:
        detections["reasons"] = reasons

    return score, verdict, actions, detections


def _policy_conditions_match(
    message: IngestMessage, conditions: Iterable[Dict[str, Any]], detections: Dict[str, Any]
) -> bool:
    for condition in conditions:
        cond_type = condition.get("type")
        value = condition.get("value")
        if cond_type == "sender_domain":
            domain = message.sender.split("@")[-1]
            if domain.lower() != str(value).lower():
                return False
        elif cond_type == "subject_contains":
            if not message.subject or str(value).lower() not in message.subject.lower():
                return False
        elif cond_type == "has_attachment":
            if not message.attachments:
                return False
        elif cond_type == "dlp_match":
            if "dlp" not in detections:
                return False
        elif cond_type == "url_malicious":
            if "urls" not in detections:
                return False
    return True
