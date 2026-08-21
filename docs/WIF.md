# GitHub OIDC and Google Cloud WIF contract

This document defines the trust boundary consumed by `mindclade/.github`. The root trust
anchor is provisioned in `bootstrap`; normal workload identities live in
`infrastructure-live`; GitHub-side variables/properties/policy live in `github-config`.

## Ownership

| Repository | WIF responsibility |
|---|---|
| `bootstrap` | Root Workload Identity Pool/provider, bootstrap/recovery identity, minimum durable IAM needed to avoid circular dependency |
| `infrastructure-live` | Normal plan/apply, artifact-publisher, deployment and other workload service accounts/IAM |
| `github-config` | Actions policy, environments, variables, immutable GitHub organization/repository IDs, and GitHub OIDC subject mode |
| `.github` | Authenticate inside each cloud job and provide a WIF preflight/diagnostic workflow |

No repository stores a long-lived GCP service-account JSON key.

## GitHub claims to map

Map only claims that exist on every job through the repository-local providers. The concrete
bootstrap mapping is equivalent to:

```hcl
attribute_mapping = {
  "google.subject"                  = "assertion.sub"
  "attribute.repository"            = "assertion.repository"
  "attribute.repository_id"         = "assertion.repository_id"
  "attribute.repository_owner_id"   = "assertion.repository_owner_id"
  "attribute.ref"                   = "assertion.ref"
  "attribute.workflow_ref"          = "assertion.workflow_ref"
  "attribute.workflow_sha"          = "assertion.workflow_sha"
  "attribute.event_name"            = "assertion.event_name"
}
```

`job_workflow_ref` and `job_workflow_sha` exist only for jobs executing a called reusable
workflow. Map them on the six dedicated ARC release providers, each of which requires one exact
immutable v4 reusable workflow. Do not map them on direct-workflow providers; doing so can make
otherwise valid direct-job tokens fail evaluation.

Mindclade does not currently authorize GCP access from repository custom-property claims.
`github-config` custom properties classify and target governance policy; they are not cloud
credentials and are not included in the active OIDC subject template.

## Immutable default subject

The active contract keeps every managed repository on GitHub's default subject and requires
the immutable ID-bearing form introduced for repositories created, renamed, or transferred
after 2026-07-15:

```text
repo:OWNER@OWNER-ID/REPO@REPO-ID:environment:ENVIRONMENT-NAME
```

Older repositories must be explicitly opted into immutable default subjects before bootstrap
WIF is activated. A legacy name-only subject is deliberately rejected. Resetting a repository
to `use_default = true` removes a custom template; by itself it does not prove that a
pre-cutover repository uses the immutable default.

## Trust conditions

Prefer immutable IDs, an explicit provider audience, and the narrowest workflow/environment
identity. A direct Terraform plan path conceptually requires all of the following:

```text
repository_owner_id == <immutable Mindclade organization ID>
repository_id == <immutable repository ID>
repository == mindclade/<repository>
aud == <exact provider audience>
sub == repo:mindclade@<owner-id>/<repository>@<repository-id>:environment:plan
```

Use equivalent CEL in the repository-specific GCP Workload Identity Provider, for example:

```hcl
attribute_condition = join(" && ", [
  format("assertion.repository_owner_id == '%s'", var.mindclade_github_org_id),
  format("assertion.repository_id == '%s'", var.repository_id),
  format("assertion.repository == 'mindclade/%s'", var.repository),
  format("assertion.aud == '%s'", var.provider_audience),
  format(
    "assertion.sub == 'repo:mindclade@%s/%s@%s:environment:plan'",
    var.mindclade_github_org_id,
    var.repository,
    var.repository_id,
  ),
])
```

The snippet is a policy contract, not a module copied into this repository. `bootstrap` /
`infrastructure-live` own the concrete provider resources and substitute the immutable
organization and repository IDs. Service-account bindings further narrow direct apply and
scheduled read paths to an exact `workflow_ref` on `refs/heads/main`.

The proposed ARC lane remains quarantined until its coordinated v4 release. Its capability
providers, reusable-workflow identities, and protected-environment subjects are design inputs,
not active trust. Publish and protect an independently qualified v4 release before introducing
or activating any of those providers; never bind cloud IAM to unpublished workflow source.

For production deployment identities, additionally bind a protected GitHub environment.
Plan/read-only identities remain separate from apply/deployment identities.

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

## Repository governance properties

`github-config` uses typed `mindclade_*` properties for ruleset selection and governance:

| Property | Example values | Purpose |
|---|---|---|
| `mindclade_repository_class` | `enterprise-control`, `production-control` | Selects governance/ruleset class |
| `mindclade_owner_team` | `platform`, `infrastructure`, `security` | Records accountable owner |
| `mindclade_production_authority` | `true`, `false` | Classifies production control-plane authority |
| `mindclade_ci_profile` | `terraform-control`, `gitops-control` | Selects the required CI profile |

Do not encode secrets, service-account emails, project IDs, or authorization grants in these
properties. They are policy labels, not a credential store or an active WIF input.

## Qualification

Before enabling the ARC lane, run the zero-data-authority `reusable-arc-wif-canary.yml` from one
new reviewed request on protected main. Then negatively test every provider with the wrong
capability, branch, caller, event, repository, audience, and reusable-workflow ref. Verify the
expected immutable owner/repository IDs, ID-bearing subject, audience, workflow/ref, and exact
reusable workflow ref/SHA for every capability. Generic `reusable-wif-auth.yml` remains useful
for non-ARC identities but cannot substitute for these cross-capability denial tests.
