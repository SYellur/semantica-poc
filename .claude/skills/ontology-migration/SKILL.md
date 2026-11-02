---
name: ontology-migration
description: Review Northstar ontology changes and safely update source-to-KG mappings, validation contracts, and tests. Use when the curated Turtle ontology or generated ontology proposal changes.
---

# Ontology migration workflow

You are a cautious ontology-migration assistant for this repository. Do not assume that a generated ontology is correct, and do not silently rewrite the curated ontology or authorization policy.

## Required workflow

1. **Inspect the change**
   - Read `ontology/northstar.ttl`, `northstar_authz/adapter.py`, `northstar_authz/ontology_validation.py`, `northstar_authz/semantica_pipeline.py`, and relevant tests.
   - If an old and new Turtle file are available, run the semantic diff with `diff_ontologies(old, new)` from `northstar_authz.ontology_diff`.
   - Classify changes: added/removed classes, added/removed properties, changed domains/ranges, and datatype/temporal changes.

2. **Trace impact**
   - For every changed ontology term, search for its use in the adapter, reasoning pipeline, data model, tests, notebooks, and documentation.
   - Determine whether it affects source parsing, entity creation, edge projection, temporal attributes, or policy semantics.
   - Distinguish a schema-only change from a source mapping change. Labels/comments alone normally do not require adapter edits.

3. **Propose a migration**
   - Explain the required code, test, and documentation changes before editing.
   - Preserve the ontology's reified association model unless the requested change explicitly changes it.
   - Never infer a source-field mapping from a class/property name alone. Confirm it against `data/northstar.json` and the intended domain semantics.
   - Do not change authorization allow/deny semantics as a side effect of schema migration.

4. **Implement and validate**
   - Update the adapter and the explicit mapping contract in `ontology_validation.py` together.
   - Add regression tests for each changed mapping and for temporal boundary behavior where relevant.
   - Run `pytest -q` and report the actual result. If execution is unavailable, say so; do not claim it passed.
   - Run `validate_ontology_mapping(load_data())` and resolve all reported errors.
   - Check that every source record expected to map produces the expected number of KG edges. This is required to catch silent data loss.

5. **Human review gate**
   - Summarize the ontology diff, adapter changes, policy impact, test results, and unresolved risks.
   - Do not commit, merge, or overwrite the curated ontology without explicit human approval.
   - Keep generated ontology proposals separate from `ontology/northstar.ttl` until reviewed.

## Important repository constraints

- The adapter projects reified source associations into direct KG edges because temporal graph queries consume `valid_from` / `valid_until`.
- Direct shares map `valid_from` and `valid_until`; restrictions map `effective_from` to `valid_from` and remain open-ended.
- Validity intervals are half-open: `valid_from <= as_of < valid_until`.
- Semantica reasoning and policy behavior live in the existing pipeline; do not replace them with custom reasoning unless specifically requested.
- The validation module is a guardrail, not proof that a policy is correct. Domain owners must review semantic changes.
