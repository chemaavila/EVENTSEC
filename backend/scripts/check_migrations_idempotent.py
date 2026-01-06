from __future__ import annotations

import os
import subprocess
import sys
import traceback


def main() -> int:
    if not (os.environ.get("DATABASE_URL") or os.environ.get("SQLALCHEMY_DATABASE_URL")):
        print("[migrations] DATABASE_URL or SQLALCHEMY_DATABASE_URL is required")
        return 1

    try:
        subprocess.run(
            ["alembic", "upgrade", "head"],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["alembic", "upgrade", "head"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        print("[migrations] alembic upgrade head failed")
        if exc.stdout:
            print(exc.stdout)
        if exc.stderr:
            print(exc.stderr, file=sys.stderr)
        traceback.print_exc()
        return 1

    print("[OK] alembic upgrade head is idempotent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
