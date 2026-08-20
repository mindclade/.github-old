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
%%{init: {"theme":"base","themeVariables":{"primaryColor":"#F2EFE8","primaryTextColor":"#201C24","primaryBorderColor":"#B5673F","secondaryColor":"#FBFAF7","tertiaryColor":"#FBFAF7","lineColor":"#5B5660","edgeLabelBackground":"#FBFAF7","clusterBkg":"#FBFAF7","clusterBorder":"#E2DED4"}}}%%
flowchart LR
    SOURCE["<Source>"] -->|"<reviewed change>"| CONTROL["<Authoritative control>"]
    CONTROL -->|"<applied state>"| TARGET["<Managed target>"]

    classDef authority fill:#201C24,color:#F2EFE8,stroke:#D68A61,stroke-width:2px;
    classDef managed fill:#F2EFE8,color:#201C24,stroke:#B5673F,stroke-width:1.5px;
    classDef external fill:#FBFAF7,color:#423D48,stroke:#5B5660,stroke-width:1.5px;
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
