from __future__ import annotations

from . import fixtures
from .database import engine


def run_seed() -> None:
    with engine.begin() as connection:
        fixtures.seed_core_data(connection)


if __name__ == "__main__":
    run_seed()
