<!-- mindclade-doc: documentation-home@1 -->

# Mindclade · Documentation templates

> **Platform Foundation · Documentation system**  
> Portable Markdown patterns for repository homes, architecture, procedures, and runbooks.

These templates define a shared reading experience across Mindclade repositories without
requiring a documentation-site generator. They are starting structures, not boilerplate to
copy blindly: remove sections that do not help the reader and replace every angle-bracketed
prompt before merging.

## Choose a template

| Reader need | Template | Use it for |
| --- | --- | --- |
| Understand and enter a repository | [Repository home](repository-home.md) | Root `README.md` files |
| Navigate a documentation set | [Documentation home](documentation-home.md) | `docs/README.md` files |
| Understand system boundaries and flow | [Architecture](architecture.md) | Conceptual architecture pages |
| Complete a planned task | [How-to guide](how-to-guide.md) | Setup, migration, rotation, and change procedures |
| Restore service under pressure | [Runbook](runbook.md) | Incident diagnosis, mitigation, recovery, and follow-up |

Architecture and operational flow diagrams use Mermaid. The shared palette, diagram choices,
accessibility requirements, and review rules are defined in the
[Mindclade documentation style guide](../documentation-style.md#diagrams).

## Required qualities

Every published page must:

- identify its audience and intended outcome near the beginning;
- distinguish repository authority from dependencies and exclusions;
- derive commands, paths, defaults, and claims from code, tests, contracts, or CI;
- provide a verification step for any procedure;
- put dangerous or irreversible actions after safer diagnostics and label them clearly;
- link to one authoritative source instead of duplicating volatile detail;
- use sequential headings, meaningful link text, and tables only for comparable records; and
- pass local-link and repository validation before merge.

Root repository homes additionally conform to `repository-home@2`: responsive MONO artwork,
local contract-backed badges, no external image requests, no more than 850 prose words, and one
accessible highlighted estate diagram.

The complete writing and review rules are in the
[Mindclade documentation style guide](../documentation-style.md).
