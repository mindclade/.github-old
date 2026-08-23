<!-- mindclade-doc: how-to@1 -->

# Publish the consolidated v5 shared workflow contract

> **Audience:** Platform and security maintainers
> **Outcome:** A future, coordinated review publishes the ARC workflow contract as an immutable
> release that downstream repositories may adopt.
> **Risk:** Critical—downstream CI and cloud trust may bind the released workflow identity.

> **Current status:** Source candidate only. The historical v4 record is retired unpublished at
> `contracts/releases/retired/v4.0.0.json` and must not be published.
> `contracts/releases/v5.0.0.json` defines the consolidated source candidate; no v5 tag or release
> exists. Connected read-back on 2026-08-23 reports repository-level immutable releases enabled
> but not enforced by the organization owner; `workflow-release-platform` is absent;
> `workflow-release-security` allows administrator bypass and has no protection rules; and the
> effective ruleset read is rejected by the current GitHub plan. Publication remains blocked until
> every control passes the read-only preflight.

## Before you begin

- `main` is protected by the required checks listed in [Enterprise setup](ENTERPRISE_SETUP.md).
- Tags matching `v*` are protected and organization immutable releases are enabled.
- `CHANGELOG.md` describes the final proposed v5 contract.
- Starter workflows and active WIF policy references still use the published `v3.0.0` contract.
- `platform` and `security` reviewers have approved the release commit.
- The Release operator's signing key is registered with GitHub as a signing key.
- The source-qualified `mindclade-release-governance-reader` App is installed with its exact
  read-only permissions, App ID variable, and protected private-key secret.

## Qualify the release commit

From a clean checkout of the reviewed `main` commit:

```sh
nix develop .#ci --command make validate
```

The tag workflow creates a draft and attaches the exact source commit and mandatory-workflow
digests. Connected qualification evidence must bind that tag and digest manifest; it must never
reference an intermediate PR commit.

Verify `hygiene`, `smoke`, and `required-repository-policy` passed for that same commit.

After github-config's protected apply and connected audit, dispatch
`release-governance-preflight.yml` from protected `main`. It must pass using the repository
`GITHUB_TOKEN` for checkout identity and the narrowly scoped release-governance reader token for
Administration and Members read. A missing or API-omitted Release-team bypass, no-bypass
tag-protection, reviewer membership, or immutable-release inventory is a hard blocker. The
preflight requires immutable releases to be enabled and enforced by the organization owner, so a
repository administrator cannot disable the control during publication.

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
draft state, extracts the exact nonempty `## v5.0.0` changelog section, and attaches a
checksum-verified source manifest. Run native Linux AMD64/ARM64 and
Darwin qualification, both independent Linux rebuilds, and the connected WIF/cloud canary
against the exact tag. Archive the resulting evidence bundle, then dispatch
`publish-release.yml` with its digest and protected change ticket. Two independent environment
approvals are mandatory. Qualification evidence expires after 24 hours. The publisher re-reads
the protected `main` head, exact tag object and peeled commit, release governance, and immutable
release enforcement after the approval waits and again immediately before publication. It also
requires two distinct approved reviewers, neither the dispatcher, and proves each reviewer's
current membership in the expected Platform or Security team. Any drift or expired evidence
requires a fresh dispatch and approvals.

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
