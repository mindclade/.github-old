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

For v5, `contracts/releases/v5.0.0.json` schema 2 declares every reusable workflow and
contract, both organization-required workflows, the complete repository-home action, release
tools, policy tools, and the policy-manifest directory. Release assembly recursively hashes
every tracked regular file in those surfaces and rejects missing, duplicate, undeclared,
symlink, or non-regular entries.

Cloud-dependent workflows additionally require qualification in an intentionally provisioned
project with the exact released identity boundary. They must not receive broad cloud access
merely so the generic smoke suite can run.

## Publish

First verify that `github-config` has applied both organization tag rules: the no-bypass
`tag-protection` rule and the separate `release-tag-creation` rule whose only always-bypass
actor is the Release team. The operator's signing key must be registered with GitHub as a
signing key. Before creating a tag, dispatch `release-governance-preflight.yml` from protected
`main`. Its no-write job binds the checkout to the current protected-main head and proves the
same connected environment, reviewer, Release-team, and tag-rule inventory used by draft and
publication. A Release-team operator then creates a signed annotated full-semver tag on the
reviewed commit:

```sh
release_sha="<reviewed-merged-commit-sha>"
test "$(printf '%s' "${release_sha}" | wc -c | tr -d ' ')" -eq 40
git merge-base --is-ancestor "${release_sha}" origin/main
git show "${release_sha}:contracts/releases/vX.Y.Z.json" >/dev/null
git tag -s vX.Y.Z -m "Mindclade shared workflow contract vX.Y.Z" "${release_sha}"
git verify-tag vX.Y.Z
git push origin vX.Y.Z
```

The creation bypass belongs only to the separate creation rule. Never add it to
`tag-protection`: Release may mint a new identity, but nobody may move or delete one. A tag by
itself assembles only a draft; managed policy synchronization additionally requires a published,
non-prerelease, GitHub-immutable release and the exact source attestation.

The commit operand is not optional. Without it the tag lands on the checkout, which after a
squash or rebase merge is a different commit than the one that was reviewed and attested.

`release.yml` first uses the read-only repository API to prove both release environments have
their exact distinct reviewer teams, protected-main-only deployment policy, self-review and
administrator bypass disabled, and that the active organization `release-tag-creation` rule has
only the Release-team creation bypass. It then asks GitHub's read-only Git Data API to confirm
that the annotated tag is validly signed and targets the expected commit, validates the changelog
and tracked release specification, creates a draft, and attaches an exact source/file-digest
manifest. It never publishes. Exact-tag qualification, protected publication, and policy
synchronization repeat the connected signature/target check instead of relying only on the local
checkout. After qualification of that exact tag, an operator dispatches `publish-release.yml`
from protected `main` with the immutable evidence digest and protected change ticket. A no-write
authorization job proves the dispatch workflow, checkout SHA, and current `origin/main` are the
same commit and repeats the connected governance preflight. Publication then crosses the
`workflow-release-platform` environment and then the `workflow-release-security` environment;
each has one exact reviewer team and prevents self-review. This enforces two distinct protected
approval boundaries before organization immutable-release enforcement protects the release and
tag.

The preflight uses only the workflow's read-scoped `GITHUB_TOKEN` plus source-managed,
non-secret `RELEASE_TEAM_ID`; it never receives an organization-administration App token. GitHub
may omit ruleset bypass actors from a response that cannot prove them. An omitted bypass inventory
is an intentional hard failure, not permission to assume the catalog was applied. Keep publication
blocked until the connected response exposes the one exact Release-team bypass; do not widen this
workflow's token merely to turn the check green.

The version heading in `CHANGELOG.md` must be exactly `## vX.Y.Z` and its section must contain
non-whitespace release notes. Draft assembly rejects a planned-status suffix or empty section so
the published release cannot silently contain only the standard consumer-pinning footer.

The already-published historical `v3.0.0` tag is unsigned legacy evidence. Its immutable tag and
release are preserved, but it may never be moved, republished, or used as precedent for a new
unsigned release. All v5 and later release paths fail closed on an unverified tag object.

Never publish from an unreviewed local commit. Never move or reuse an existing release tag.
The historical v4 source record is retained under `contracts/releases/retired/` with
`superseded-unpublished` status. It is not a publishable release specification, and no v4 tag
or release may be created from it.

## Subtree target releases

`reusable-subtree-mirror.yml` retains intentional force authority only for the target branch,
whose history is a replaceable one-way projection. Its App does not hold a signing key, so every
nonempty `tag` input now fails closed before the mirror branch is rewritten. A separately
protected target-release workflow must eventually bind the exact source repository, source
commit, subtree path, split commit, workflow ref, and workflow SHA into a signed annotated tag;
that design and connected negative tests must qualify before target version creation is enabled.

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
Managed consumers also receive `contracts/policy-bundle/adoption.json`; it binds the policy
bundle and local validator to the exact v5 release commit. The repository-home action verifies
that record before evaluating content.

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
