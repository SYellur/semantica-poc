from datetime import datetime, timezone

from northstar_authz.policy import AuthorizationEngine
from northstar_authz.service import load_data


def instant(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def test_alice_inherits_team_ancestors():
    assert AuthorizationEngine(load_data()).inherited_teams("Alice") == {
        "API", "Platform", "Engineering"
    }


def test_alice_expected_documents_on_november_first():
    engine = AuthorizationEngine(load_data())
    as_of = instant("2026-11-01T12:00:00Z")
    allowed = {
        row["id"] for row in engine.data["documents"]
        if engine.check_access("Alice", row["id"], as_of).allowed
    }
    assert allowed == {"DOC-101", "DOC-103", "DOC-106", "DOC-107"}


def test_restriction_overrides_route_and_clearance():
    decision = AuthorizationEngine(load_data()).check_access(
        "Alice", "DOC-102", instant("2026-11-01T12:00:00Z")
    )
    assert decision.allowed is False
    assert "Active restriction" in decision.reasons[0]


def test_direct_share_expiry_boundary():
    engine = AuthorizationEngine(load_data())
    assert engine.check_access(
        "Ethan", "DOC-107", instant("2026-10-27T12:00:00Z")
    ).allowed
    assert not engine.check_access(
        "Ethan", "DOC-107", instant("2026-10-28T00:00:00Z")
    ).allowed


def test_confidential_direct_share_does_not_bypass_clearance():
    decision = AuthorizationEngine(load_data()).check_access(
        "Farah", "DOC-104", instant("2026-11-01T12:00:00Z")
    )
    assert decision.allowed is False
    assert "Insufficient clearance" in decision.reasons
