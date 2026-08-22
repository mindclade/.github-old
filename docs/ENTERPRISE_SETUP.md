# GitHub Enterprise setup

This is the deployment contract for [`mindclade/.github`](https://github.com/mindclade/.github).
The owning [enterprise](https://github.com/enterprises/mindclade),
[organization](https://github.com/mindclade), and
[repository index](https://github.com/orgs/mindclade/repositories) use the canonical
`mindclade` slug. Apply organization/repository
settings through `mindclade/github-config`; use the UI only for controls the provider/API
cannot manage, and record those exceptions in the same desired-state repository.

## 1. Repository identity

- Owner: `mindclade`
- Name: `.github`
- Visibility: **internal**
- Default branch: `main`
- Forking: disabled unless a documented enterprise policy requires it
- Actions access: internal/private Mindclade repositories may call reusable workflows here
- Member-only organization profile source: `mindclade/.github-private/profile/README.md`;
  keep `.github-private` private and authoritative

`required-repository-policy.yml` checks repository owner, default branch, class-compatible visibility, lifecycle, production authority, and required Mindclade custom properties on governed changes
to `main`.

## 2. Required teams

Create and maintain these organization teams before CODEOWNERS enforcement:

- `@mindclade/platform`
- `@mindclade/security`

Both need read access. Grant higher repository roles only through declared GitHub desired state.
Security-sensitive workflow, identity, provenance, and policy paths require security review.

## 3. Default-branch and tag rulesets

For this repository's `main` branch require:

- pull requests; no direct pushes;
- code-owner review and resolved conversations;
- `hygiene / actionlint + yamllint`;
- `hygiene / offline validation`;
- `smoke / verdict`;
- `required-repository-policy / verify`;
- signed commits and linear history where compatible with the selected merge method;
- merge queue when adopted for this repository;
- force pushes and branch deletion blocked;
- bypass restricted to a time-bounded break-glass role with audit evidence.

Protect tags matching `v*`: only annotated full-semver `vX.Y.Z` release tags are allowed and
tag update/deletion is blocked. Tag rules protect creation/update before release publication;
organization immutable-release enforcement protects the published release/tag afterward.

## 4. Organization ruleset workflow

Use `.github/workflows/required-security-baseline.yml` as an organization or enterprise **required
workflow** ruleset for protected default branches of internal/private repositories. The file
uses only supported ruleset triggers (`pull_request` and `merge_group`) and is deliberately
language-neutral.

It enforces:

1. GitHub dependency review for pull requests, failing on newly introduced high/critical
   vulnerable dependencies.
2. Full commit-SHA pinning for new/changed third-party action references. Calls to released
   `mindclade/.github` reusable workflows may use immutable full semver.
3. A stable `verdict` job so internal workflow details can evolve without ruleset churn.

Roll the ruleset out in **Evaluate** mode first, inspect results across representative Go,
Python, Rust, Terraform, GitOps, and monorepo repositories, then promote to **Active**. Do not
apply the required-workflow rule to every branch; target protected branches whose updates are
performed through pull requests.

Language-specific CI remains opt-in through reusable workflows or repository-specific policy.
Do not force Go/Python/Rust/Terraform jobs onto repositories that do not contain those stacks.

## 5. Actions security

At the enterprise/organization level:

- allow GitHub-authored plus an explicit third-party allowlist;
- require action references to be pinned to a full commit SHA where the platform supports it;
- default `GITHUB_TOKEN` permissions to read-only;
- block self-hosted runners from untrusted pull-request code;
- allow internal/private repositories to call `mindclade/.github` workflows;
- retain logs/artifacts according to evidence-retention policy;
- manage allowed actions centrally rather than allowing repository-local exceptions by
  default.

The repository validator repeats SHA-pin enforcement as defense in depth. There are no
semver-tag exceptions for third-party actions.

Reusable workflow permissions can only stay the same or be reduced through a call chain; a
called workflow cannot elevate beyond the caller. Consumer workflows must therefore grant the
job permissions required by cloud/provenance workflows (`id-token: write`, and for OCI
attestation `attestations: write` / `artifact-metadata: write`, plus only the repository scopes
the job actually needs).

## 6. Immutable releases

Set the organization immutable-releases policy to **all repositories** unless a separately
approved exception policy requires selected repositories. At minimum it must cover `.github`
and every repository publishing versioned artifacts.

Immutable release publication:

1. `release.yml` validates the annotated semver tag and changelog.
2. It creates a GitHub Release as a draft.
3. It publishes the completed draft.
4. GitHub immutable-release enforcement locks the tag/assets and automatically creates the
   release attestation.

Never move/reuse an immutable release tag. Publish a new patch release for corrections.

## 7. Artifact provenance and linked artifacts

For general GitHub container publication, `reusable-oci-build.yml` provides:

- build and push by digest;
- generate an SPDX 2.3 JSON SBOM with the complete extracted
  `LicenseRef-Mindclade-Proprietary` and a digest-bound first-party package;
- fail if any third-party SBOM package lacks reviewed notice metadata;
- generate GitHub SLSA build provenance with `actions/attest`;
- generate a GitHub SBOM attestation;
- push the attestations to the OCI registry;
- create a GitHub linked-artifact storage record using `artifact-metadata: write`.

Before adopting the workflow release, synchronize policy bundle `2026.08.21.3` into the caller.
The caller must carry the exact bundle manifest, complete root `LICENSE`, reviewed
`contracts/third-party-materials.json`, generated `THIRD_PARTY_NOTICES.md`, and both distributed
SBOM/notice tools. A package that is not first-party and lacks reviewed notice metadata stops the
build before its SBOM can be uploaded or attested.

Private/internal artifact attestations use GitHub's private Sigstore instance; no public Rekor
publication path is required. The builder cannot issue a Binary Authorization deployment
attestation.

This general-purpose workflow is not Mindclade's production artifact authority. Dedicated ARC
workflows on the isolated private CI cluster perform the authoritative production build and
qualification and issue two distinct Binary Authorization evidence roots for the immutable digest.

After both ARC build/provenance and qualification attestations exist,
`reusable-binauthz-sign.yml` may create the separately named GKE admission attestation. It:

- accepts only the digest from the caller;
- obtains identity, attestors, and KMS key version from governance-managed variables;
- runs behind the caller repository's protected `release` environment;
- cryptographically validates the distinct ARC build/provenance and qualification
  occurrences against their attestors (list results alone are not trusted);
- authenticates as a dedicated signer service account; and
- creates or verifies the deployment attestation idempotently.

Google Cloud CLI 580.0.0 still exposes KMS `sign-and-create` in the beta track. The workflow
pins that CLI version and passes `--validate`; re-qualify the command before every CLI upgrade
or before switching to a future stable-track spelling.

Bind the signer service account's WIF grant to the exact released `job_workflow_ref`, the
monorepo's immutable repository identifiers, and the `release` environment subject. Do not
grant either ARC evidence identity access to the signer key or deployment attestor.
Grant the signer `roles/binaryauthorization.attestorsVerifier`, not the list-only
`attestorsViewer`, on the three attestor projects.
The three governed roots use explicit `BINAUTHZ_BUILD_*`, `BINAUTHZ_QUALIFICATION_*`, and
`BINAUTHZ_DEPLOYMENT_*` variables; do not reuse an attestor across roles.

## 8. OIDC/WIF governance

`bootstrap` owns root WIF trust. `infrastructure-live` owns normal workload identities.
`github-config` owns the GitHub-side policy/metadata consumed by those trust conditions.

Define repository governance properties such as:

- `mindclade_repository_class`: `enterprise-control` / `production-control` / `source-monorepo`
- `mindclade_owner_team`: `platform` / `infrastructure` / `security` / domain teams
- `mindclade_production_authority`: `true` / `false`
- `mindclade_ci_profile`: `terraform-control` / `terragrunt-control` / `gitops-control`

Use them for catalog validation and ruleset targeting; they are not active cloud-authority
claims. Keep managed repositories on GitHub's immutable default OIDC subject. GCP trust binds:

- the ID-bearing immutable default `sub` with owner and repository IDs;
- separately mapped immutable `repository_owner_id` and `repository_id`;
- the exact repository and provider audience;
- exact direct `workflow_ref`/ref bindings for repository-local jobs;
- exact approved `job_workflow_ref` at an immutable release ref for the dedicated signer only;
- protected environment for apply/deploy identities where applicable.

Map `job_workflow_ref`/`job_workflow_sha` only on providers dedicated to reusable-workflow
jobs; direct jobs do not carry those optional claims. Keep plan/read-only, apply/deployment,
artifact-publisher, and bootstrap/recovery identities separate.

See [`WIF.md`](WIF.md) for the concrete claim contract.

## 9. Organization variables and secrets

Publish only identity references and non-secret configuration as variables, for example:

- `MINDCLADE_GITHUB_ORG_ID`
- `WIF_PROVIDER_PLAN`
- `SA_TF_PLAN`
- `WIF_PROVIDER_SIGNER` and `SA_ARTIFACT_SIGNER`
- `WIF_PROVIDER_ARC_CANARY` and `SA_ARC_CANARY`
- `WIF_PROVIDER_ARC_BUILDER` and `SA_ARTIFACT_BUILDER`
- `WIF_PROVIDER_ARC_QUALIFICATION_READER` and `SA_ARTIFACT_QUALIFICATION_READER`
- `WIF_PROVIDER_ARC_QUALIFIER` and `SA_ARTIFACT_QUALIFIER`
- `WIF_PROVIDER_ARC_PROMOTER` and `SA_ARTIFACT_PROMOTER`
- qualification and deployment attestor projects/names plus an immutable KMS key version
- environment-specific Artifact Registry and Binary Authorization identifiers

The optional consumer-pin audit uses a GitHub App:

- repository variable `PIN_AUDIT_APP_ID`;
- repository secret `PIN_AUDIT_APP_KEY`;
- installation permissions limited to organization repository metadata/contents read plus
  issues write on this repository.

When those values are absent, the optional audit skips cleanly.

Never store a GCP service-account key.

Create runner group `mindclade-arc-artifact-authority` as selected/private, allow only
`mindclade-internal-monorepo`, and restrict it to
`mindclade/mindclade-internal-monorepo/.github/workflows/release.yml@refs/heads/main`. Install
the `mindclade-arc` GitHub App only on that repository with organization self-hosted-runners
write and repository Actions/metadata read. Install `mindclade-release-promoter` only on
`gitops` with contents and pull-requests write plus metadata read. These installations are
connected controls and must be verified against `github-config` before enabling WIF.

## 10. Inheritance boundaries

An internal `.github` repository can provide supported organization community-health defaults
and internal workflow/template components. Issue/PR template inheritance has stricter public
repository requirements, so `github-config` should provision repository-local copies where
needed rather than making this repository public.

The member organization profile is a separate GitHub publication boundary. Keep
`mindclade/.github-private` private with its rendered source at `profile/README.md`; do not
duplicate the profile body in this repository.

`CODEOWNERS`, rulesets, environments, variables, secrets, repository custom properties, and
required checks do not inherit from this repository; `github-config` owns them.

## 11. Deferred v4 production release

From a clean checkout:

```sh
python3 tools/check_workflow_contracts.py
python3 tools/validate_repo.py
nix develop .#ci --command actionlint -color
nix develop .#ci --command yamllint --strict .
```

The v4 production contract is not published. Starter workflows and active policy remain pinned
to `v3.0.0`. A separate coordinated release PR must record evidence for the final protected-main
commit before an authorized operator creates any v4 tag. Follow
[Workflow release bootstrap](workflow-release-bootstrap.md); never use an intermediate branch
commit as release evidence.

## 12. Operational prerequisites

Before relying on organization defaults, verify monitored aliases route to restricted groups:
`security@mindclade.com`, `biosecurity@mindclade.com`, and `conduct@mindclade.com`.

Enable private vulnerability reporting, secret scanning/push protection, dependency graph and
dependency review, code scanning, artifact attestations, and other GitHub security controls
according to repository risk and enterprise license coverage.
