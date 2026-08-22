<!-- mindclade-doc: style-guide@1 -->

# Mindclade · Documentation style guide

> **Platform Foundation · Authoring standard**  
> Accurate, calm, task-oriented documentation for control-plane and product repositories.

Top-level policy, licensing, community, and changelog files additionally follow the
[common-document contract](common-document-contract.md). Repository-home visual identity and
reader-success rules remain defined here and in
[`templates/repository-home.md`](templates/repository-home.md).
The exact root `LEGAL.md` is the authority for documentation reliance, legal effect, and
representation boundaries; link to it instead of duplicating or paraphrasing legal terms.

## Voice and visual identity

Use `Mindclade · <System>` for repository and documentation-home titles. Follow it with a
two-line callout that names the platform position and the page outcome. The theme is carried
by consistent hierarchy, compact metadata, precise language, generous whitespace, and a
small set of local brand-colored badges. Badges reinforce text; they never carry meaning that
is available only through color.

Write directly to the reader. Prefer “Run `make validate`” to “Validation can be performed.”
Use `Mindclade`, American English for new pages, and the exact product names used in code.

### Brand assets and typography

Use the MONO identity for engineering surfaces: repositories, package pages, command-line
tools, developer documentation, and README headers. Use one identity family per page; do not
mix MONO and CAPS artwork. The canonical source is
`mindclade/.github-private/mindclade-brand-assets`.

Every root README must use the shared repository-home template's centered `<picture>` header.
Vendor the flattened light and dark PNG wordmarks at these repository-relative paths:

- `docs/assets/brand/mono-wordmark-1080w.png`; and
- `docs/assets/brand/mono-wordmark-dark-1080w.png`.

The `.github-private` brand-source repository is the sole exception: its root README links
directly to the canonical files under `mindclade-brand-assets/png/` instead of duplicating
them.

Use the dark wordmark when `prefers-color-scheme: dark` matches, retain the light wordmark as
the fallback, set the rendered width to `360`, and provide meaningful alt text. Use PNGs in
GitHub Markdown because the source SVG wordmarks contain live font-dependent text. Do not
stretch, recolor, shadow, outline, or recreate the wordmark.

Root READMEs use local SVG badges under `docs/assets/badges/`. Class, visibility, and change
model come from `contracts/repository.yaml`; one or two additional badges may show a stable
toolchain or repository characteristic. Use the canonical palette, include an accessible
`<title>`, and never load a badge or image from a third-party service. Do not put numeric
toolchain versions in badges.

GitHub Markdown does not load repository-provided CSS or web fonts. Let GitHub render body
copy in its native interface font; the flattened wordmark preserves the approved MONO
typography. Documentation sites that control their CSS may self-host the brand-kit fonts:
Instrument Sans for headings and body copy, and JetBrains Mono for code, labels, and the MONO
identity. Do not substitute a font inside brand artwork.

Use only the canonical brand tokens in diagrams and custom documentation surfaces:

| Token | Value | Use |
| --- | --- | --- |
| Ink | `#201C24` | Primary text and authoritative controls |
| Clay | `#B5673F` | Primary accent and boundaries |
| Clay light | `#D68A61` | High-contrast accent on ink |
| Bone | `#FBFAF7` | Light surfaces |
| Bone warm | `#F2EFE8` | Managed surfaces and reversed text |
| Body | `#423D48` | Secondary text |
| Muted | `#5B5660` | External or secondary boundaries |
| Rule | `#E2DED4` | Quiet grouping boundaries |

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

Root READMEs follow `repository-home@2`: brand header, local badges, outcome, contract, primary
readers, mission, authority boundary, safe quick start, one highlighted estate diagram,
repository map, change path, canonical links, and security. Quick starts state prerequisites,
an observable success signal, the first failure route, and the external-action safety boundary.
Keep prose at or below 850 words; a simple repository may be shorter rather than padded.

## Evidence standard

Treat tests, executable examples, workflow definitions, public interfaces, contracts, and
configuration defaults as sources of truth. Verify every command, path, flag, default, and
version against repository evidence. Narrow or qualify anything that cannot be verified.

The documentation validator rejects unqualified certification, broad compliance, guarantee,
and contractual response-time claims. An exceptional approved claim must be preceded by a
`mindclade-legal-claim` annotation naming its accountable owner, evidence record, exact scope,
review date, and expiry. The annotation is an auditable exception pointer, not permission to
broaden the claim beyond its evidence.

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
| Shared or authoritative control | `#201C24` | `#F2EFE8` | `#D68A61` |
| Managed component or reviewed stage | `#F2EFE8` | `#201C24` | `#B5673F` |
| External dependency or source | `#FBFAF7` | `#423D48` | `#5B5660` |
| Caution or approval boundary | `#FBFAF7` | `#201C24` | `#B5673F` |
| Failure or stop condition | `#201C24` | `#F2EFE8` | `#B5673F` |

Give caution and failure nodes an explicit label, distinct shape, or dashed stroke in addition
to color. Style Mermaid subgraphs with bone fill and rule-colored boundaries so renderer
defaults cannot introduce off-brand colors.

Start every Mermaid diagram with the shared base-theme directive so unclassified nodes,
connectors, edge labels, and subgraphs also use brand tokens:

```text
%%{init: {"theme":"base","themeVariables":{"primaryColor":"#F2EFE8","primaryTextColor":"#201C24","primaryBorderColor":"#B5673F","secondaryColor":"#FBFAF7","tertiaryColor":"#FBFAF7","lineColor":"#5B5660","edgeLabelBackground":"#FBFAF7","clusterBkg":"#FBFAF7","clusterBorder":"#E2DED4"}}}%%
```

Do not set `fontFamily` in Mermaid embedded on GitHub: the server-side renderer cannot load
the private font files and may choose an unsuitable fallback. A controlled documentation site
may set Instrument Sans after it loads the self-hosted WOFF2 asset.

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
6. headings and link text are accessible;
7. diagrams follow the Mermaid conventions and retain a text equivalent;
8. root READMEs use the approved responsive MONO wordmark and local badges;
9. repository homes pass the `repository-home@2` validator; and
10. no generated output or unrelated formatting churn is included.
