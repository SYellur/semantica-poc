"""Semantica-backed Northstar decision path.

Uses Datalog for recursive reachability and Reasoner for allow inference.
The deny-overrides rule is made explicit by withholding NoActiveRestriction
facts for pairs that have an active restriction at the requested instant.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .adapter import is_active
from .service import build_graph, temporal_snapshot


@dataclass(frozen=True)
class SemanticaDecision:
    allowed: bool
    explanation: str
    snapshot: dict[str, Any]


def _datalog_term(value: str) -> str:
    term = re.sub(r"[^a-zA-Z0-9_]", "_", value).lower()
    if not term or term[0].isdigit():
        term = "v_" + term
    return term


def evaluate_with_semantica(
    data: dict[str, Any], person_id: str, document_id: str, as_of: datetime
) -> SemanticaDecision:
    """Run temporal KG query, Datalog reachability and policy inference."""
    from semantica.reasoning import DatalogReasoner, ExplanationGenerator, Reasoner

    graph = build_graph(data)
    snapshot = temporal_snapshot(graph, as_of)

    # Recursive graph reachability: direct membership plus parent-team closure.
    datalog = DatalogReasoner()
    for row in data["team_memberships"]:
        datalog.add_fact(
            f"membership({_datalog_term(row['person_id'])}, {_datalog_term(row['team_id'])})"
        )
    for row in data["team_hierarchy"]:
        datalog.add_fact(
            f"parent_team({_datalog_term(row['child_team_id'])}, {_datalog_term(row['parent_team_id'])})"
        )
    for row in data["projects"]:
        datalog.add_fact(
            f"owns_project({_datalog_term(row['owning_team'])}, {_datalog_term(row['id'])})"
        )
    for row in data["project_assignments"]:
        datalog.add_fact(
            f"assigned({_datalog_term(row['person_id'])}, {_datalog_term(row['project_id'])})"
        )

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

    # Temporal edges are also filtered by TemporalGraphQuery; these checks make
    # the exact sample policy explicit and prepare the Reasoner facts.
    active_shares = [
        row for row in data["direct_shares"]
        if is_active(row.get("valid_from"), row.get("valid_until"), as_of)
    ]
    active_restrictions = [
        row for row in data["restrictions"]
        if is_active(row.get("effective_from"), None, as_of)
    ]

    reasoner = Reasoner()
    person_terms = {person_id}
    for project in projects:
        reasoner.add_fact(f"ProjectAccess({person_id}, {project})")

    for doc in data["documents"]:
        reasoner.add_fact(f"DocumentInProject({doc['id']}, {doc['project_id']})")
        reasoner.add_fact(f"DocumentClassification({doc['id']}, {doc['classification']})")

    for row in data["clearances"]:
        reasoner.add_fact(f"HasClearance({row['person_id']}, {row['level']})")
    for row in active_shares:
        reasoner.add_fact(f"ActiveDirectShare({row['person_id']}, {row['document_id']})")

    restricted_pairs = {
        (row["person_id"], row["document_id"]) for row in active_restrictions
    }
    for doc in data["documents"]:
        pair = (person_id, doc["id"])
        if pair not in restricted_pairs:
            reasoner.add_fact(f"NoActiveRestriction({person_id}, {doc['id']})")

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
    target = f"Allow({person_id}, {document_id})"
    matched = next((item for item in results if item.conclusion == target), None)
    if matched is None:
        if (person_id, document_id) in restricted_pairs:
            explanation = "DENY: active restriction overrides all allow routes."
        else:
            explanation = "DENY: no qualifying route and clearance combination was inferred."
        return SemanticaDecision(False, explanation, snapshot)

    explanation_generator = ExplanationGenerator()
    detail = explanation_generator.generate_explanation(matched)
    explanation = getattr(detail, "natural_language", None) or str(detail)
    return SemanticaDecision(True, explanation, snapshot)
