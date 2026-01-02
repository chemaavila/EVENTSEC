import pytest
from sqlalchemy import exc as sqlalchemy_exc
from sqlalchemy.orm import configure_mappers


@pytest.fixture(autouse=True)
def setup_database() -> None:
    yield


def test_configure_mappers_no_ambiguous_fk() -> None:
    from backend.app import models  # noqa: F401

    configure_mappers()


def test_seed_detection_rules_skips_when_table_missing(monkeypatch) -> None:
    from backend.app import main

    def _raise_missing_table(_db):  # type: ignore[no-untyped-def]
        raise sqlalchemy_exc.ProgrammingError(
            "SELECT * FROM detection_rules", {}, Exception("missing table")
        )

    monkeypatch.setattr(main.crud, "list_detection_rules", _raise_missing_table)
    main._seed_detection_rules()
