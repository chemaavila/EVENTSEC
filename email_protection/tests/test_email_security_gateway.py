import importlib
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def load_app(tmp_path):
    os.environ["TOKEN_DB_PATH"] = str(tmp_path / "email_security.db")
    if "app" in sys.modules:
        del sys.modules["app"]
    import app as app_module
    importlib.reload(app_module)
    app_module.init_db()
    app_module.init_email_security_db()
    return app_module


def test_ingest_quarantine(tmp_path):
    app_module = load_app(tmp_path)
    client = TestClient(app_module.app)

    tenant = client.post("/email-protection/tenants", json={"name": "Acme"}).json()
    policy = {
        "tenant_id": tenant["id"],
        "name": "Quarantine attachments",
        "direction": "inbound",
        "conditions": [{"type": "has_attachment"}],
        "actions": [{"type": "quarantine"}],
    }
    response = client.post("/email-protection/policies", json=policy)
    assert response.status_code == 200

    ingest_payload = {
        "tenant_id": tenant["id"],
        "direction": "inbound",
        "sender": "attacker@example.com",
        "recipients": ["user@acme.com"],
        "subject": "Invoice",
        "body": "Please see attachment",
        "attachments": [
            {
                "filename": "eicar.txt",
                "content_base64": "WDVPIVAlQEFQWzRcUFpYNTQoUF4pN0NDKTd9JEVJQ0FSLVNUTkRBUkQtQU5USVZJUlVTLVRFU1QtRklMRSFkSCtIKiA=",
            }
        ],
        "urls": [],
    }
    result = client.post("/email-protection/ingest", json=ingest_payload).json()
    assert result["verdict"] in {"quarantined", "blocked"}

    quarantine = client.get("/email-protection/quarantine", params={"tenant_id": tenant["id"]}).json()
    assert len(quarantine) == 1
