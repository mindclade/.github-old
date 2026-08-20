# GitHub OIDC and Google Cloud WIF contract

This document defines the trust boundary consumed by `Mindclade/.github`. The root trust
anchor is provisioned in `bootstrap`; normal workload identities live in
`infrastructure-live`; GitHub-side variables/properties/policy live in `github-config`.

## Ownership

| Repository | WIF responsibility |
|---|---|
| `bootstrap` | Root Workload Identity Pool/provider, bootstrap/recovery identity, minimum durable IAM needed to avoid circular dependency |
| `infrastructure-live` | Normal plan/apply, artifact-publisher, deployment and other workload service accounts/IAM |
| `github-config` | Actions policy, environments, variables, immutable GitHub organization ID, repository custom properties, OIDC property inclusion |
| `.github` | Authenticate inside each cloud job and provide a WIF preflight/diagnostic workflow |

No repository stores a long-lived GCP service-account JSON key.

## GitHub claims to map

Map the minimum claims needed for policy decisions from the GitHub OIDC assertion into the
GCP provider. A representative Terraform shape is:

```hcl
attribute_mapping = {
  "google.subject"                  = "assertion.sub"
  "attribute.repository"            = "assertion.repository"
  "attribute.repository_id"         = "assertion.repository_id"
  "attribute.repository_owner_id"   = "assertion.repository_owner_id"
  "attribute.repository_visibility" = "assertion.repository_visibility"
  "attribute.job_workflow_ref"      = "assertion.job_workflow_ref"
  "attribute.job_workflow_sha"      = "assertion.job_workflow_sha"
  "attribute.cloud_access"          = "assertion.repo_property_cloud_access"
  "attribute.deployment_tier"       = "assertion.repo_property_deployment_tier"
  "attribute.workload_class"        = "assertion.repo_property_workload_class"
}
```

`github-config` must configure `cloud_access`, `deployment_tier`, and `workload_class` as
organization/enterprise repository custom properties and include those properties in Actions
OIDC tokens before GCP conditions depend on them.

## Trust conditions

Prefer immutable IDs and the called reusable workflow over mutable names. For example, the
Terraform-plan provider should conceptually require all of the following:

```text
repository_owner_id == <immutable Mindclade organization ID>
repository_visibility is internal or private
job_workflow_ref == Mindclade/.github/.github/workflows/reusable-tf-plan.yml@refs/tags/v3.0.0
cloud_access == enabled
workload_class == infrastructure
```

Use an equivalent CEL expression in the GCP Workload Identity Provider, for example:

```hcl
attribute_condition = join(" && ", [
  format("assertion.repository_owner_id == '%s'", var.mindclade_github_org_id),
  "(assertion.repository_visibility == 'internal' || assertion.repository_visibility == 'private')",
  "assertion.job_workflow_ref == 'Mindclade/.github/.github/workflows/reusable-tf-plan.yml@refs/tags/v3.0.0'",
  "assertion.repo_property_cloud_access == 'enabled'",
  "assertion.repo_property_workload_class == 'infrastructure'",
])
```

The snippet is a policy contract, not a module copied into this repository. `bootstrap` /
`infrastructure-live` own the concrete provider resources and substitute the immutable
organization ID. Because `v3.0.0` is protected by GitHub immutable releases/tag policy, the
workflow ref is a stable trust anchor. `job_workflow_sha` is still mapped for audit evidence
and may be bound as an additional control where automatic IAM updates are acceptable.

For production deployment identities, additionally bind a protected GitHub environment and
an appropriate `deployment_tier` repository property. Plan/read-only identities should be
separate from apply/deployment identities.

## Runtime rules

Every job that calls GCP authenticates in that same job:

```yaml
permissions:
  contents: read
  id-token: write

steps:
  - uses: google-github-actions/auth@<full-commit-sha>
    with:
      workload_identity_provider: ${{ vars.WIF_PROVIDER_PLAN }}
      service_account: ${{ vars.SA_TF_PLAN }}
```

A reusable preflight cannot authenticate a different caller job: credentials and generated
files are runner-local and disappear when the called job ends. `reusable-wif-auth.yml` is
therefore diagnostic only. It safely reports selected OIDC claims, optionally validates the
immutable owner ID, performs federation, and verifies that GCP accepts an access token.

## Recommended GitHub properties

Use a small typed vocabulary in `github-config`:

| Property | Example values | Purpose |
|---|---|---|
| `cloud_access` | `disabled`, `enabled` | Coarse ability to receive any cloud identity |
| `workload_class` | `application`, `infrastructure`, `release`, `gitops` | Selects allowed identity family |
| `deployment_tier` | `none`, `dev`, `staging`, `production` | Narrows environment-sensitive roles |

Do not encode secrets, service-account emails, project IDs, or authorization grants in custom
properties. They are policy labels, not a credential store.

## Qualification

Before enabling a new identity, invoke `reusable-wif-auth.yml` with the exact provider and
service account the workload will use. Pass the immutable GitHub organization ID from an
organization variable when available. Verify that the summary shows the expected repository,
visibility, reusable workflow ref/SHA, and repository-property claims.
