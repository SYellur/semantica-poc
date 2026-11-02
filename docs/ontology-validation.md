# Ontology and mapping validation

Run the validator against the sample data:

```bash
python -c "from northstar_authz.service import load_data; from northstar_authz.ontology_validation import assert_ontology_mapping_valid; assert_ontology_mapping_valid(load_data())"
```

The validator checks ontology declarations, emitted relationship types, domain/range compatibility, relationship endpoint existence, source-record-to-edge counts, and temporal date projection. The source-record counts are important: a valid ontology alone cannot detect a record that the adapter silently skipped.

Compare two Turtle ontology versions with:

```python
from northstar_authz.ontology_diff import diff_ontologies

report = diff_ontologies("ontology/previous.ttl", "ontology/northstar.ttl")
print(report)
```

The report separates additions and removals for classes, object properties, datatype properties, domains, and ranges.

The Claude workflow is in `.claude/skills/ontology-migration/SKILL.md`. It requires the agent to trace changes into the adapter, reasoning pipeline, tests, and documentation, then run the validation gate and regression suite. Human review remains required before changing the curated ontology or merging migration changes.
