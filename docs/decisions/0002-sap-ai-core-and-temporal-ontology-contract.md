# ADR-002: SAP AI Core ontology generation and curated runtime ontology

- **Status:** Accepted for the POC
- **Date:** 2026-11-02

## Context

The POC uses Semantica for ontology proposal generation, graph construction, temporal graph querying, recursive Datalog inference, policy inference, and successful-allow explanations. Design-time ontology generation calls SAP AI Core through LiteLLM, without custom OAuth or raw HTTP code.

The curated runtime ontology is `ontology/northstar.ttl`. The explicit source-to-KG mapper is `northstar_authz/adapter.py`. An ontology proposal does not define how every Northstar JSON source record maps to ontology classes, properties, graph nodes, or edges.

If the ontology changes and the mapper is not adapted, source records or fields may be dropped, edges may be mis-typed, or semantics may drift. Ontology changes must therefore be treated as coordinated schema-and-mapping migrations.

The current POC projects temporal values from reified share/restriction associations onto edge-level `valid_from` / `valid_until` fields for `TemporalGraphQuery`. The desired behavior is for temporal support to work directly with the qualified/reified ontology model. The POC has not demonstrated that end-to-end behavior as an out-of-the-box Semantica capability. This is an upstream capability question/requirement, not a confirmed Semantica bug.

## Decision

1. Use Semantica's `LLMOntologyGenerator` and `OWLGenerator` for design-time ontology proposals.
2. Route generation through a thin adapter over Semantica's `LiteLLM` wrapper with a `sap/<model>` identifier, defaulting to `sap/gpt-4o`.
3. Let LiteLLM read `AICORE_SERVICE_KEY` and `AICORE_RESOURCE_GROUP`; do not implement OAuth/HTTP in this POC.
4. Keep generated Turtle under `generated/` as a proposal. Never overwrite curated `ontology/northstar.ttl` automatically.
5. Keep two primary notebooks: SAP AI Core + Semantica ontology proposal generation; and curated ontology + explicit mapping + Semantica KG/temporal/reasoning runtime.
6. Keep the Northstar adapter explicit and narrow. It creates KG entities/relationships and projects temporal fields required by the current temporal query path.
7. Require ontology diff, mapper impact review, source-record coverage validation, temporal projection checks, regression tests, and human approval for every adopted schema change.
8. Track native temporal support for reified association individuals as a Semantica capability requirement. The POC projection is a compatibility workaround, not proof of native reified temporal support.

## Consequences

- SAP credentials and the SAP AI Core model deployment must be configured outside source control.
- Ontology proposals can be generated without changing runtime behavior.
- Mapper maintenance remains necessary while source-to-KG mapping is explicit.
- Validation catches configured mapping omissions and type/predicate mismatches, but cannot prove the ontology or authorization policy is semantically correct.
- Temporal projection remains in the adapter until Semantica documents/supports temporal properties on reified association entities or another agreed design is adopted.

## Required migration workflow

1. Diff old and candidate Turtle files.
2. Identify changed classes, object/datatype properties, domains, ranges, and temporal fields.
3. Trace each change into source JSON, mapper, validation contract, reasoning pipeline, tests, notebooks, and docs.
4. Update mapper and validation together. Never infer source mappings from generated names alone.
5. Verify entity/edge coverage, endpoint typing, and temporal date preservation.
6. Run regression tests and compare authorization outcomes.
7. Obtain human approval before replacing the curated ontology.

Notebook 01 demonstrates design-time generation. Notebook 02 demonstrates runtime against the reviewed Turtle ontology. Regenerating the ontology does not automatically migrate a source mapper.
