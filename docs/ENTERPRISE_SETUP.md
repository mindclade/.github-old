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
- generate an SPDX JSON SBOM;
- generate GitHub SLSA build provenance with `actions/attest`;
- generate a GitHub SBOM attestation;
- push the attestations to the OCI registry;
- create a GitHub linked-artifact storage record using `artifact-metadata: write`.

Private/internal artifact attestations use GitHub's private Sigstore instance; no public Rekor
publication path is required. The builder cannot issue a Binary Authorization deployment
attestation.

This general-purpose workflow is not Mindclade's production artifact authority. Buildkite
performs the authoritative production build and qualification and issues two distinct Binary
Authorization evidence roots for the immutable digest.

After both Buildkite build/provenance and qualification attestations exist,
`reusable-binauthz-sign.yml` may create the separately named GKE admission attestation. It:

- accepts only the digest from the caller;
- obtains identity, attestors, and KMS key version from governance-managed variables;
- runs behind the caller repository's protected `release` environment;
- verifies the distinct Buildkite build/provenance and qualification attestors;
- authenticates as a dedicated signer service account; and
- creates or verifies the deployment attestation idempotently.

Bind the signer service account's WIF grant to the exact released `job_workflow_ref`, the
monorepo's immutable repository identifiers, and the `release` environment subject. Do not
grant either Buildkite evidence identity access to the signer key or deployment attestor.
The three governed roots use explicit `BINAUTHZ_BUILD_*`, `BINAUTHZ_QUALIFICATION_*`, and
`BINAUTHZ_DEPLOYMENT_*` variables; do not reuse an attestor across roles.

## 8. OIDC/WIF governance

`bootstrap` owns root WIF trust. `infrastructure-live` owns normal workload identities.
`github-config` owns the GitHub-side policy/metadata consumed by those trust conditions.

Define repository custom properties such as:

- `cloud_access`: `disabled` / `enabled`
- `workload_class`: `application` / `infrastructure` / `release` / `gitops`
- `deployment_tier`: `none` / `dev` / `staging` / `production`

Configure these properties for inclusion in GitHub Actions OIDC tokens. GCP trust should bind:

- immutable `repository_owner_id` rather than only the `Mindclade` string;
- repository visibility (`internal` or `private`);
- exact approved `job_workflow_ref` at an immutable release ref;
- relevant repository custom-property claims;
- protected environment for apply/deploy identities where applicable.

Map `job_workflow_sha` for evidence and optional stricter binding. Keep plan/read-only,
apply/deployment, artifact-publisher, and bootstrap/recovery identities separate.

See [`WIF.md`](WIF.md) for the concrete claim contract.

## 9. Organization variables and secrets

Publish only identity references and non-secret configuration as variables, for example:

- `MINDCLADE_GITHUB_ORG_ID`
- `WIF_PROVIDER_PLAN`
- `SA_TF_PLAN`
- `WIF_PROVIDER_SIGNER` and `SA_ARTIFACT_SIGNER`
- qualification and deployment attestor projects/names plus an immutable KMS key version
- environment-specific Artifact Registry and Binary Authorization identifiers

The optional consumer-pin audit uses a GitHub App:

- repository variable `PIN_AUDIT_APP_ID`;
- repository secret `PIN_AUDIT_APP_KEY`;
- installation permissions limited to organization repository metadata/contents read plus
  issues write on this repository.

When those values are absent, the optional audit skips cleanly.

Never store a GCP service-account key.

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

## 11. Initial production release

From a clean checkout:

```sh
python3 tools/check_workflow_contracts.py
python3 tools/validate_repo.py
nix develop .#ci --command actionlint -color
nix develop .#ci --command yamllint --strict .
```

Push `main`, enable rulesets/immutable releases, let repository workflows pass, then create the
first production contract:

```sh
git tag -a v3.0.0 -m "Mindclade GitHub Enterprise workflow foundation v3"
git push origin v3.0.0
```

Starter workflows intentionally reference `v3.0.0`; they become usable after this release.
Do not create the tag before `main` protection and organization immutable-release enforcement
are active.

## 12. Operational prerequisites

Before relying on organization defaults, verify monitored aliases route to restricted groups:
`security@mindclade.com`, `biosecurity@mindclade.com`, and `conduct@mindclade.com`.

Enable private vulnerability reporting, secret scanning/push protection, dependency graph and
dependency review, code scanning, artifact attestations, and other GitHub security controls
according to repository risk and enterprise license coverage.
