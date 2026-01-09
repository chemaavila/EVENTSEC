from __future__ import annotations

from backend.app import search


class FakeIndices:
    def __init__(self) -> None:
        self.created: dict[str, dict] = {}
        self.aliases: dict[str, str] = {}

    def exists(self, index: str) -> bool:  # noqa: A003
        return index in self.created

    def create(self, index: str, body: dict) -> None:
        self.created[index] = body

    def exists_alias(self, name: str) -> bool:
        return name in self.aliases

    def get_alias(self, name: str) -> dict:
        return {index: {"aliases": {name: {}}} for name, index in self.aliases.items()}

    def update_aliases(self, body: dict) -> None:
        for action in body.get("actions", []):
            if "remove" in action:
                alias = action["remove"]["alias"]
                self.aliases.pop(alias, None)
            if "add" in action:
                alias = action["add"]["alias"]
                self.aliases[alias] = action["add"]["index"]

    def put_alias(self, index: str, name: str) -> None:
        self.aliases[name] = index


class FakeClient:
    def __init__(self) -> None:
        self.indices = FakeIndices()


def test_ensure_indices_creates_aliases(monkeypatch):
    fake_client = FakeClient()
    monkeypatch.setattr(search, "client", fake_client)
    search._ensured_indices.clear()
    search._ensured_aliases.clear()

    search.ensure_indices()

    assert search.EVENTS_V2_INDEX in fake_client.indices.created
    assert search.ALERTS_V2_INDEX in fake_client.indices.created
    assert fake_client.indices.aliases[search.EVENTS_INDEX_ALIAS] == search.EVENTS_V2_INDEX
    assert fake_client.indices.aliases[search.ALERTS_INDEX_ALIAS] == search.ALERTS_V2_INDEX

    mappings = fake_client.indices.created[search.EVENTS_V2_INDEX]
    assert mappings["mappings"]["properties"]["details"]["enabled"] is False
