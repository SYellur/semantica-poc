# Authorization decision — activity by Semantica stage

```mermaid
flowchart TD
    START(["Access request<br/>person · document · as_of"])

    subgraph PREP["A · Northstar-specific preparation"]
        direction TB
        LOAD["Load Northstar source records"]
        MAP["Adapter maps entities + relationships"]
        TEMP_FIELDS["Project share/restriction dates<br/>onto temporal edge fields"]
        LOAD --> MAP --> TEMP_FIELDS
    end

    subgraph KG["B · Semantica KG + temporal"]
        direction TB
        BUILD["GraphBuilder<br/>Build knowledge graph"]
        SNAP["TemporalGraphQuery<br/>Create as-of snapshot"]
        BUILD --> SNAP
    end

    subgraph RECURSION["C · Semantica recursive reasoning"]
        direction TB
        FACTS["Load membership, parent-team,<br/>project-owner and assignment facts"]
        RULES["DatalogReasoner<br/>Apply recursive team_access rules<br/>and project_access rules"]
        PROJECTS["Return reachable projects"]
        FACTS --> RULES --> PROJECTS
    end

    subgraph POLICY["D · Semantica policy reasoning"]
        direction TB
        POLICY_FACTS["Reasoner facts:<br/>reachable projects · document project<br/>classification · clearance<br/>active shares · no active restriction"]
        APPLY["Reasoner.forward_chain()<br/>Evaluate Northstar IF–THEN rules"]
        ALLOW{"Allow inference found?"}
        POLICY_FACTS --> APPLY --> ALLOW
    end

    subgraph RESULT["E · Decision response"]
        direction TB
        EXPLAIN["ExplanationGenerator<br/>Explain successful inference"]
        DENY["Service builds denial reason<br/>active restriction / no route / clearance"]
        OUT_ALLOW(["ALLOW + explanation"])
        OUT_DENY(["DENY + reason"])
        EXPLAIN --> OUT_ALLOW
        DENY --> OUT_DENY
    end

    START --> LOAD
    TEMP_FIELDS --> BUILD
    SNAP --> FACTS
    PROJECTS --> POLICY_FACTS
    SNAP -. "active shares + restrictions" .-> POLICY_FACTS
    ALLOW -- Yes --> EXPLAIN
    ALLOW -- No --> DENY

    classDef sem fill:#e7f1ff,stroke:#2864a5,color:#15385b,stroke-width:1.5px
    classDef custom fill:#fff2d8,stroke:#b7791f,color:#5b3b0b,stroke-width:1.5px
    classDef decision fill:#fff7d6,stroke:#a17b18,color:#55400b,stroke-width:1.5px
    classDef output fill:#f1eafe,stroke:#7751a8,color:#38245b
    class MAP,TEMP_FIELDS custom
    class BUILD,SNAP,FACTS,RULES,PROJECTS,POLICY_FACTS,APPLY,EXPLAIN sem
    class ALLOW decision
    class OUT_ALLOW,OUT_DENY output
```

## Reading the decision

- **TemporalGraphQuery** removes expired or not-yet-effective share/restriction edges for the requested instant.
- **DatalogReasoner** derives inherited team membership and project reachability; this is the recursive part.
- **Reasoner** grants access only when a project route or direct share meets the classification rule and there is no active restriction.
- An active restriction prevents the service from adding the `NoActiveRestriction` fact, so no Allow rule can use that pair.
- **ExplanationGenerator** explains successful Allow inference. The current POC formats denial reasons in application code.
