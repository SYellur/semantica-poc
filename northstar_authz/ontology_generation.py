"""SAP AI Core ontology proposal generation through Semantica + LiteLLM.

LiteLLM reads AICORE_SERVICE_KEY and AICORE_RESOURCE_GROUP from the environment.
No OAuth or HTTP transport is implemented by this POC.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

BASE_URI = "https://example.org/northstar#"
DEFAULT_MODEL = "sap/gpt-4o"

DOMAIN_GUIDANCE = """
Propose an OWL ontology for the Northstar document authorization domain.
Use core classes: Person, Team, Project, Document, ClearanceLevel.
Model qualified associations as explicit classes: TeamMembership,
ProjectAssignment, Clearance, DirectDocumentShare, and DocumentRestriction.
Model the required association endpoints and represent validity properties
validFrom / validUntil / effectiveFrom as xsd:dateTime.
Also model project ownership, document membership, team parentage, and
document classification. Use the supplied base namespace. Do not invent
business entities or authorization rules. This is a schema proposal only:
do not produce source-to-ontology mapping code or access-control rules.
"""


def build_generation_prompt(data: dict[str, Any]) -> str:
    """Combine Northstar modelling constraints with source field inventory."""
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
        + "\nSource collection and field-type inventory:\n"
        + json.dumps(structure, indent=2, ensure_ascii=False)
    )


class SapLiteLLMProvider:
    """Adapt Semantica's LiteLLM wrapper to LLMOntologyGenerator's provider API."""

    def __init__(self, model: str = DEFAULT_MODEL, llm: Any = None):
        self.model = model
        if llm is None:
            from semantica.llms import LiteLLM
            llm = LiteLLM(model=model)
        self._llm = llm

    @staticmethod
    def _clean(kwargs: dict[str, Any]) -> dict[str, Any]:
        # The LiteLLM wrapper owns model; omit None to use LiteLLM defaults.
        return {
            key: value for key, value in kwargs.items()
            if key != "model" and value is not None
        }

    def generate_structured(self, prompt: str, **kwargs: Any) -> Any:
        return self._llm.generate_structured(prompt, **self._clean(kwargs))

    def is_available(self) -> bool:
        return self._llm.is_available()


def build_provider(model: str = DEFAULT_MODEL) -> SapLiteLLMProvider:
    """Construct the SAP adapter using Semantica's LiteLLM wrapper."""
    return SapLiteLLMProvider(model=model)


def generate_ontology(
    source_path: str | Path = "data/northstar.json",
    output_path: str | Path = "generated/northstar.proposed.ttl",
    model: str = DEFAULT_MODEL,
) -> dict[str, Any]:
    """Generate a proposal with Semantica; preserve the curated runtime ontology."""
    from semantica.ontology import LLMOntologyGenerator, OWLGenerator

    if not os.getenv("AICORE_SERVICE_KEY") or not os.getenv("AICORE_RESOURCE_GROUP"):
        raise EnvironmentError(
            "Set AICORE_SERVICE_KEY and AICORE_RESOURCE_GROUP before generation."
        )

    with Path(source_path).open(encoding="utf-8") as handle:
        data = json.load(handle)

    # Semantica owns ontology prompting, structured-output handling and export.
    # The custom adapter is only the provider boundary for the SAP LiteLLM model.
    generator = LLMOntologyGenerator(provider="openai", model=model)
    generator.provider = build_provider(model)

    ontology = generator.generate_ontology_from_text(
        build_generation_prompt(data),
        base_uri=BASE_URI,
        name="Northstar Authorization Ontology",
        version="1.0",
    )
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    OWLGenerator().export_owl(ontology, file_path=str(output), format="turtle")
    return ontology


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a Northstar ontology proposal with SAP AI Core via LiteLLM"
    )
    parser.add_argument("--source", default="data/northstar.json")
    parser.add_argument("--output", default="generated/northstar.proposed.ttl")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()
    generate_ontology(args.source, args.output, args.model)
    print(f"Proposal written to {args.output}")
    print("It does not replace ontology/northstar.ttl or update the mapper.")


if __name__ == "__main__":
    main()
