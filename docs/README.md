<!-- mindclade-doc: documentation-home@1 -->

# Mindclade · GitHub platform documentation

> **Platform Foundation · Shared automation and organization policy**  
> Understand, consume, qualify, and release Mindclade's reusable GitHub workflows safely.

## Choose your path

| If you need to... | Start with | You will... |
| --- | --- | --- |
| Understand this repository's boundary | [Architecture](architecture.md) | See how shared workflows, governance, and cloud trust connect |
| Configure GitHub Enterprise | [Enterprise setup](ENTERPRISE_SETUP.md) | Establish teams, rulesets, Actions policy, and release controls |
| Consume or change a reusable workflow | [Workflow contracts](WORKFLOW_CONTRACTS.md) | Preserve caller-visible APIs and choose the correct release level |
| Configure cloud federation | [OIDC and WIF contract](WIF.md) | Bind workflow identity to narrowly scoped Google Cloud access |
| Publish the first production contract | [Workflow release bootstrap](workflow-release-bootstrap.md) | Qualify and publish the immutable `v3.0.0` baseline |

## Getting started

- [Initial import and activation](initial-import.md) — validate and activate this repository in
  the platform dependency order.
- [Enterprise setup](ENTERPRISE_SETUP.md) — configure the GitHub-side controls this repository
  depends on.
- [Workflow trust](workflow-trust.md) — understand immutable references, least privilege, and
  OIDC boundaries.

## Architecture and security

- [Architecture](architecture.md) — component, release, and trust flow.
- [GitHub Actions security model](ACTIONS_SECURITY.md) — non-negotiable workflow invariants.
- [OIDC and WIF contract](WIF.md) — division of identity responsibilities across control
  repositories.
- [Enterprise platform foundation blueprint](MINDCLADE_ENTERPRISE_PLATFORM_FOUNDATION_BLUEPRINT.md)
  — estate-wide architecture and acceptance gates.

## Workflow lifecycle

- [Reusable workflow contracts](WORKFLOW_CONTRACTS.md) — caller-visible compatibility surface.
- [Shared workflow release policy](release-policy.md) — semantic versioning, qualification,
  publication, and consumer rollout.
- [Workflow release bootstrap](workflow-release-bootstrap.md) — first immutable production
  release.

## Authoring standards

- [Documentation style guide](documentation-style.md) — voice, evidence, safety, and review
  expectations.
- [Documentation templates](templates/README.md) — repository home, documentation home,
  architecture, how-to, and runbook patterns.

## Source of truth

Workflow files under `.github/workflows/`, snapshots under `contracts/workflows/`, validators
under `tools/`, and repository policy under `contracts/repository.yaml` are authoritative.
Documentation explains those artifacts; it does not override them.

## Validate documentation changes

Run from the repository root:

```sh
nix develop .#ci --command make validate
```

Also check changed local links and render the Markdown in GitHub's preview before merge.

