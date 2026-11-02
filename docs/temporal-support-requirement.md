# Semantica temporal support requirement: reified associations

## Context

Northstar models qualified relationships as reified ontology individuals, including `DirectDocumentShare` and `DocumentRestriction`. Temporal properties (`validFrom`, `validUntil`, and `effectiveFrom`) belong to those association individuals.

The current POC projects these dates onto graph relationship fields `valid_from` / `valid_until` because the runtime uses `TemporalGraphQuery.query_at_time(..., at_time=...)` on graph edges.

## Desired capability

Support temporal validity directly for qualified/reified associations represented in an ontology/KG, without requiring each application to flatten or duplicate dates onto edge-level fields.

Expected behavior:
- Interpret start/end validity consistently, including open-ended records.
- Support half-open intervals where specified: `valid_from <= as_of < valid_until`.
- Filter/reconstruct a point-in-time graph while retaining identity and attributes of the reified association.
- Document the contract between ontology temporal properties and temporal query behavior.
- Test start boundary, end boundary, open-ended records, and multiple association instances between the same subject/object.

## Current POC workaround

- `DirectDocumentShare.validFrom` -> edge `valid_from`
- `DirectDocumentShare.validUntil` -> edge `valid_until`
- `DocumentRestriction.effectiveFrom` -> edge `valid_from`, with open-ended `valid_until`

The workaround is explicit and validated in the POC. It is not evidence of native, out-of-the-box support for temporal properties on reified associations.

## Upstream question

Please clarify whether this behavior is supported today, intentionally outside the temporal query module's scope, or an integration gap/bug. If unsupported, document the recommended pattern or consider native temporal handling for reified association entities.
