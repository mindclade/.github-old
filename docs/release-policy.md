<!-- mindclade-doc: reference@1 -->

# Mindclade shared workflow release policy

> **Audience:** Reusable-workflow maintainers and consumer repository owners
> **Outcome:** Choose, qualify, publish, and adopt a workflow release without changing an
> existing immutable contract in place.

## Versioned surface

The compatibility surface is defined by `workflow_call` inputs, secrets, outputs, job IDs,
explicit permissions, defaults, and observable behavior. Machine-readable structural
snapshots live in `contracts/workflows/`; [Workflow contracts](WORKFLOW_CONTRACTS.md) explains
how to review and refresh them.

Use semantic versioning:

| Release | Use when |
| --- | --- |
| Patch | Behavior is corrected without breaking the caller contract |
| Minor | Backward-compatible capability is added, such as an optional input with a safe default |
| Major | A required input is added, an input/output/job is removed or renamed, a default is tightened, or caller permissions/behavior break compatibility |

## Required evidence

Before tagging, the release commit must have:

- a reviewed `CHANGELOG.md` entry;
- matching workflow-contract snapshots;
- passing `nix develop .#ci --command make validate`;
- a passing `smoke / verdict`; and
- passing repository-policy checks.

Cloud-dependent workflows additionally require qualification in an intentionally provisioned
project with the exact released identity boundary. They must not receive broad cloud access
merely so the generic smoke suite can run.

## Publish

Create an annotated full-semver tag on the reviewed commit:

```sh
release_sha="$(python3 -c 'import json,pathlib
print(json.loads(pathlib.Path("contracts/releases/vX.Y.Z.json").read_text())["source_commit"])')"
git merge-base --is-ancestor "${release_sha}" origin/main
git tag -a vX.Y.Z -m "Mindclade shared workflow contract vX.Y.Z" "${release_sha}"
git push origin vX.Y.Z
```

The commit operand is not optional. Without it the tag lands on the checkout, which after a
squash or rebase merge is a different commit than the one that was reviewed and attested.

`release.yml` validates the tag, changelog, and tracked release specification; creates a draft;
and attaches an exact source/file-digest manifest. It never publishes. After connected
qualification of that exact tag, an operator dispatches `publish-release.yml` with the immutable
evidence digest and protected change ticket. Publication first crosses the
`workflow-release-platform` environment and then the `workflow-release-security` environment;
each has one exact reviewer team and prevents self-review. This enforces two distinct protected
approval boundaries before organization immutable-release enforcement protects the release and
tag.

Never publish from an unreviewed local commit. Never move or reuse an existing release tag.

## Roll out to consumers

Reusable-workflow consumers pin the full version:

```yaml
jobs:
  ci:
    uses: mindclade/.github/.github/workflows/reusable-go-ci.yml@vX.Y.Z
```

Adoption is a consumer-side pull request with its own CI evidence. Renovate may propose the
bump; it does not bypass review. Roll out to representative lower-risk consumers before
control-plane or production-authority repositories when behavior changed materially.

Composite-action consumers use the full 40-character commit behind that release because the
organization requires SHA-pinned action references:

```sh
release_sha="$(git rev-parse 'vX.Y.Z^{}')"
test "${#release_sha}" -eq 40
```

```yaml
- uses: mindclade/.github/actions/validate-repository-home@<release-commit-sha> # vX.Y.Z
```

Never substitute the annotated-tag object ID, a branch SHA that has not been released, or a
mutable branch name.

## Correct a release

An immutable release is never repaired in place. Stop further rollout, document the issue,
publish a corrected patch (or the appropriate higher version), qualify it, and update affected
consumers. Existing consumers may pin their last known-good full version while the correction
is prepared.
