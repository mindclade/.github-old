# GitHub Actions security model

## Invariants

- The organization default `GITHUB_TOKEN` permission is read-only.
- Privileged jobs declare only the permissions they need.
- External actions are pinned to full commit SHAs.
- Mindclade reusable workflows are consumed through immutable full-semver tags.
- Cloud access uses GitHub OIDC and service-account impersonation; no service-account JSON keys.
- Pull requests from untrusted sources never receive privileged secrets or production identity.
- Build, qualification, signing, promotion, infrastructure apply, and runtime identities are distinct.
- Apply workflows live in the repository that owns the affected desired state.

## Workflow release order

1. Merge and qualify `.github`.
2. Create an immutable full-semver tag.
3. Update `github-config` ruleset-workflow references.
4. Let Renovate update consumers.
5. Audit stale consumers with `pin-audit.yml`.

Never move or recreate an existing release tag.
