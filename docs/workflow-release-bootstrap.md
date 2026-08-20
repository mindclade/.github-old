<!-- mindclade-doc: how-to@1 -->

# Publish the first shared workflow contract

> **Audience:** Platform and security maintainers
> **Outcome:** The reviewed `v3.0.0` workflow contract is published as an immutable GitHub
> Release and can be adopted by downstream repositories.
> **Risk:** Critical—downstream CI and cloud trust may bind the released workflow identity.

## Before you begin

- `main` is protected by the required checks listed in [Enterprise setup](ENTERPRISE_SETUP.md).
- Tags matching `v*` are protected and organization immutable releases are enabled.
- `CHANGELOG.md` describes `v3.0.0`.
- Starter workflows and WIF policy references use `v3.0.0`.
- `platform` and `security` reviewers have approved the release commit.

## Qualify the release commit

From a clean checkout of the reviewed `main` commit:

```sh
nix develop .#ci --command make validate
```

Verify `hygiene`, `smoke`, and `required-repository-policy` passed for that same commit.

## Create the immutable release

```sh
git switch main
git pull --ff-only
git tag -a v3.0.0 -m "Mindclade GitHub Enterprise workflow foundation v3"
git push origin v3.0.0
```

Confirm `release.yml` publishes the draft and the organization immutable-release policy locks
the release and tag.

## Verify a consumer

Open a reviewed pull request in one representative consumer using an exact release reference:

```yaml
jobs:
  ci:
    uses: mindclade/.github/.github/workflows/reusable-go-ci.yml@v3.0.0
```

Verify the called jobs report the expected check names and permissions. For WIF-enabled
workflows, also perform the qualification in [OIDC and WIF](WIF.md#qualification).

## Roll back or recover

If validation or publication fails, correct `main` through a pull request and retry with the
same tag only if GitHub never published or protected it. Once `v3.0.0` is published and
immutable, do not move or delete it; publish the correction as a new semantic version.
