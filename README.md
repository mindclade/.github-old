# Mindclade `.github`

Organization-wide GitHub policy, community-health defaults, starter workflows, required
ruleset-workflow implementation, and reusable CI for Mindclade's GitHub Enterprise Cloud
organization.

> **Visibility contract:** this repository is intentionally **internal**. Do not make it
> public. `required-repository-policy.yml` verifies owner, default branch, visibility, lifecycle, and required Mindclade custom properties for every governed repository.
> branch and fails closed on drift.

## Position in the repository estate

```text
.github
    |
    | workflow implementations, templates, community health, contracts
    v
github-config
    |
    | rulesets, teams, repo settings, environments, Actions/OIDC governance
    v
+----------------------+----------------------+----------------------+
| bootstrap            | infrastructure-live  | gitops               |
+----------------------+----------------------+----------------------+
                         |
                         v
              mindclade-internal-monorepo
```

`.github` consumes policy and identity configuration; it does not provision GitHub or cloud
control planes. `github-config` owns GitHub desired state, `bootstrap` owns root durable cloud
trust, `infrastructure-live` owns normal GCP desired state and workload identities, and
`gitops` owns Kubernetes/Argo CD desired state.

## What belongs here

| Path | Responsibility |
|---|---|
| `.github/workflows/reusable-*.yml` | Versioned CI APIs for internal repositories |
| `.github/workflows/required-security-baseline.yml` | Language-neutral workflow attached by organization rulesets |
| `.github/workflows/{hygiene,smoke,required-repository-policy,pin-audit,release}.yml` | This repository's qualification/release automation |
| `workflow-templates/` | Organization starter workflows pinned to an immutable release |
| `contracts/workflows/` | Snapshots of reusable workflow API contracts |
| `.github/DISCUSSION_TEMPLATE/` | Shared design-proposal form where GitHub inheritance supports it |
| `.github/ISSUE_TEMPLATE/` and PR template | Maintenance UX for this repository; `github-config` distributes copies where inheritance does not apply |
| Root policy files | Community-health defaults |
| `docs/` | Enterprise setup, WIF trust contract, workflow-versioning contract |
| `testdata/` | Hermetic smoke-test fixtures |
| `tools/` | Offline validators and contract checks |

The canonical organization profile source lives in `profile/README.md`. This internal repository
remains the owner of that content even where GitHub Enterprise rendering behavior requires a
separate publication boundary in the future.

## Reusable workflow catalog

Consumers use immutable **full semver** releases. Do not call `@main`, a branch, or a moving
major tag.

```yaml
jobs:
  ci:
    uses: Mindclade/.github/.github/workflows/reusable-go-ci.yml@v3.0.0
    with:
      go-version: "1.25.12"
```

The doubled `.github/.github/` is correct: the first `.github` is the repository name and the
second is the directory inside it.

| Workflow | Contract |
|---|---|
| `reusable-go-ci.yml` | Go build/vet/lint/race/coverage |
| `reusable-uv-ci.yml` | Locked uv sync, Ruff, Pyright, pytest |
| `reusable-rust-ci.yml` | rustfmt, locked metadata, Clippy, tests, cargo-deny |
| `reusable-codeql.yml` | Matrix CodeQL analysis |
| `reusable-tf-plan.yml` | WIF auth, fmt/init/validate, TFLint, Checkov, non-retained plan review |
| `reusable-oci-build.yml` | Docker/Bazel OCI build, SBOM, GitHub SLSA provenance + SBOM attestations, linked-artifact record, optional BinAuthz |
| `reusable-wif-auth.yml` | OIDC-claim/WIF preflight; credentials intentionally do not escape its job |
| `reusable-repo-hygiene.yml` | Binary and repository-size budgets |
| `reusable-subtree-mirror.yml` | Controlled one-way subtree publication via GitHub App |

`required-security-baseline.yml` is different: `github-config` attaches it to organization/enterprise
rulesets so it runs without each consumer repository opting in. It performs dependency review
on pull requests and rejects newly changed workflow/action files that introduce mutable
third-party action references.

## Supply-chain model

- Third-party actions are pinned to full commit SHAs.
- Mindclade reusable workflow calls use immutable full-semver releases.
- GitHub Enterprise's organization policy should also require SHA pinning as defense in depth.
- OCI artifacts are addressed by digest.
- `actions/attest` is the canonical source-build provenance and SBOM attestation mechanism.
  Private/internal repositories use GitHub's private Sigstore instance.
- OCI attestations are pushed to the registry and recorded as GitHub linked artifacts.
- GKE admission remains a separate Binary Authorization decision when an attestor is supplied.
- Organization immutable releases lock published release tags/assets and automatically create
  release attestations.
- No GCP service-account JSON key is accepted. Cloud jobs use GitHub OIDC + GCP WIF.

A caller of a reusable workflow cannot let the callee elevate `GITHUB_TOKEN` permissions.
Cloud callers therefore grant the maximum permissions the called job needs at the caller job.
For example, Terraform plan callers grant `contents: read`, `id-token: write`, and (when PR
comments are enabled) `pull-requests: write`; OCI publication callers additionally grant
`attestations: write` and `artifact-metadata: write`.

## WIF model

`bootstrap` creates the root GitHub↔GCP trust anchor. `infrastructure-live` creates normal
workload-specific identities. `github-config` publishes provider/service-account identifiers,
repository custom properties, environments, and OIDC claim policy. These workflows consume
that trust.

GCP conditions should bind immutable `repository_owner_id`, private/internal visibility,
`job_workflow_ref` for the approved released workflow, and repository custom-property claims
such as `cloud_access`. See [`docs/WIF.md`](docs/WIF.md).

## Workflow contracts

Reusable workflows are versioned APIs. `tools/check_workflow_contracts.py` snapshots their
inputs, secrets, outputs, job IDs, and explicit permission surfaces. An implementation-only
change does not alter a snapshot; an API change does.

```sh
python3 tools/check_workflow_contracts.py
```

When an intentional major-version contract change is approved:

```sh
python3 tools/check_workflow_contracts.py --update
```

Review the resulting JSON diff like an API schema migration. See
[`docs/WORKFLOW_CONTRACTS.md`](docs/WORKFLOW_CONTRACTS.md).

## Development and qualification

```sh
nix develop .#ci --command actionlint -color
nix develop .#ci --command yamllint --strict .
python3 tools/check_workflow_contracts.py
python3 tools/validate_repo.py
```

`hygiene.yml` runs the same structural checks. `smoke.yml` executes the hermetic Go, Python,
Rust, CodeQL, and hygiene reusable workflows against fixtures. Cloud-dependent WIF/Terraform/
OCI paths require an intentionally provisioned qualification project and are not granted a
cloud identity by default.

## Release model

Merging a reusable-workflow change reaches no consumer until a new immutable release is
published and a consumer updates its `uses:` reference.

1. Update `CHANGELOG.md` and preserve or intentionally version the workflow contract.
2. Require `hygiene`, `smoke`, and `required-repository-policy` to pass.
3. Create an annotated full-semver tag, beginning with `v3.0.0` for this production contract.
4. `release.yml` assembles a draft release and publishes it only after validation.
5. Organization immutable-release enforcement locks the tag/assets and produces the GitHub
   release attestation.
6. Renovate can open consumer bumps; each rollout remains reviewable.

Never move an existing release tag. Correct a bad release with a new patch version.

See [`docs/ENTERPRISE_SETUP.md`](docs/ENTERPRISE_SETUP.md) before the initial push/release.
