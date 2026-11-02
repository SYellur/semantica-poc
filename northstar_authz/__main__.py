from __future__ import annotations

import argparse
from datetime import datetime, timezone

from .policy import AuthorizationEngine
from .service import load_data


def main() -> None:
    parser = argparse.ArgumentParser(description="Northstar document authorization POC")
    parser.add_argument("--person", default="Alice")
    parser.add_argument("--document")
    parser.add_argument("--as-of", default="2026-11-01T12:00:00Z")
    args = parser.parse_args()

    as_of = datetime.fromisoformat(args.as_of.replace("Z", "+00:00"))
    if as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=timezone.utc)

    data = load_data()
    engine = AuthorizationEngine(data)
    documents = [args.document] if args.document else [row["id"] for row in data["documents"]]
    for document_id in documents:
        decision = engine.check_access(args.person, document_id, as_of)
        print(f"{decision.person_id} -> {decision.document_id}: "
              f"{'ALLOW' if decision.allowed else 'DENY'}")
        for reason in decision.reasons:
            print(f"  - {reason}")


if __name__ == "__main__":
    main()
