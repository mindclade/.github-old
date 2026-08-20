<!-- mindclade-doc-template: architecture@1 -->

# Mindclade · <System> architecture

> **Audience:** <Primary technical audience>  
> **Outcome:** Understand the system boundary, component relationships, trust model, and
> failure domains before changing it.

## Context

Describe the problem this system solves and its place in the platform.

## Authority boundary

### Owns

- <Resource or decision this system controls.>

### Delegates or depends on

- <Adjacent system, dependency direction, and reason.>

### Explicitly excludes

- <Responsibility that must remain elsewhere.>

## Component model

The diagram shows <the single relationship the reader should understand>.

```mermaid
flowchart LR
    SOURCE["<Source>"] -->|"<reviewed change>"| CONTROL["<Authoritative control>"]
    CONTROL -->|"<applied state>"| TARGET["<Managed target>"]

    classDef authority fill:#0b1f33,color:#ffffff,stroke:#3aa3ff,stroke-width:2px;
    classDef managed fill:#e8f4ff,color:#0b1f33,stroke:#1677b8,stroke-width:1.5px;
    classDef external fill:#f4f7fa,color:#0b1f33,stroke:#66788a,stroke-width:1.5px;
    class CONTROL authority;
    class TARGET managed;
    class SOURCE external;
```

| Component | Responsibility | Source of truth |
| --- | --- | --- |
| `<component>` | <What it does> | `<path>` |

## Change and data flow

Explain the reviewed path from source change to applied state. Identify generated artifacts
and the point where evidence is verified.

## Trust and security boundaries

Document identities, credential boundaries, protected environments, policy enforcement, and
sensitive data handling.

## Failure domains and recovery

Name expected failure modes, blast radius, and the authoritative runbook for each.

## Invariants

- <Property that must remain true.>

## Related documentation

- <Procedure, runbook, contract, and decision links.>
