# Authorization request — sequence by component

The sequence below shows the **runtime path**. Ontology proposal generation is intentionally excluded: it is a separate, optional design-time activity.

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant Service as Northstar service
    participant Adapter as Northstar adapter
    participant GB as Semantica · GraphBuilder
    participant TQ as Semantica · TemporalGraphQuery
    participant DL as Semantica · DatalogReasoner
    participant R as Semantica · Reasoner
    participant EG as Semantica · ExplanationGenerator

    Client->>Service: check(person, document, as_of)
    Service->>Adapter: map Northstar JSON + ontology-aligned model
    Note over Adapter: Map entities/relationships<br/>Project association dates to edge validity
    Adapter-->>Service: GraphBuilder input
    Service->>GB: build(entities, relationships)
    GB-->>Service: Knowledge graph
    Service->>TQ: query_at_time(graph, as_of)
    TQ-->>Service: Point-in-time snapshot

    Service->>DL: Add membership, parent-team,<br/>ownership and assignment facts
    Service->>DL: Add recursive team_access / project_access rules
    Service->>DL: derive_all() + query project_access
    DL-->>Service: Reachable projects

    Note over Service,R: Active shares and restrictions are read from the same temporal snapshot
    Service->>R: Add project, document, clearance,<br/>active-share and no-active-restriction facts
    Service->>R: Add Northstar IF–THEN access rules
    Service->>R: forward_chain()
    R-->>Service: Allow inference or no Allow proof

    alt Allow inference found
        Service->>EG: generate_explanation(inference_result)
        EG-->>Service: Natural-language explanation
        Service-->>Client: ALLOW + explanation
    else No Allow inference
        Note over Service: Determine whether an active restriction<br/>or missing route/clearance explains the denial
        Service-->>Client: DENY + reason
    end
```

## Where each component participates

1. **GraphBuilder** turns the adapter's mapped entities and relationships into the KG.
2. **TemporalGraphQuery** supplies the graph valid at the requested instant.
3. **DatalogReasoner** recursively derives inherited teams and project access.
4. **Reasoner** evaluates the document policy against those derived facts and the active temporal facts.
5. **ExplanationGenerator** explains a successful Allow inference. Denial messages are currently assembled by the service.

See the [high-level architecture](architecture.md) for the design-time ontology workflow and the custom/Semantica boundary.
