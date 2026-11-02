from datetime import datetime, timezone

from northstar_authz.adapter import is_active, source_to_kg
from northstar_authz.service import load_data


def test_interval_is_half_open():
    start = "2026-10-20T00:00:00Z"
    end = "2026-10-28T00:00:00Z"
    assert is_active(start, end, datetime(2026, 10, 27, 12, tzinfo=timezone.utc))
    assert not is_active(start, end, datetime(2026, 10, 28, 0, tzinfo=timezone.utc))


def test_adapter_projects_share_dates_onto_kg_edge_fields():
    graph_input = source_to_kg(load_data())
    share = next(
        edge for edge in graph_input["relationships"]
        if edge["source"] == "Ethan" and edge["target"] == "DOC-107"
        and edge["type"] == "DIRECT_SHARE"
    )
    assert share["valid_from"] == "2026-10-20T00:00:00Z"
    assert share["valid_until"] == "2026-10-28T00:00:00Z"


def test_adapter_projects_open_ended_restriction():
    graph_input = source_to_kg(load_data())
    restriction = next(
        edge for edge in graph_input["relationships"]
        if edge["source"] == "Alice" and edge["target"] == "DOC-102"
        and edge["type"] == "RESTRICTED_FROM"
    )
    assert restriction["valid_from"] == "2026-10-25T00:00:00Z"
    assert restriction["valid_until"] is None


def test_all_mapped_relationship_endpoints_exist_as_entities():
    graph_input = source_to_kg(load_data())
    entity_ids = {entity["id"] for entity in graph_input["entities"]}
    for edge in graph_input["relationships"]:
        assert edge["source"] in entity_ids
        assert edge["target"] in entity_ids
