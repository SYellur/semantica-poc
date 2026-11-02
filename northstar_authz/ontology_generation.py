"""Optional LLM-assisted ontology proposal generation using Semantica."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

BASE_URI = "https://example.org/northstar#"

DOMAIN_GUIDANCE = """
Propose an OWL ontology for the Northstar document authorization domain.
Use these core classes: Person, Team, Project, Document, ClearanceLevel.
Model qualified associations as explicit classes rather than flattening their
attributes: TeamMembership, ProjectAssignment, Clearance, DirectDocumentShare,
and DocumentRestriction.

Required association properties:
- TeamMembership: memberPerson -> Person; memberTeam -> Team.
- ProjectAssignment: assignedPerson -> Person; assignedProject -> Project.
- Clearance: clearedPerson -> Person; clearanceLevel -> ClearanceLevel.
- DirectDocumentShare: sharePerson -> Person; sharedDocument -> Document;
  validFrom and validUntil as xsd:dateTime datatype properties.
- DocumentRestriction: restrictedPerson -> Person; restrictedDocument -> Document;
  effectiveFrom as xsd:dateTime datatype property.

Also model Project -> owning Team, Document -> belonging Project, Team -> parent
Team, and Document classification. Use the supplied base namespace for class
and property IRIs. Do not invent business entities or authorization rules.
The result is a schema proposal only: do not generate source-to-ontology mapping
code or infer allow/deny policy rules.
"""


def build_generation_prompt(data: dict[str, Any]) -> str:
    """Combine fixed modelling constraints with the actual source structure."""
    structure = {
        collection: [
            {key: type(value).__name__ for key, value in row.items()}
            for row in records[:3]
        ]
        for collection, records in data.items()
        if isinstance(records, list) and records and isinstance(records[0], dict)
    }
    return (
        DOMAIN_GUIDANCE
        + "\nSource collection and field-type inventory (representative rows):\n"
        + json.dumps(structure, indent=2, ensure_ascii=False)
    )


def generate_ontology(
    source_path: str | Path,
    output_path: str | Path = "generated/northstar.proposed.ttl",
    provider: str = "openai",
    model: str | None = None,
) -> dict[str, Any]:
    """Generate a proposed ontology and export it as Turtle with Semantica."""
    from semantica.ontology import LLMOntologyGenerator, OWLGenerator

    with Path(source_path).open(encoding="utf-8") as handle:
        data = json.load(handle)

    generator = LLMOntologyGenerator(provider=provider, model=model)
    ontology = generator.generate_ontology_from_text(
        build_generation_prompt(data),
        base_uri=BASE_URI,
        name="Northstar Authorization Ontology",
        version="1.0",
    )
    OWLGenerator().export_owl(
        ontology, file_path=output_path, format="turtle"
    )
    return ontology


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a proposed Northstar ontology with Semantica"
    )
    parser.add_argument("--source", default="data/northstar.json")
    parser.add_argument("--output", default="generated/northstar.proposed.ttl")
    parser.add_argument("--provider", default="openai")
    parser.add_argument("--model")
    args = parser.parse_args()
    generate_ontology(args.source, args.output, args.provider, args.model)
    print(f"Ontology proposal written to {args.output}")
    print("Review the proposal; it does not replace ontology/northstar.ttl.")


if __name__ == "__main__":
    main()
