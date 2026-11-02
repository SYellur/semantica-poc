# Authorization request sequence

```mermaid
sequenceDiagram
    autonumber
    actor Caller
    participant Service as Authorization service
    participant Mapper as Northstar adapter
    participant Builder as Semantica GraphBuilder
    participant Temporal as TemporalGraphQuery
    participant Datalog as DatalogReasoner
    participant Rules as Semantica Reasoner
    participant Explain as ExplanationGenerator

    Caller->>Service: check(person, document, as_of)
    Service->>Mapper: map source records
    Mapper-->>Service: entities + relationships (+ temporal edge fields)
    Service->>Builder: build(graph input)
    Builder-->>Service: knowledge graph
    Service->>Temporal: query_at_time(graph, as_of)
    Temporal-->>Service: point-in-time snapshot
    Service->>Datalog: derive team/project closure
    Datalog-->>Service: project_access facts
    Service->>Rules: evaluate policy facts and IF-THEN rules
    Rules-->>Service: Allow inference or no proof
    opt Successful inference
        Service->>Explain: generate_explanation(inference result)
        Explain-->>Service: natural-language explanation
    end
    Service-->>Caller: ALLOW or DENY + evidence
```

The default CLI uses the deterministic reference evaluator for a fast demonstration. The Python function `evaluate_with_semantica` exercises the Semantica-backed reasoning path.
