"""Small Northstar-specific source-to-KG mapping adapter."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def is_active(start: str | None, end: str | None, as_of: datetime) -> bool:
    """Check a half-open validity interval [start, end)."""
    point = as_of if as_of.tzinfo else as_of.replace(tzinfo=timezone.utc)
    point = point.astimezone(timezone.utc)
    start_dt, end_dt = parse_datetime(start), parse_datetime(end)
    return (start_dt is None or start_dt <= point) and (end_dt is None or point < end_dt)


def source_to_kg(data: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Convert normalized Northstar records to GraphBuilder input.

    Shares and restrictions become temporal edges. The TTL ontology uses
    reified association classes because the relationships carry attributes.
    This adapter projects those association dates onto the edge fields used by
    Semantica's TemporalGraphQuery.
    """
    entities: list[dict[str, Any]] = []
    relationships: list[dict[str, Any]] = []

    def add_entity(kind: str, identifier: str, **properties: Any) -> None:
        entities.append({"id": identifier, "type": kind, "properties": properties})

    def add_edge(source: str, target: str, kind: str, **properties: Any) -> None:
        relationships.append({
            "source": source, "target": target, "type": kind, **properties
        })

    for item in data["people"]:
        add_entity("Person", item["id"], name=item["name"])
    for item in data["teams"]:
        add_entity("Team", item["id"], name=item["name"])
    for level in sorted({row["level"] for row in data["clearances"]}):
        add_entity("ClearanceLevel", level, name=level)
    for item in data["projects"]:
        add_entity("Project", item["id"], name=item["name"])
        add_edge(item["owning_team"], item["id"], "OWNS_PROJECT")
    for item in data["documents"]:
        add_entity("Document", item["id"], classification=item["classification"])
        add_edge(item["project_id"], item["id"], "HAS_DOCUMENT")
    for item in data["team_memberships"]:
        add_edge(item["person_id"], item["team_id"], "MEMBER_OF")
    for item in data["team_hierarchy"]:
        add_edge(item["child_team_id"], item["parent_team_id"], "PARENT_TEAM")
    for item in data["project_assignments"]:
        add_edge(item["person_id"], item["project_id"], "ASSIGNED_TO")
    for item in data["clearances"]:
        add_edge(item["person_id"], item["level"], "HAS_CLEARANCE")
    for item in data["direct_shares"]:
        add_edge(
            item["person_id"], item["document_id"], "DIRECT_SHARE",
            valid_from=item.get("valid_from"), valid_until=item.get("valid_until"),
        )
    for item in data["restrictions"]:
        add_edge(
            item["person_id"], item["document_id"], "RESTRICTED_FROM",
            valid_from=item.get("effective_from"), valid_until=None,
        )

    return {"entities": entities, "relationships": relationships}
