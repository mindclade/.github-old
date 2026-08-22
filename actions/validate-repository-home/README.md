# Validate a Mindclade repository home and common documents

This composite action validates the caller's checked-out `README.md` against
`contracts/repository.yaml` and the `repository-home@2` documentation contract. It checks the
MONO header, local badges and images, contract-table parity, primary-reader and first-success
routing, quick-start success/failure/safety labels, required paths, local links and anchors,
Mermaid estate diagram, version claims, and prose budget without network access or third-party
Python packages. The same action enforces `common-document@1`: the complete root policy set,
document markers, exact proprietary license, conduct, and legal-reliance digests,
repository-specific notice identity and attribution, contributor authorization, bounded
security safe harbor, support boundaries, one root license surface, and the exact optional
source-header template. It also requires a deterministic `THIRD_PARTY_NOTICES.md`, its reviewed
provenance contract, and byte-exact policy-bundle copies of the third-party notice validator and
SPDX proprietary-license enricher.

```yaml
steps:
  - uses: actions/checkout@<full-commit-sha>
    with:
      persist-credentials: false
  - uses: mindclade/.github/actions/validate-repository-home@<immutable-release-sha>
    with:
      adoption-record-path: contracts/policy-bundle/adoption.json
      local-validator-path: scripts/validate-repository-home.py
```

The action reads `$GITHUB_WORKSPACE`; it has no outputs, credentials, or write behavior. The
optional `local-validator-path` is relative to that workspace. When supplied, the action fails
unless the file exists inside the workspace and is byte-identical to the released validator.
This preserves an offline developer command without letting the mirror drift from CI authority.
After v5 publication, managed consumers also supply `adoption-record-path`. The record binds the
action's full commit SHA to the v5 tag, exact policy-manifest digest, bundle version, and released
validator digest. The action verifies the consumer manifest and optional offline mirror against
that record before it evaluates repository content. Omitting the record is supported only for
the canonical repository and staged pre-v5 migration; governed consumer activation requires it.

Composite actions use the full 40-character commit behind the immutable release, not its tag.
Until a release containing this action is published and qualified, estate repositories continue
to run the local validator from their existing fail-closed CI targets.

## Release rollout

After an operator publishes the release, obtain its commit with
`git rev-parse 'vX.Y.Z^{}'`, confirm the result is 40 characters and reachable from `origin/main`,
and update consumers through separate reviewed pull requests. Use
`scripts/validate-repository-home.py` as the mirror path in `.github-private`, `bootstrap`,
`infrastructure-live`, `github-config`, and `gitops`; the internal monorepo uses
`tools/docs/validate_repository_home.py`.

Keep each repository's explicit offline validation target. Where a CI job invokes that target
through an aggregate `make validate`, split the non-home checks into `validate-core`: local
`make validate` continues to include both targets, while CI runs this action followed by
`make validate-core`. This avoids executing the mirror after the released action has already
proved the repository home, common documents, repository contract, and byte parity.
