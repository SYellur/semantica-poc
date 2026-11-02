# ADR-003: Structured-source ontology discovery and human-approved schema design

- **Status:** Proposed for stakeholder review
- **Date:** 2026-11-02
- **Scope:** Structured source data (for example, JSON, CSV, or API payloads)

## Context

The POC needs a repeatable way to derive the domain entities, relationships, and temporal semantics represented by structured source data.

A structured payload contains both records and a schema-like structure. Feeding complete record content directly into a single ontology-generation prompt is not a sufficient production design assumption: large datasets and large target ontologies can exceed practical prompt/context budgets, introduce noise from individual records, and make the generated result difficult to review. The exact limits depend on the model, prompt, and dataset and must be measured; this ADR does not claim that every Semantica ontology-generation use case is inherently single-shot or unsuitable for production.

The current POC already distinguishes Semantica ontology proposals from the curated runtime ontology. It also records that the source-to-KG mapper is explicit and that temporal values need deliberate modelling and validation. This ADR defines the preceding structured-data discovery and approval workflow. It does not replace ADR-002's runtime decisions.

## Decision

For structured sources, use a Claude Skill-assisted ontology discovery workflow, with deterministic preprocessing and mandatory human approval:

1. **Inspect and profile the source deterministically.**
   - Read the supplied source files or API payloads.
   - Parse the structure programmatically.
   - Clean and normalize metadata deterministically (for example, field names, nesting, declared types, nullability, sample counts, and observed value shapes).
   - Keep representative values only when needed to resolve ambiguity; do not send the full dataset by default.
   - Preserve provenance back to source paths/fields so proposed concepts can be traced to the input.

2. **Prepare a metadata-only or metadata-first representation.**
   - Produce a compact source profile containing field paths, types, cardinality/nullability observations, nesting, candidate keys, and references between records where detectable.
   - Separate observed facts from inferred meaning. A field named team_id, for example, is evidence of a possible reference, not proof of a domain relationship.
   - Record temporal candidates such as valid_from, valid_to, effective dates, event timestamps, and their source formats. Do not silently assume that every timestamp is a validity interval.

3. **Use the Claude Skill to propose the domain model.**
   - Supply the source profile and domain context to the skill.
   - Ask it to propose entity candidates, relationship candidates, relationship direction/cardinality, identifiers, datatype/object properties, and temporal semantics where supported by evidence.
   - Require each proposal to include its source-field evidence, assumptions, unresolved questions, and confidence/rationale.
   - For large inputs, process bounded profiles or logical source groups and reconcile the proposals, rather than assuming one unbounded prompt can model the complete domain.

4. **Validate the proposal against the ontology contract and Semantica capabilities.**
   - Check that the candidate classes and properties are internally consistent and that relationship endpoints, domains/ranges, and datatypes are coherent.
   - Use Semantica ontology validation where applicable as a technical validation step.
   - Explicitly inspect temporal modelling. A technically valid ontology is not, by itself, proof that valid-time semantics have been captured correctly or that the current Semantica temporal query path supports the chosen representation.
   - Record unsupported or uncertain constructs as review findings rather than silently translating or dropping them.

5. **Require human domain review before approval.**
   - Review entity/relationship proposals, temporal interpretation, identifiers, cardinality, and unresolved assumptions with stakeholders.
   - The LLM is a proposal assistant, not the authority that approves domain semantics.
   - The human reviewers decide the intended model and resolve ambiguities. Persist the approved ontology and review outcome as versioned artifacts.

6. **Compare alternative generation outputs.**
   - For the POC, generate a Semantica ontology proposal and a Claude Skill-assisted proposal from the same prepared source profile.
   - Produce a semantic diff covering classes, properties, domains/ranges, relationship direction/cardinality, identifiers, and temporal constructs.
   - Use the diff to support review; do not treat either generator's output as ground truth.

## Why not rely only on the existing Semantica LLM ontology-generation path?

Semantica's generator remains useful as a baseline and proposal-generation capability, and it should be demonstrated rather than dismissed. However, the POC's structured-data workflow needs explicit control over:

- deterministic source profiling rather than relying on raw record text as the sole input;
- evidence-backed entity and relationship discovery;
- temporal semantics and the distinction between event time and valid time;
- bounded processing and reconciliation for larger source schemas;
- human resolution of domain ambiguity; and
- a reviewable diff and approval record before the ontology becomes the runtime contract.

The concern about a single-shot prompt is therefore a production architecture risk to test with representative schema sizes and model context limits. The proposed skill workflow gives us an explicit place to introduce profiling, decomposition, reconciliation, and review. It does not guarantee scalability automatically.

## Consequences

### Positive

- Full source records need not be sent to the LLM merely to discover the schema.
- Entity and relationship proposals can be traced to source fields and reviewed.
- Temporal candidates are surfaced as first-class modelling questions.
- Stakeholders can compare Semantica and skill-generated proposals before approving a model.
- Human approval prevents generated ontology output from silently becoming the production contract.

### Trade-offs and risks

- The source profiler and proposal reconciliation workflow require implementation and tests.
- The LLM may infer incorrect relationships from naming or sample values; evidence and human review remain mandatory.
- Human ontology review is intentionally a time-consuming governance step.
- SHACL and ontology validation can check declared constraints, but cannot independently decide whether the domain model reflects business meaning.
- Temporal rules may require explicit SHACL constraints or application-level checks; do not assume all cross-field interval semantics are inferred automatically.
- This ADR does not select a final production strategy for incremental ontology evolution, mapper regeneration, or large-scale reasoning.

## POC acceptance criteria

- Run both Semantica's generator and the Claude Skill workflow against the same structured source profile.
- Show the deterministic source profiling output and the evidence supporting proposed entities and relationships.
- Show temporal candidates and explicitly distinguish valid time from event/transaction time where relevant.
- Present a semantic diff between the two candidate ontologies.
- Conduct a stakeholder review and record accepted changes, rejected proposals, and unresolved questions.
- Persist only the human-approved ontology as the candidate runtime contract.
- Demonstrate at least one ambiguous or malformed source field and show that the workflow requests human resolution instead of inventing a mapping.

## Out of scope

- Automatically generating or approving the source-to-KG mapper. That is a separate ingestion design decision and must consume the approved ontology.
- Automatically loading an unreviewed ontology into the runtime graph.
- Claiming that Semantica lacks all production scalability or that a Claude Skill alone solves large-ontology scalability.
- Treating SHACL validation as a substitute for domain-expert review.

## Relationship to existing decisions

- **ADR-002:** Retains Semantica's role in ontology proposal generation and the curated runtime ontology boundary. ADR-003 adds a structured-source discovery and human-approval workflow before a candidate ontology is adopted.
- The subsequent mapper/ingestion decision must define deterministic source-to-ontology transformation, edge-case policy, SHACL/data validation, temporal validation, and fail-closed behavior before graph construction.
