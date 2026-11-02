"""Validation gates for the Northstar source-to-KG adapter and ontology."""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from rdflib import Graph, Namespace, OWL, RDF, RDFS

from .adapter import source_to_kg

NS = Namespace("https://example.org/northstar#")
DEFAULT_ONTOLOGY = Path(__file__).resolve().parents[1] / "ontology" / "northstar.ttl"

# These are the KG projection predicates emitted by adapter.py, not every
# source-domain property in the richer reified ontology.
EXPECTED_EDGE_COUNTS = {
    "ownsProjectEdge": lambda d: len(d["projects"]),
    "hasDocument": lambda d: len(d["documents"]),
    "memberOf": lambda d: len(d["team_memberships"]),
    "hasParentTeam": lambda d: len(d["team_hierarchy"]),
    "assignedTo": lambda d: len(d["project_assignments"]),
    "hasClearance": lambda d: len(d["clearances"]),
    "directShareTo": lambda d: len(d["direct_shares"]),
    "restrictedFrom": lambda d: len(d["restrictions"]),
}


def validate_ontology_mapping(
    data: dict[str, Any], ontology_path: str | Path = DEFAULT_ONTOLOGY
) -> list[str]:
    """Return validation errors; an empty list means all configured checks pass.

    Checks ontology declarations, projection predicate domain/range, graph
    endpoints, and exact per-source-record relationship counts. The count
    contract is what catches records silently omitted by the adapter.
    """
    graph = Graph()
    graph.parse(str(ontology_path), format="turtle")
    graph_input = source_to_kg(data)
    errors: list[str] = []

    declared_classes = set(graph.subjects(RDF.type, OWL.Class))
    declared_object_properties = set(graph.subjects(RDF.type, OWL.ObjectProperty))
    entity_types = {entity["id"]: entity["type"] for entity in graph_input["entities"]}

    for entity_type in sorted({e["type"] for e in graph_input["entities"]}):
        if (NS[entity_type], RDF.type, OWL.Class) not in graph:
            errors.append(f"KG entity type {entity_type!r} is not declared as an owl:Class")

    entity_counts = Counter(entity["type"] for entity in graph_input["entities"])
    expected_entity_counts = {
        "Person": len(data["people"]),
        "Team": len(data["teams"]),
        "Project": len(data["projects"]),
        "Document": len(data["documents"]),
        "ClearanceLevel": len({row["level"] for row in data["clearances"]}),
    }
    for entity_type, expected in expected_entity_counts.items():
        actual = entity_counts[entity_type]
        if actual != expected:
            errors.append(
                f"Entity mapping coverage for {entity_type}: expected {expected} "
                f"entities from source records, got {actual}"
            )

    counts = Counter(edge["type"] for edge in graph_input["relationships"])
    for predicate, expected_fn in EXPECTED_EDGE_COUNTS.items():
        expected = expected_fn(data)
        actual = counts[predicate]
        if actual != expected:
            errors.append(
                f"Mapping coverage for {predicate}: expected {expected} edges "
                f"from source records, got {actual}"
            )

    for predicate, count in counts.items():
        uri = NS[predicate]
        if uri not in declared_object_properties:
            errors.append(f"Emitted relationship {predicate!r} is not a declared owl:ObjectProperty")
            continue
        domain = graph.value(uri, RDFS.domain)
        range_ = graph.value(uri, RDFS.range)
        for edge in (e for e in graph_input["relationships"] if e["type"] == predicate):
            source_type = entity_types.get(edge["source"])
            target_type = entity_types.get(edge["target"])
            if source_type is None:
                errors.append(f"{predicate} source {edge['source']!r} has no KG entity")
            elif domain is not None and domain != NS[source_type]:
                errors.append(
                    f"{predicate} domain mismatch: source {edge['source']!r} is {source_type}, "
                    f"ontology expects {domain}"
                )
            if target_type is None:
                errors.append(f"{predicate} target {edge['target']!r} has no KG entity")
            elif range_ is not None and range_ != NS[target_type]:
                errors.append(
                    f"{predicate} range mismatch: target {edge['target']!r} is {target_type}, "
                    f"ontology expects {range_}"
                )

    # Temporal projections must preserve source dates on every temporal edge.
    shares = [e for e in graph_input["relationships"] if e["type"] == "directShareTo"]
    for edge, source in zip(shares, data["direct_shares"]):
        if edge.get("valid_from") != source.get("valid_from"):
            errors.append(f"Direct share {source.get('person_id')}->{source.get('document_id')} lost valid_from")
        if edge.get("valid_until") != source.get("valid_until"):
            errors.append(f"Direct share {source.get('person_id')}->{source.get('document_id')} lost valid_until")

    restrictions = [e for e in graph_input["relationships"] if e["type"] == "restrictedFrom"]
    for edge, source in zip(restrictions, data["restrictions"]):
        if edge.get("valid_from") != source.get("effective_from"):
            errors.append(
                f"Restriction {source.get('person_id')}->{source.get('document_id')} "
                "did not project effective_from to valid_from"
            )
        if edge.get("valid_until") is not None:
            errors.append(
                f"Restriction {source.get('person_id')}->{source.get('document_id')} "
                "must remain open-ended"
            )

    return errors


def assert_ontology_mapping_valid(
    data: dict[str, Any], ontology_path: str | Path = DEFAULT_ONTOLOGY
) -> None:
    errors = validate_ontology_mapping(data, ontology_path)
    if errors:
        raise ValueError("Ontology/mapping validation failed:\n- " + "\n- ".join(errors))
