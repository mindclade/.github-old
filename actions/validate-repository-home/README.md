# Validate a Mindclade repository home

This no-input composite action validates the caller's checked-out `README.md` against
`contracts/repository.yaml` and the `repository-home@2` documentation contract. It checks the
MONO header, local badges and images, contract-table parity, required paths, local links and
anchors, Mermaid estate diagram, version claims, and prose budget without network access or
third-party Python packages.

```yaml
steps:
  - uses: actions/checkout@<full-commit-sha>
    with:
      persist-credentials: false
  - uses: mindclade/.github/actions/validate-repository-home@<immutable-release-sha>
```

The action reads `$GITHUB_WORKSPACE`; it has no inputs, outputs, credentials, or write behavior.
Until an immutable `.github` release containing the action is published and qualified, estate
repositories run the byte-identical validator copy from their local validation target.
