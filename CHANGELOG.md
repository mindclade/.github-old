<!-- mindclade-doc: changelog@1 -->

# Changelog

## Policy bundle 2026.08.23.1 (planned with v5.0.0; not published)

### Added

- Add sealed evidence claim, verification, deployment-bundle, exception, eligibility-decision,
  and production-control contracts for synchronized fleet adoption.
- Define the initial ten-control production-eligibility policy with bounded freshness and
  explicit exception eligibility.
- Add append-only policy-bundle version history and base-commit immutability enforcement.

### Changed

- Define `.github-private` as the checked-in brand distribution rather than a brand-governance
  authority.

All notable changes to the versioned reusable-workflow contract are recorded here. Consumers
pin immutable full-semver releases, so a merged change reaches a consumer only after a new
release is published and the consumer updates its `uses:` reference.

The format follows Keep a Changelog. Semantic versioning applies to reusable workflow inputs,
outputs, secrets, defaults, job identifiers, permissions, and observable behavior.

## Policy bundle 2026.08.21.4 (planned with v5.0.0; not published)

### Added

- Bind each managed consumer to the exact v5 release commit, policy-manifest digest, bundle
  version, and repository-home validator digest through a machine-readable adoption record.
- Enforce contributor authorization, hold-marker removal, and published policy-sync provenance
  whenever a pull request becomes eligible to merge.

### Security

- Parse README URLs and require the exact `img.shields.io` hostname when rejecting remote
  Shields badges; deceptive lookalike hosts, userinfo prefixes, and redirect parameters do not
  satisfy the hostname check.
- Synchronize policy artifacts only from the published, source-attested v5 tag rather than from
  mutable `main`.

## v5.0.0 (planned; not published)

### Added

- Added retained native Nix qualification evidence for Linux AMD64, Linux ARM64, and Apple Silicon.
- Added an activation-blocked Nix cache population workflow for the canonical monorepo. It
  requires protected main, independent environment approval, an exact immutable checkout, and a
  cache-scoped write token while explicitly excluding pull requests, cloud authority, server
  secrets, and client signing keys. No caller is enabled before connected cache qualification.
- Added `reusable-nix-qualification.yml` with internal change detection, isolated CI-shell
  validation, and an always-present verdict job.
- Added native Linux arm64 and Apple Silicon qualification to the reusable Nix contract.
- Added two-runner `nix build --rebuild` evidence with deterministic output-hash comparison.

### Changed

- Run the two x86_64-linux reproducibility rebuilds on Ubuntu 24.04 and 22.04, record the exact
  OS evidence, and reject identical runner images before comparing derivations, store paths, and
  output hashes.
- **Breaking (publish as v5.0.0):** `reusable-gitops-promote.yml` replaces the ambiguous
  `rollback-digest` input with the exact `previous-release-id` and
  `previous-subject-digest` lineage pair, and requires the closed-catalog `application` and
  `release-kind` identity required by the GitOps v1beta1 promotion contract. The workflow
  rejects a previous release that is not numerically older than the candidate.
  The historical v4 contract is retired unpublished; no consumer may adopt this change until an
  explicitly reviewed immutable release is published.
- **Breaking (publish as v5.0.0):** `reusable-oci-build.yml` now enriches every SPDX 2.3
  SBOM with the complete proprietary `LicenseRef`, a digest-bound first-party package, and
  reviewed third-party notice coverage before upload or attestation. Callers must first
  synchronize policy bundle `2026.08.21.4`, including both SBOM/notice tools and their
  repository-specific provenance contract.
- **Breaking (publish as v5.0.0):** release attestation schema 2 covers every reusable and
  required workflow, workflow contract, repository-home action file, policy tool, and policy
  manifest file. Undeclared, missing, duplicate, non-regular, and symlink surfaces fail closed.
- **Breaking (publish as v5.0.0):** the repository-home action accepts an optional adoption
  record and verifies its full release/provenance chain before repository validation.

### Security

- Require every v5 release identity to be a GitHub-verified signed annotated tag that targets
  the exact protected-main source commit. Draft assembly, exact-tag qualification, protected
  publication, and policy synchronization independently repeat this connected check.
- Remove the subtree mirror's forced-tag path. Every nonempty mirror `tag` input now fails closed
  before branch rewriting until a separately protected target-release signer is qualified.

## Retired v4.0.0 draft (superseded; never published)

### Added

- Added the `reusable-nix-flake.yml` baseline with a locked, runner-selectable flake check.
- Added dedicated ARC canary, build, qualification-read, qualification-attest, promotion, and
  disaster-recovery evidence workflows with versioned machine contracts.
- Added exact digest, attestor occurrence, GitOps promotion, and immutable evidence outputs for
  the production artifact-authority path.

### Changed

- **Breaking:** replaced Buildkite artifact authority with private GKE-hosted GitHub Actions
  Runner Controller and six capability-specific workload identity providers.
- Required trusted-main callers, push-only execution, exact provider audiences, and immutable v4
  reusable-workflow identities for production artifact operations.

### Security

- Capability-prefixed federated subjects prevent cross-provider IAM subject collisions.
- Production promotion remains PR-only and the builder cannot issue qualification or deployment
  authority.

## v3.0.0

### Added

- Added `reusable-binauthz-sign.yml`, a protected-release workflow that requires distinct
  Buildkite build/provenance and qualification attestations before using a dedicated signer
  identity and immutable KMS key version to issue a third deployment attestation.

### Changed

- **Breaking:** removed Binary Authorization attestor/key inputs and signing from
  `reusable-oci-build.yml`. Publish this contract change as a new major release; do not move
  an existing release tag.

- Split cloud-federated planning from pull-request mutation so no plan job combines Google
  Cloud OIDC with repository write authority.
- Replaced concurrent Terragrunt `TF_PLUGIN_CACHE_DIR` use with Terragrunt's provider-cache
  server and current `terragrunt run` command form.
- Tightened reusable Terraform planning to read-only cloud and repository permissions; plan
  comments are published by a separate least-privilege job.
- Made Go module-tidiness checks support dependency-free modules without `go.sum`, corrected
  executable fixture modes, and rejected CodeQL's unsupported Go `none` build mode before init.
- Narrowed the supported Terraform line to `>= 1.15.0, < 1.16.0`.

### Security

- GitHub's general OCI builder is not a Mindclade production trust authority. Buildkite build
  and qualification identities cannot mint the deployment attestation accepted by production
  GKE, and caller-controlled inputs cannot select the signer identity, attestors, or KMS key.
- Required security policy rejects privileged pull-request jobs that combine `id-token: write`
  with repository mutation permissions.
- First-party consumers must pin the immutable `v3.0.0` release tag.

## v2.0.0

### Added

- Organization-ruleset workflow for dependency review and changed-workflow action-pin policy.
- GitHub-native SLSA build provenance and SBOM attestations for published OCI images.
- Linked-artifact storage records for published images.
- OIDC/WIF claim diagnostics including immutable organization/repository IDs,
  `job_workflow_ref`, `job_workflow_sha`, visibility, and selected repository properties.
- Versioned reusable-workflow API snapshots under `contracts/workflows/` with an offline
  drift checker.
- Enterprise guidance for immutable releases, ruleset workflows, custom OIDC properties, and
  GCP WIF trust conditions.
- Starter workflows for Go, Python/uv, and Terraform repositories pinned to `v2.0.0`.

### Changed

- Reset the first production workflow contract to `v2.0.0` and normalized all starter/docs
  references to the same immutable release.
- `reusable-oci-build.yml` now treats GitHub artifact attestations as canonical source-build
  provenance while keeping GCP Binary Authorization as the optional GKE admission control.
- `release.yml` assembles a draft release before publication, matching GitHub immutable-release
  best practice.
- CI uses actionlint 1.7.12 through a narrow Nix override while retaining the existing locked
  nixpkgs base.
- Organization profile content is removed from this internal repository; member profile
  content is maintained in `.github-private/profile/README.md`.

### Removed

- Legacy SLSA generator workflow and its third-party semver-pin exception.
- Public-Sigstore/cosign image/SBOM attestation path from the standard OCI workflow.
- Low-value `stale.yml` and OpenSSF Scorecard scheduled workflows.
- Staged profile/brand assets that did not belong in the internal `.github` control repository.

### Security

- Every third-party action reference is full-commit-SHA pinned.
- Required ruleset security runs centrally without executing untrusted repository code.
- WIF policy is designed around immutable `repository_owner_id`, exact released
  `job_workflow_ref`, private/internal visibility, and repository custom-property claims.
- No GCP service-account JSON credentials are accepted by the reusable cloud workflows.
