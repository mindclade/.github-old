<!-- mindclade-doc: style-guide@1 -->

# Mindclade · Documentation style guide

> **Platform Foundation · Authoring standard**  
> Accurate, calm, task-oriented documentation for control-plane and product repositories.

## Voice and visual identity

Use `Mindclade · <System>` for repository and documentation-home titles. Follow it with a
two-line callout that names the platform position and the page outcome. The theme is carried
by consistent hierarchy, compact metadata, precise language, and generous whitespace—not by
decorative badges or color-dependent meaning.

Write directly to the reader. Prefer “Run `make validate`” to “Validation can be performed.”
Use `Mindclade`, American English for new pages, and the exact product names used in code.

## Information architecture

Keep one primary reader need per page:

- repository homes orient and route;
- tutorials teach a controlled first success;
- how-to guides complete a specific planned task;
- architecture pages explain boundaries, flow, and trade-offs;
- reference pages provide exact contracts and defaults; and
- runbooks start from an observable failure and restore service safely.

Place volatile facts in one authoritative page and link to it. Preserve existing filenames and
anchors when moving content would break links.

## Evidence standard

Treat tests, executable examples, workflow definitions, public interfaces, contracts, and
configuration defaults as sources of truth. Verify every command, path, flag, default, and
version against repository evidence. Narrow or qualify anything that cannot be verified.

For procedures, include prerequisites, stop conditions, expected results, independent
verification, and recovery guidance. Never make success depend on an undocumented chat,
individual memory, or the failed runtime itself.

## Markdown conventions

- Use one level-one heading per page and sequential heading levels.
- Add a blank line around headings, lists, tables, callouts, and fenced blocks.
- Label command fences `sh`; use `text`, `yaml`, `json`, `hcl`, or the actual language for
  other content.
- Use meaningful link text and repository-relative links for files in the same repository.
- Use tables for short comparable records, never to package paragraphs.
- Wrap prose consistently with the repository's existing formatter; do not wrap URLs or code.
- Use ASCII punctuation in commands and identifiers. Prose may use typographic punctuation
  where it renders reliably.

## Diagrams

Use Mermaid for diagrams embedded in Markdown. Choose the smallest diagram that materially
clarifies a relationship: `flowchart` for architecture and dependency direction,
`sequenceDiagram` for interactions, `stateDiagram-v2` for lifecycle, and a table when exact
field-by-field comparison matters more than topology.

Every Mermaid diagram must:

- have a short sentence immediately before it that states what the reader should learn;
- use accessible labels rather than relying on node identifiers;
- preserve meaning in the surrounding prose or table for renderers without Mermaid support;
- keep direction predictable (`LR` for estates and flows, `TD` for layered dependencies);
- avoid icons, unapproved external assets, and color-only status signals; and
- use the shared Mindclade palette when classes improve comprehension.

Use these class colors consistently:

| Role | Fill | Text | Stroke |
| --- | --- | --- | --- |
| Shared or authoritative control | `#0b1f33` | `#ffffff` | `#3aa3ff` |
| Managed component or reviewed stage | `#e8f4ff` | `#0b1f33` | `#1677b8` |
| External dependency or source | `#f4f7fa` | `#0b1f33` | `#66788a` |
| Caution or approval boundary | `#fff4d6` | `#0b1f33` | `#b7791f` |
| Failure or stop condition | `#fde8e8` | `#5f1717` | `#c53030` |

Do not add a diagram when a sentence or compact table communicates the same information more
precisely. Validate Mermaid fences and syntax in the documentation build before merge.

## Safety and confidentiality

Never include credentials, private keys, secret values, customer data, private model weights,
restricted biological data, raw Terraform state, or unsanitized plan output. Put destructive
commands after read-only diagnostics, label their blast radius, and require the same approvals
as the underlying system.

## Review checklist

Before merge, confirm:

1. the page's audience and outcome are clear;
2. ownership and exclusions match `contracts/repository.yaml` or equivalent code;
3. commands match the Makefile, scripts, and CI;
4. local links and anchors resolve;
5. procedures include verification and recovery;
6. headings and link text are accessible; and
7. diagrams follow the Mermaid conventions and retain a text equivalent; and
8. no generated output or unrelated formatting churn is included.
