# ADR-001: Keep ontology generation and KG mapping separate

- **Status:** Accepted for the POC
- **Date:** 2026-11-02

## Context

The POC can use Semantica's `LLMOntologyGenerator` to propose ontology classes and properties. The generated ontology may differ from the curated Northstar ontology.

The KG adapter currently maps Northstar JSON fields to a known set of entity types and relationship names. It also projects dates from reified share and restriction records onto graph relationships for Semantica's temporal query API.

Therefore, a newly generated ontology does not automatically make the existing adapter compatible. If class or property names, domains, ranges, or modelling choices change, the adapter mapping may need to change as well.

## Decision and approach taken

For this POC:

1. Use Semantica's ontology generator to create a **proposal**, not an automatically adopted runtime schema.
2. Review and curate the proposal before using it.
3. Keep an explicit Northstar-specific adapter that maps source JSON to the approved ontology/KG structure.
4. Keep temporal projection logic explicit in the adapter.
5. Do not regenerate or silently change the runtime KG schema on each request.

A future extension may generate a mapping specification alongside the ontology. That specification would map source entities and fields to ontology classes and properties, describe relationship construction, and identify temporal fields. It must be validated and approved before the adapter uses it. **This dynamic mapping specification is not implemented in the current POC.**

## Benefits

- Keeps KG construction predictable and testable.
- Prevents an LLM-generated schema change from silently changing authorization behaviour.
- Makes source-to-KG transformations visible and reviewable.
- Keeps the custom code limited to domain-specific mapping while Semantica handles graph construction and reasoning.

## Pros

- Clear separation between domain modelling and source-data transformation.
- Easier to debug when source data or ontology changes.
- Supports deterministic tests without calling an LLM.
- Allows ontology proposals to be explored without breaking the working KG pipeline.

## Cons

- The adapter must be updated when approved ontology properties or source structures change.
- Generated ontology and adapter mapping can drift unless checked together.
- It is not fully dynamic or schema-independent.
- A new data source or substantially different ontology may require additional mapping work.

## Challenges

- Keeping ontology classes/properties aligned with adapter relationship names.
- Mapping source records to the correct ontology entities and relationships.
- Handling reified associations whose dates or other attributes must be projected onto KG edges.
- Validating that generated mappings preserve domain meaning and authorization semantics.
- Detecting breaking ontology changes before they reach runtime.

## When to use

Use this approach when:

- The domain and source schema are reasonably stable.
- Correctness and predictable authorization decisions matter more than automatic schema flexibility.
- Ontology proposals can be reviewed and approved before use.
- There are a manageable number of source-to-ontology mappings.

## When to avoid

Avoid relying on a manually maintained adapter alone when:

- Many unrelated data sources and frequently changing schemas must be supported.
- Ontologies are generated or changed frequently without a review step.
- The cost of maintaining mappings becomes high.
- The system requires genuinely schema-driven ingestion across domains.

In those cases, consider a generated mapping specification with validation, versioning, compatibility checks, and human approval. Do not assume ontology generation alone provides this capability.

## Consequences

The current POC deliberately favours a reviewed ontology and explicit adapter over automatic ontology-driven KG generation. This introduces some maintenance work, but avoids treating an LLM-generated ontology as an executable source-data mapping.

Semantica's `LLMOntologyGenerator` proposes ontology structure; the POC adapter performs Northstar-specific source-to-KG mapping. These are separate responsibilities.
