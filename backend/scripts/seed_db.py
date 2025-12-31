from __future__ import annotations

from backend.app import fixtures
from backend.app.database import engine


def main() -> None:
    with engine.begin() as connection:
        fixtures.seed_core_data(connection)


if __name__ == "__main__":
    main()
