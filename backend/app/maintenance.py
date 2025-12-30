from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import ProgrammingError

from . import models, search
from .database import SessionLocal


def prune(max_age_days: int) -> dict:
    """Delete events older than max_age_days and issue delete-by-query to OpenSearch."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    stats = {"events_deleted": 0, "opensearch_deleted": 0}

    with SessionLocal() as db:
        try:
            stats["events_deleted"] = (
                db.query(models.Event).filter(models.Event.created_at < cutoff).delete()
            )
            db.commit()
        except ProgrammingError as exc:
            db.rollback()
            stats["events_error"] = str(exc)
            stats["events_deleted"] = 0
            # Table probably does not exist yet (migrations pending); bail out early.
            return stats

    try:
        response = search.client.delete_by_query(
            index="events-v1",
            body={"query": {"range": {"timestamp": {"lt": cutoff.isoformat()}}}},
            conflicts="proceed",
        )
        stats["opensearch_deleted"] = response.get("deleted", 0)
    except Exception as exc:  # noqa: BLE001
        stats["opensearch_error"] = str(exc)

    return stats


async def loop_prune(max_age_days: int, loop_seconds: int) -> None:
    while True:
        stats = prune(max_age_days)
        print(f"[maintenance] Prune stats: {stats}")
        await asyncio.sleep(loop_seconds)


def main() -> None:
    parser = argparse.ArgumentParser(description="EventSec maintenance utilities")
    parser.add_argument(
        "--days", type=int, default=30, help="Delete data older than N days"
    )
    parser.add_argument(
        "--loop-seconds",
        type=int,
        default=0,
        help="Run forever sleeping this many seconds between runs (0 = run once)",
    )
    args = parser.parse_args()

    if args.loop_seconds > 0:
        asyncio.run(loop_prune(args.days, args.loop_seconds))
    else:
        stats = prune(args.days)
        print(f"[maintenance] Prune stats: {stats}")


if __name__ == "__main__":
    main()
