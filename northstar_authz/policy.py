"""Transparent deterministic policy evaluator used by the quick-start CLI."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .adapter import is_active


@dataclass(frozen=True)
class Decision:
    person_id: str
    document_id: str
    allowed: bool
    reasons: tuple[str, ...] = field(default_factory=tuple)


class AuthorizationEngine:
    """Minimal reference implementation of the Northstar sample policy."""

    def __init__(self, data: dict[str, Any]):
        self.data = data

    def inherited_teams(self, person_id: str) -> set[str]:
        parent_map: dict[str, set[str]] = {}
        for row in self.data["team_hierarchy"]:
            parent_map.setdefault(row["child_team_id"], set()).add(row["parent_team_id"])

        reachable = {
            row["team_id"] for row in self.data["team_memberships"]
            if row["person_id"] == person_id
        }
        frontier = list(reachable)
        while frontier:
            current = frontier.pop()
            for parent in parent_map.get(current, set()):
                if parent not in reachable:
                    reachable.add(parent)
                    frontier.append(parent)
        return reachable

    def accessible_projects(self, person_id: str) -> set[str]:
        teams = self.inherited_teams(person_id)
        projects = {
            row["id"] for row in self.data["projects"]
            if row["owning_team"] in teams
        }
        projects.update(
            row["project_id"] for row in self.data["project_assignments"]
            if row["person_id"] == person_id
        )
        return projects

    def check_access(
        self, person_id: str, document_id: str, as_of: datetime
    ) -> Decision:
        documents = {row["id"]: row for row in self.data["documents"]}
        document = documents.get(document_id)
        if document is None:
            return Decision(person_id, document_id, False, ("Unknown document",))

        restrictions = [
            row for row in self.data["restrictions"]
            if row["person_id"] == person_id
            and row["document_id"] == document_id
            and is_active(row.get("effective_from"), None, as_of)
        ]
        if restrictions:
            return Decision(
                person_id, document_id, False,
                ("Active restriction overrides every allow route",),
            )

        project_route = document["project_id"] in self.accessible_projects(person_id)
        direct_share = any(
            row["person_id"] == person_id
            and row["document_id"] == document_id
            and is_active(row.get("valid_from"), row.get("valid_until"), as_of)
            for row in self.data["direct_shares"]
        )

        reasons: list[str] = []
        if project_route:
            reasons.append("Project route via inherited team or assignment")
        if direct_share:
            reasons.append("Active direct document share")

        clearance = any(
            row["person_id"] == person_id
            and row["level"] == document["classification"]
            for row in self.data["clearances"]
        )
        classification_ok = (
            document["classification"] == "Internal" or clearance
        )
        if not classification_ok:
            reasons.append("Insufficient clearance")
        if not project_route and not direct_share:
            reasons.append("No active project or direct-share route")

        allowed = (project_route or direct_share) and classification_ok
        if allowed:
            reasons.append("Policy conditions satisfied")
        return Decision(person_id, document_id, allowed, tuple(reasons))
