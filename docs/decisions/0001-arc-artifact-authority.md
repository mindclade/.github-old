<!-- mindclade-doc: architecture-decision@1 -->

# ADR-0001: ARC is the authoritative artifact CI platform

**Status:** Accepted for source implementation; connected activation pending  
**Date:** 2026-08-20  
**Owners:** Platform and Security

## Decision

GitHub Actions Runner Controller on a dedicated private GKE cluster replaces Buildkite for
authoritative builds and qualification. Pull-request jobs remain GitHub-hosted. Release authority
begins only when one versioned request is merged to protected `main`; manual/API dispatches and
tags cannot exchange a privileged token.

The trusted source/ref check lives in an immutable `.github` reusable workflow. Bootstrap WIF
conditions independently require immutable organization/repository IDs, the exact audience,
`push`, `refs/heads/main`, the exact caller, and the exact released `job_workflow_ref`. Replacing a
validator in the checked-out monorepo therefore cannot grant cloud authority.

Builder, qualification reader, qualifier attestor, signer, promoter, Argo CD reconciler, and
runtime identities remain separate. The signer stays on a GitHub-hosted runner behind the
`release` environment. The promoter can open a GitOps PR but cannot merge it or sign an artifact.

## Ownership

- `.github`: immutable reusable workflow implementations and API snapshots.
- `github-config`: runner group, workflow restrictions, GitHub App installation contract,
  critical-path reviews, environments, and non-secret variables.
- `bootstrap`: capability-specific GitHub OIDC providers and trust outputs.
- `infrastructure-live`: dedicated CI VPC, private GKE, IAM/KMS/Secret Manager, and node pools.
- `gitops`: dedicated CI Argo CD and ARC desired state.
- monorepo: release requests, target catalog, Bazel graph, and release workflow caller.

## Activation and rollback

Buildkite remains unprovisioned during source rollout. ARC is activated in order: zero-authority
upstream-image canary, custom-runner qualification, builder/qualifier authority, signing and
promotion, GPU lanes, then Buildkite source retirement after two successful releases and a
recovery drill.

Rollback sets runner scale sets to zero, disables the affected WIF provider and runner group,
and restores the prior qualified runner digest. It never grants Buildkite authority as a
fallback.
