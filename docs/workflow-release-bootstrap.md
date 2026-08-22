<!-- mindclade-doc: how-to@1 -->

# Publish the consolidated v5 shared workflow contract

> **Audience:** Platform and security maintainers
> **Outcome:** A future, coordinated review publishes the ARC workflow contract as an immutable
> release that downstream repositories may adopt.
> **Risk:** Critical—downstream CI and cloud trust may bind the released workflow identity.

> **Current status:** Source candidate only. The restored v4 manifest qualifies its historical
> protected-main source but does not create or authorize a tag. Publish and qualify v4 first for
> consumers whose WIF contracts require it. `contracts/releases/v5.0.0.json` then defines the
> consolidated successor; no v5 tag or release exists.

## Before you begin

- `main` is protected by the required checks listed in [Enterprise setup](ENTERPRISE_SETUP.md).
- Tags matching `v*` are protected and organization immutable releases are enabled.
- `CHANGELOG.md` describes the final proposed v5 contract.
- Starter workflows and active WIF policy references still use the published `v3.0.0` contract.
- `platform` and `security` reviewers have approved the release commit.
- The Release operator's signing key is registered with GitHub as a signing key.

## Qualify the release commit

From a clean checkout of the reviewed `main` commit:

```sh
nix develop .#ci --command make validate
```

The tag workflow creates a draft and attaches the exact source commit and mandatory-workflow
digests. Connected qualification evidence must bind that tag and digest manifest; it must never
reference an intermediate PR commit.

Verify `hygiene`, `smoke`, and `required-repository-policy` passed for that same commit.

## Create the immutable release

Tag the commit the manifest attests, never whatever `main` happens to point at. A squash or
rebase merge leaves that commit reachable only from stale branches, so `git tag -s v5.0.0 -m …`
with no commit operand tags a different tree and nothing reports it.

```sh
git switch main
git pull --ff-only
approved_tag=v5.0.0
approved_release_commit=FULL_PROTECTED_MAIN_SHA_FROM_RELEASE_EVIDENCE
test "${#approved_release_commit}" -eq 40
git merge-base --is-ancestor "$approved_release_commit" origin/main
git tag -s "$approved_tag" -m "Mindclade shared workflow contract v5" "$approved_release_commit"
git verify-tag "$approved_tag"
git push origin "$approved_tag"
```

Confirm `release.yml` reports the signed annotated tag as GitHub-verified, leaves the release in
draft state, and attaches a checksum-verified source manifest. Run native Linux AMD64/ARM64 and
Darwin qualification, both independent Linux rebuilds, and the connected WIF/cloud canary
against the exact tag. Archive the resulting evidence bundle, then dispatch
`publish-release.yml` with its digest and protected change ticket. Two independent environment
approvals are mandatory.

Confirm the annotated tag peels back to the same commit before consumers pin it:

```sh
release_sha="$(git rev-parse "${approved_tag}^{}")"
test "$release_sha" = "$approved_release_commit"
```

## Verify

Open a reviewed pull request in one representative consumer using an exact release reference:

```yaml
jobs:
  ci:
    uses: mindclade/.github/.github/workflows/reusable-go-ci.yml@v5.0.0
```

Verify the called jobs report the expected check names and permissions. For WIF-enabled
workflows, also perform the qualification in [OIDC and WIF](WIF.md#qualification).

Pilot the repository-home composite action with the captured commit, not the tag or annotated
tag object ID:

```yaml
- uses: mindclade/.github/actions/validate-repository-home@<release-commit-sha>
  with:
    adoption-record-path: contracts/policy-bundle/adoption.json
    local-validator-path: scripts/validate-repository-home.py
```

## Roll back or recover

If validation fails before the tag is pushed, correct `main` through a pull request and recreate
the local tag. After a tag is pushed, do not move, delete, or reuse it; correct `main` and publish
the correction as a new semantic version.
