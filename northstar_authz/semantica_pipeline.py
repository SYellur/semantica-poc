"""Semantica-backed Northstar decision path.

Uses TemporalGraphQuery for time filtering, Datalog for recursive reachability,
and Reasoner for allow inference. Deny-overrides is represented explicitly by
withholding NoActiveRestriction facts for pairs with a live restriction.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .service import build_graph, temporal_snapshot


@dataclass(frozen=True)
class SemanticaDecision:
    allowed: bool
    explanation: str
    snapshot: dict[str, Any]


def _term(value: str) -> str:
    """Convert a source identifier into a safe predicate argument."""
    result = re.sub(r"[^a-zA-Z0-9_]", "_", value)
    if not result or result[0].isdigit():
        result = "v_" + result
    return result


def _datalog_term(value: str) -> str:
    return _term(value).lower()


def evaluate_with_semantica(
    data: dict[str, Any], person_id: str, document_id: str, as_of: datetime
) -> SemanticaDecision:
    """Run time filtering, recursive project reachability and policy inference."""
    from semantica.reasoning import DatalogReasoner, ExplanationGenerator, Reasoner

    graph = build_graph(data)
    snapshot = temporal_snapshot(graph, as_of)
    snapshot_edges = snapshot.get("relationships", [])

    # Load the static relations from the point-in-time KG into Datalog.
    datalog = DatalogReasoner()
    for edge in snapshot_edges:
        source = _datalog_term(edge.get("source", ""))
        target = _datalog_term(edge.get("target", ""))
        relation = edge.get("type")
        if relation == "MEMBER_OF":
            datalog.add_fact(f"membership({source}, {target})")
        elif relation == "PARENT_TEAM":
            datalog.add_fact(f"parent_team({source}, {target})")
        elif relation == "OWNS_PROJECT":
            datalog.add_fact(f"owns_project({source}, {target})")
        elif relation == "ASSIGNED_TO":
            datalog.add_fact(f"assigned({source}, {target})")

    datalog.add_rule("team_access(P, T) :- membership(P, T).")
    datalog.add_rule(
        "team_access(P, Parent) :- team_access(P, Child), parent_team(Child, Parent)."
    )
    datalog.add_rule(
        "project_access(P, Project) :- team_access(P, Team), owns_project(Team, Project)."
    )
    datalog.add_rule("project_access(P, Project) :- assigned(P, Project).")
    datalog.derive_all()

    project_rows = datalog.query(
        f"project_access({_datalog_term(person_id)}, ?Project)"
    )
    project_lookup = {
        _datalog_term(row["id"]): row["id"] for row in data["projects"]
    }
    projects = {
        project_lookup.get(row["Project"], row["Project"])
        for row in project_rows
    }

    # Use the TemporalGraphQuery snapshot as the source of truth for active
    # direct shares and restrictions. It filters valid_from/valid_until edges.
    active_share_pairs = {
        (edge.get("source"), edge.get("target"))
        for edge in snapshot_edges if edge.get("type") == "DIRECT_SHARE"
    }
    active_restriction_pairs = {
        (edge.get("source"), edge.get("target"))
        for edge in snapshot_edges if edge.get("type") == "RESTRICTED_FROM"
    }

    reasoner = Reasoner()
    for project in projects:
        reasoner.add_fact(
            f"ProjectAccess({_term(person_id)}, {_term(project)})"
        )
    for doc in data["documents"]:
        reasoner.add_fact(
            f"DocumentInProject({_term(doc['id'])}, {_term(doc['project_id'])})"
        )
        reasoner.add_fact(
            f"DocumentClassification({_term(doc['id'])}, {_term(doc['classification'])})"
        )
    for row in data["clearances"]:
        reasoner.add_fact(
            f"HasClearance({_term(row['person_id'])}, {_term(row['level'])})"
        )
    for share_person, share_document in active_share_pairs:
        reasoner.add_fact(
            f"ActiveDirectShare({_term(share_person)}, {_term(share_document)})"
        )

    # Add negative-condition facts only when there is no active restriction.
    for doc in data["documents"]:
        pair = (person_id, doc["id"])
        if pair not in active_restriction_pairs:
            reasoner.add_fact(
                f"NoActiveRestriction({_term(person_id)}, {_term(doc['id'])})"
            )

    reasoner.add_rule(
        "IF NoActiveRestriction(?p, ?d) AND ProjectAccess(?p, ?project) "
        "AND DocumentInProject(?d, ?project) AND DocumentClassification(?d, Internal) "
        "THEN Allow(?p, ?d)"
    )
    reasoner.add_rule(
        "IF NoActiveRestriction(?p, ?d) AND ProjectAccess(?p, ?project) "
        "AND DocumentInProject(?d, ?project) AND DocumentClassification(?d, Confidential) "
        "AND HasClearance(?p, Confidential) THEN Allow(?p, ?d)"
    )
    reasoner.add_rule(
        "IF NoActiveRestriction(?p, ?d) AND ActiveDirectShare(?p, ?d) "
        "AND DocumentClassification(?d, Internal) THEN Allow(?p, ?d)"
    )
    reasoner.add_rule(
        "IF NoActiveRestriction(?p, ?d) AND ActiveDirectShare(?p, ?d) "
        "AND DocumentClassification(?d, Confidential) "
        "AND HasClearance(?p, Confidential) THEN Allow(?p, ?d)"
    )

    results = reasoner.forward_chain()
    target = f"Allow({_term(person_id)}, {_term(document_id)})"
    matched = next(
        (item for item in results if item.conclusion == target), None
    )
    if matched is None:
        if (person_id, document_id) in active_restriction_pairs:
            explanation = "DENY: an active restriction overrides every allow route."
        else:
            explanation = "DENY: no qualifying route and clearance combination was inferred."
        return SemanticaDecision(False, explanation, snapshot)

    details = ExplanationGenerator().generate_explanation(matched)
    explanation = getattr(details, "natural_language", None) or str(details)
    return SemanticaDecision(True, explanation, snapshot)
