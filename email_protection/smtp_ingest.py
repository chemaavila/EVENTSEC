import os
from email.parser import BytesParser
from email.policy import default
from typing import Any, Dict

import requests
from aiosmtpd.controller import Controller

API_BASE = os.getenv("EMAIL_PROTECT_API_BASE", "http://localhost:8100")
TENANT_ID = os.getenv("EMAIL_PROTECT_TENANT_ID", "")


class IngestHandler:
    def handle_DATA(self, server, session, envelope):  # type: ignore[no-untyped-def]
        message = BytesParser(policy=default).parsebytes(envelope.content)
        sender = envelope.mail_from
        recipients = envelope.rcpt_tos
        subject = message.get("subject", "")
        body = _extract_body(message)
        payload: Dict[str, Any] = {
            "tenant_id": TENANT_ID,
            "direction": "inbound",
            "sender": sender,
            "recipients": recipients,
            "subject": subject,
            "body": body,
            "attachments": [],
            "urls": [],
        }
        if not TENANT_ID:
            return "550 Tenant ID not configured"
        requests.post(f"{API_BASE}/email-protection/ingest", json=payload, timeout=10)
        return "250 Message accepted for delivery"


def _extract_body(message):
    if message.is_multipart():
        for part in message.walk():
            if part.get_content_type() == "text/plain":
                return part.get_content()
        return ""
    return message.get_content()


def main():
    host = os.getenv("EMAIL_PROTECT_SMTP_HOST", "0.0.0.0")
    port = int(os.getenv("EMAIL_PROTECT_SMTP_PORT", "2525"))
    controller = Controller(IngestHandler(), hostname=host, port=port)
    controller.start()
    try:
        controller.loop.run_forever()
    finally:
        controller.stop()


if __name__ == "__main__":
    main()
