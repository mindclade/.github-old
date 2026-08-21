<!-- mindclade-doc: how-to@1 -->

# Publish the first shared workflow contract

> **Audience:** Platform and security maintainers
> **Outcome:** The reviewed `v4.0.0` ARC workflow contract is published as an immutable GitHub
> Release and can be adopted by downstream repositories.
> **Risk:** Critical—downstream CI and cloud trust may bind the released workflow identity.

## Before you begin

- `main` is protected by the required checks listed in [Enterprise setup](ENTERPRISE_SETUP.md).
- Tags matching `v*` are protected and organization immutable releases are enabled.
- `CHANGELOG.md` describes `v4.0.0`.
- Starter workflows and WIF policy references use `v4.0.0`.
- `platform` and `security` reviewers have approved the release commit.

## Qualify the release commit

From a clean checkout of the reviewed `main` commit:

```sh
nix develop .#ci --command make validate
```

The checked-in `contracts/releases/v4.0.0.json` records the exact source commit, Git trees,
mandatory-workflow digests, and the connected evidence that source validation cannot supply.
Run `python3 tools/validate_release_readiness.py --require-local-tag` only after fetching the
authoritative tag namespace. The ordinary source check intentionally accepts an absent local tag
without treating that absence as proof about GitHub.

Verify `hygiene`, `smoke`, and `required-repository-policy` passed for that same commit.

## Create the immutable release

Tag the commit the manifest attests, never whatever `main` happens to point at. A squash or
rebase merge leaves that commit reachable only from stale branches, so `git tag -a v4.0.0 -m …`
with no commit operand tags a different tree and nothing reports it.

```sh
git switch main
git pull --ff-only
release_sha="$(python3 -c 'import json,pathlib
print(json.loads(pathlib.Path("contracts/releases/v4.0.0.json").read_text())["source_commit"])')"
test "${#release_sha}" -eq 40
git merge-base --is-ancestor "${release_sha}" origin/main

git tag -a v4.0.0 -m "Mindclade ARC artifact-authority workflow foundation v4" "${release_sha}"
git push origin v4.0.0
```

Confirm `release.yml` publishes the draft and the organization immutable-release policy locks
the release and tag.

Confirm the annotated tag peels back to the same commit before consumers pin it:

```sh
test "$(git rev-parse 'v4.0.0^{}')" = "${release_sha}"
```

## Verify

Open a reviewed pull request in one representative consumer using an exact release reference:

```yaml
jobs:
  ci:
    uses: mindclade/.github/.github/workflows/reusable-go-ci.yml@v4.0.0
```

Verify the called jobs report the expected check names and permissions. For WIF-enabled
workflows, also perform the qualification in [OIDC and WIF](WIF.md#qualification).

Pilot the repository-home composite action with the captured commit, not the tag or annotated
tag object ID:

```yaml
- uses: mindclade/.github/actions/validate-repository-home@<release-commit-sha> # v4.0.0
  with:
    local-validator-path: scripts/validate-repository-home.py
```

## Roll back or recover

If validation or publication fails, correct `main` through a pull request and retry with the
same tag only if GitHub never published or protected it. Once `v4.0.0` is published and
immutable, do not move or delete it; publish the correction as a new semantic version.
