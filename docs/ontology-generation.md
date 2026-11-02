# Ontology generation with Semantica

The project keeps a curated schema at `ontology/northstar.ttl`. To propose a new version from the structured source, run:

```bash
# Configure the provider's usual API key environment variable first.
python -m northstar_authz.ontology_generation \
  --source data/northstar.json \
  --output generated/northstar.proposed.ttl \
  --provider openai
```

This calls Semantica's `LLMOntologyGenerator.generate_ontology_from_text` and exports with `OWLGenerator.export_owl`. The prompt supplies a field/type inventory and the Northstar modelling constraints, including reified time-bounded associations and xsd:dateTime fields.

## What it automates

- proposes ontology classes and object/datatype properties from source structure and domain guidance;
- uses Semantica's ontology generator and OWL/Turtle exporter;
- avoids writing a separate LLM prompt/JSON-schema implementation.

## What it does not automate

- It does not create the source record-to-KG mapping rules.
- It does not transform reified association individuals into edge-level `valid_from` / `valid_until` fields.
- It does not author access-control allow/deny policy rules.
- It does not guarantee that the generated schema is semantically correct.

Review the generated file against `ontology/northstar.ttl` before adopting it. Keep `ontology/northstar.ttl` as the curated reference. The mapping adapter remains intentionally small and domain-specific because Semantica's documented LLM ontology generator returns schema classes/properties, not Northstar ETL instructions.
