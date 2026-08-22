# Mindclade · `.github` production blueprint

**Repository class:** `enterprise-control`  
**Visibility:** `internal`  
**Default branch:** `main`

## Authoritative responsibilities

- `shared-workflows`
- `community-health`
- `workflow-contracts`

## Explicit exclusions

- `cloud-resources`
- `github-enterprise-desired-state`
- `kubernetes-desired-state`
- `application-source`

## Operating invariant

All changes are pull-request reviewed, subject to CODEOWNERS and required checks, merged through the configured queue for protected repositories, and performed by narrowly scoped identities. Live-system qualification evidence is separate from source completeness.
