from datetime import datetime, timezone

import pytest

pytest.importorskip("semantica")

from northstar_authz.semantica_pipeline import evaluate_with_semantica
from northstar_authz.service import load_data


def at(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def test_semantica_reasoning_path_allows_project_route():
    decision = evaluate_with_semantica(
        load_data(), "Alice", "DOC-101", at("2026-11-01T12:00:00Z")
    )
    assert decision.allowed is True
    assert decision.snapshot["num_relationships"] > 0


def test_semantica_reasoning_path_denies_active_restriction():
    decision = evaluate_with_semantica(
        load_data(), "Alice", "DOC-102", at("2026-11-01T12:00:00Z")
    )
    assert decision.allowed is False
    assert "restriction" in decision.explanation.lower()


def test_semantica_temporal_snapshot_expires_direct_share():
    before_expiry = evaluate_with_semantica(
        load_data(), "Ethan", "DOC-107", at("2026-10-27T12:00:00Z")
    )
    at_expiry = evaluate_with_semantica(
        load_data(), "Ethan", "DOC-107", at("2026-10-28T00:00:00Z")
    )
    assert before_expiry.allowed is True
    assert at_expiry.allowed is False
