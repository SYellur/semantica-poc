# Semantica Northstar Authorization POC

A runnable proof of concept for time-aware document authorization using Semantica and a Northstar sample domain.

The POC demonstrates:
- ontology modelling, including reified associations when a relationship has its own attributes;
- mapping structured source records into a knowledge graph;
- point-in-time graph queries for time-bounded direct shares and restrictions;
- recursive team ancestry and project reachability with Datalog;
- authorization policy evaluation and explanation hooks;
- small deterministic tests that do not call an LLM.

> **Important:** This is a learning/demo implementation, not a production authorization service. Do not use it as the only control protecting real documents.

## Quick start

Python 3.10+:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\\Scripts\\activate
pip install -e ".[dev]"
pytest -q
python -m northstar_authz --person Alice --as-of 2026-11-01T12:00:00Z
```

The default CLI runs a deterministic reference evaluator, so no LLM key or model service is needed.

To invoke the Semantica integration path from Python:

```python
from datetime import datetime, timezone
from northstar_authz.service import load_data
from northstar_authz.semantica_pipeline import evaluate_with_semantica

data = load_data()
result = evaluate_with_semantica(
    data,
    person_id="Alice",
    document_id="DOC-101",
    as_of=datetime(2026, 11, 1, 12, tzinfo=timezone.utc),
)
print(result.allowed, result.explanation)
```

The Semantica path uses public documented APIs: `GraphBuilder`, `TemporalGraphQuery`, `DatalogReasoner`, `Reasoner`, and `ExplanationGenerator`. It is kept separate from the deterministic fallback so individual layers can be understood and tested.

## Layout

```text
.
├── data/northstar.json
├── docs/
│   ├── architecture.md
│   ├── sequence.md
│   └── activity.md
├── ontology/northstar.ttl
├── northstar_authz/
│   ├── adapter.py
│   ├── policy.py
│   ├── service.py
│   └── semantica_pipeline.py
├── tests/
│   ├── test_adapter.py
│   ├── test_policy.py
│   ├── test_ontology.py
│   ├── test_ontology_generation.py
│   └── test_semantica_pipeline.py
├── .github/workflows/tests.yml
└── pyproject.toml
```

## Authorization semantics

A person can reach a document through:
1. team membership → parent team(s) → project owning team → documents in that project;
2. direct project assignment; or
3. an active direct document share.

Confidential documents require Confidential clearance. An active person/document restriction overrides all allow routes. The sample policy assumes direct shares do **not** bypass classification clearance.

All validity windows are half-open: `valid_from <= as_of < valid_until`. Missing `valid_until` means open-ended.

Expected sample outcomes on **2026-11-01**:
- Alice inherits API → Platform → Engineering and can reach Phoenix and Orion.
- Alice can access DOC-101, DOC-103, DOC-106, DOC-107.
- Alice is denied DOC-102 because her active restriction overrides her team route and clearance.
- Ethan's share to DOC-107 is active on 2026-10-27 and expired from 2026-10-28 onward.
- Farah's share to confidential DOC-104 does not grant access because she has no Confidential clearance.

## Why there is a small custom adapter

The ontology correctly represents a time-bounded share or restriction as a reified association individual, with dates stored as properties of that individual. Semantica's documented temporal KG query API works with `valid_from` / `valid_until` on graph relationships. `adapter.py` performs this Northstar-specific projection when constructing graph input. Ontology generation by itself does not define this source-to-KG transformation.

This is intentionally a narrow adapter, not a custom reasoning engine. Semantica remains responsible for graph construction, temporal querying, recursive inference, policy inference, and explanation in the integration path.

## Ontology generation

An optional proposal-generation script uses Semantica's native `LLMOntologyGenerator` and `OWLGenerator`. It writes a proposed Turtle file under `generated/` and does not overwrite the curated ontology. See [ontology generation](docs/ontology-generation.md). The native generator proposes classes and properties; Northstar source-to-KG mapping remains in the small adapter.

## Diagrams

The diagrams distinguish Semantica-provided capabilities from the Northstar-specific adapter and policy.

- [High-level architecture](docs/architecture.md) — design-time ontology generation and runtime component map.
- [Request sequence](docs/sequence.md) — which component is called, and in what order, for one access request.
- [Authorization activity](docs/activity.md) — the decision flow from temporal snapshot through recursive reachability and policy evaluation.

In the diagrams, **blue** denotes Semantica components, **amber** denotes Northstar-specific preparation, and **purple** denotes returned decisions.

## References

The implementation is based on the public Semantica documentation:
- [Ontology module](https://github.com/semantica-agi/semantica/blob/main/docs/reference/ontology.md)
- [Knowledge graph module](https://github.com/semantica-agi/semantica/blob/main/docs/reference/kg.md)
- [Reasoning module](https://github.com/semantica-agi/semantica/blob/main/docs/reference/reasoning.md)
- [Module overview](https://github.com/semantica-agi/semantica/blob/main/docs/modules.md)

The CI suite covers domain policy, adapter integrity, ontology parsing, the Semantica KG/temporal/reasoning path, and ontology-prompt constraints. The integration tests do not require an LLM provider. The optional ontology proposal command does require provider credentials.
