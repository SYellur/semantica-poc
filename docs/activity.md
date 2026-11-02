# Authorization activity

```mermaid
flowchart TD
    A([Request received]) --> B[Load source facts]
    B --> C[Map entities and relationships]
    C --> D[Project association validity onto temporal edges]
    D --> E[Build knowledge graph]
    E --> F[Query snapshot at requested instant]
    F --> G[Derive inherited teams recursively]
    G --> H[Resolve reachable projects and active direct shares]
    H --> I{Active restriction?}
    I -- Yes --> X[DENY: restriction overrides]
    I -- No --> J{Project route or direct share?}
    J -- No --> Y[DENY: no access route]
    J -- Yes --> K{Classification clearance satisfied?}
    K -- No --> Z[DENY: insufficient clearance]
    K -- Yes --> L[ALLOW]
    X --> M[Build explanation and evidence]
    Y --> M
    Z --> M
    L --> M
    M --> N([Return decision])
```

The activity applies deny-overrides: an active restriction stops evaluation before any allow route can grant access. Confidential clearance is required for both project access and direct-share access.
