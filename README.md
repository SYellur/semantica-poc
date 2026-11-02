# Semantica Northstar Authorization POC

A learning proof of concept for time-aware document authorization using Semantica and a Northstar sample domain.

The POC demonstrates ontology modelling, explicit source-to-KG mapping, temporal graph snapshots, recursive team/project reachability, authorization inference, and validation against a curated Turtle ontology.

> **Scope:** this is a learning/demo implementation, not a production authorization service. Do not use it as the only control protecting real documents.

## Quick start

Python 3.10+:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\\Scripts\\activate
pip install -e ".[dev]"
pytest -q
python -m northstar_authz --person Alice --as-of 2026-11-01T12:00:00Z
```

The default CLI runs the deterministic reference evaluator and needs no LLM credentials.

## Two guided notebooks

Install Jupyter and launch from the repository root:

```bash
pip install jupyter
jupyter notebook
```

1. [01 — SAP AI Core ontology generation](notebooks/01_sap_ai_core_ontology_generation.ipynb): call SAP AI Core through LiteLLM and Semantica's `LLMOntologyGenerator` / `OWLGenerator` to generate a schema **proposal**.
2. [02 — Curated ontology, mapping, temporal KG and reasoning](notebooks/02_curated_ontology_kg_and_reasoning.ipynb): use the reviewed Turtle ontology, explicitly map source records, build a KG with Semantica, query a temporal snapshot, and run Semantica reasoning.

The notebooks are separate by design. A generated ontology does not update the source-to-KG mapper automatically.

## SAP AI Core configuration

Set these environment variables before running notebook 01. Keep credentials out of notebooks, source control, and logs.

```bash
export AICORE_SERVICE_KEY='{"clientid":"...","clientsecret":"...","url":"https://<tenant>.authentication.sap.hana.ondemand.com","serviceurls":{"AI_API_URL":"https://api.ai.<region>.aws.ml.hana.ondemand.com"}}'
export AICORE_RESOURCE_GROUP="default"
```

The model defaults to `sap/gpt-4o`. Confirm that the corresponding model/deployment is available in your SAP AI Core account. LiteLLM handles provider authentication; this POC does not implement OAuth or raw HTTP transport.

## Architecture

- **Semantica:** `LLMOntologyGenerator` and `OWLGenerator` for design-time schema proposals; `GraphBuilder`, `TemporalGraphQuery`, `DatalogReasoner`, `Reasoner`, and `ExplanationGenerator` in the runtime reasoning path.
- **Northstar adapter:** the small domain-specific component that maps source JSON into graph entities/edges and performs the temporal projection required by the current temporal query path.
- **Curated ontology:** `ontology/northstar.ttl` is the reviewed runtime schema. Generated Turtle under `generated/` is proposal-only.

## Why the mapper must change with the ontology

The ontology describes domain concepts and relationships. It does not specify how every JSON record is transformed into a KG entity or relationship. When classes, properties, domains/ranges, or temporal modelling change, the adapter and its validation contract may need corresponding changes.

A stale mapper can omit source records or emit incorrectly typed graph relationships. The migration gate therefore checks ontology declarations, property domains/ranges, endpoint existence, expected source-to-entity/edge counts, and temporal date projection. These checks catch configured mapping failures; they do not prove domain semantics or authorization policy correctness.

Run the checks with:

```bash
python -c "from northstar_authz.service import load_data; from northstar_authz.ontology_validation import assert_ontology_mapping_valid; assert_ontology_mapping_valid(load_data())"
pytest -q
```

For candidate ontology changes, run `northstar_authz.ontology_diff.diff_ontologies(old, new)`, review mapper impact, update mapper and validator together, add regression tests, and require human approval before adopting the Turtle. See [validation](docs/ontology-validation.md), [ADR-002](docs/decisions/0002-sap-ai-core-and-temporal-ontology-contract.md), [ADR-003: structured-source ontology discovery](docs/decisions/0003-structured-source-ontology-discovery.md), and the [ontology-migration Claude skill](.claude/skills/ontology-migration/SKILL.md).

## Temporal support: current workaround and upstream requirement

The POC calls Semantica's `TemporalGraphQuery` using edge-level `valid_from` / `valid_until` fields. In the curated ontology, the corresponding dates belong to reified association individuals, so the adapter projects them onto graph edges.

The desired behavior is temporal querying directly over temporal properties on reified associations. This POC has not demonstrated that as an out-of-the-box Semantica capability. Record it as an upstream capability question/requirement until Semantica maintainers clarify whether it is supported, intentionally out of scope, or a defect. See [temporal support requirement](docs/temporal-support-requirement.md).

## Main files

- `ontology/northstar.ttl` — curated runtime ontology.
- `northstar_authz/ontology_generation.py` — Semantica ontology generator/exporter with SAP AI Core LiteLLM adapter.
- `northstar_authz/adapter.py` — explicit Northstar source-to-KG mapping and temporal projection.
- `northstar_authz/ontology_validation.py` — mapping completeness and ontology contract checks.
- `northstar_authz/semantica_pipeline.py` — Semantica temporal/reasoning pipeline.
- `docs/decisions/0002-sap-ai-core-and-temporal-ontology-contract.md` — architecture decision.

## References

- [Semantica ontology module](https://github.com/semantica-agi/semantica/blob/main/docs/reference/ontology.md)
- [Semantica knowledge graph module](https://github.com/semantica-agi/semantica/blob/main/docs/reference/kg.md)
- [Semantica reasoning module](https://github.com/semantica-agi/semantica/blob/main/docs/reference/reasoning.md)
