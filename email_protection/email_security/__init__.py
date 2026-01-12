"""Email Protection (gateway/policy/quarantine) modules."""

from email_security.routes import router as email_security_router
from email_security.storage import init_email_security_db

__all__ = ["email_security_router", "init_email_security_db"]
