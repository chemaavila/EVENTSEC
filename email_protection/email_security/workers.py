import json
import time
from typing import Any, Dict

from email_security.storage import fetch_pending_queue, update_queue_status


def process_queue_once() -> int:
    items = fetch_pending_queue(limit=10)
    for item in items:
        payload: Dict[str, Any] = json.loads(item["payload_json"])
        _ = payload
        update_queue_status(item["id"], "completed")
    return len(items)


def run_queue_worker(poll_seconds: int = 5) -> None:
    while True:
        processed = process_queue_once()
        if processed == 0:
            time.sleep(poll_seconds)
