from __future__ import annotations

from backend.app import search


def test_network_mapping_contains_ips():
    props = search.NETWORK_EVENT_MAPPINGS["mappings"]["properties"]
    assert props["src_ip"]["type"] == "ip"
    assert props["dst_ip"]["type"] == "ip"
