<!-- mindclade-doc: how-to@1 -->

# Publish the deferred v4 shared workflow contract

> **Audience:** Platform and security maintainers
> **Outcome:** A future, coordinated review publishes the ARC workflow contract as an immutable
> release that downstream repositories may adopt.
> **Risk:** Critical—downstream CI and cloud trust may bind the released workflow identity.

> **Current status:** Deferred. Main contains candidate source only. There is no v4 release
> manifest or authorized v4 tag, and consumers must remain on `v3.0.0` until a separate release
> PR records evidence for the final main commit.

## Before you begin

- `main` is protected by the required checks listed in [Enterprise setup](ENTERPRISE_SETUP.md).
- Tags matching `v*` are protected and organization immutable releases are enabled.
- `CHANGELOG.md` describes the final proposed v4 contract.
- Starter workflows and active WIF policy references still use the published `v3.0.0` contract.
- `platform` and `security` reviewers have approved the release commit.

## Qualify the release commit

From a clean checkout of the reviewed `main` commit:

```sh
nix develop .#ci --command make validate
```

A separate release-evidence PR must record the final source commit, Git trees,
mandatory-workflow digests, and connected qualification. The evidence must reference a commit
reachable from protected main after merge; it must never reference an intermediate PR commit.

Verify `hygiene`, `smoke`, and `required-repository-policy` passed for that same commit.

## Create the immutable release

```sh
git switch main
git pull --ff-only
approved_tag=v4.0.0 # replace with the tag approved by the release-evidence PR
git tag -a "$approved_tag" -m "Mindclade ARC artifact-authority workflow foundation"
git push origin "$approved_tag"
```

Confirm `release.yml` publishes the draft and the organization immutable-release policy locks
the release and tag.

Capture the commit behind the annotated release tag for composite-action consumers:

```sh
release_sha="$(git rev-parse "${approved_tag}^{}")"
test "${#release_sha}" -eq 40
git merge-base --is-ancestor "${release_sha}" origin/main
```

## Verify

Open a reviewed pull request in one representative consumer using an exact release reference:

```yaml
jobs:
  ci:
    uses: mindclade/.github/.github/workflows/reusable-go-ci.yml@<approved-v4-tag>
```

Verify the called jobs report the expected check names and permissions. For WIF-enabled
workflows, also perform the qualification in [OIDC and WIF](WIF.md#qualification).

Pilot the repository-home composite action with the captured commit, not the tag or annotated
tag object ID:

```yaml
- uses: mindclade/.github/actions/validate-repository-home@<release-commit-sha>
  with:
    local-validator-path: scripts/validate-repository-home.py
```

## Roll back or recover

If validation or publication fails, correct `main` through a pull request and retry with the
same tag only if GitHub never published or protected it. Once the release is published and
immutable, do not move or delete it; publish the correction as a new semantic version.
