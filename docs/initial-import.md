<!-- mindclade-doc: how-to@1 -->

# Import and activate the GitHub platform repository

> **Audience:** GitHub Enterprise owners and platform/security maintainers
> **Outcome:** `mindclade/.github` is imported on protected `main`, its offline and smoke checks
> pass, and the first immutable production workflow release is ready to publish.
> **Risk:** Critical—this repository supplies organization-wide workflow implementation.

## Before you begin

- Preserve the destination repository's `.git` directory and existing audit history.
- Confirm the repository is owned by `Mindclade`, named `.github`, uses `main`, and has
  `internal` visibility as declared in `contracts/repository.yaml`.
- Create the `platform` and `security` teams before enabling CODEOWNERS enforcement.
- Keep consumer repositories pinned to their existing workflow release until qualification is
  complete.
- Do not create `v3.0.0` before tag protection and immutable-release enforcement are active.

## Import and validate

From the repository root:

```sh
nix develop .#ci --command make validate
```

Expected result: workflow contracts, action pins, the production repository contract, offline
repository validation, actionlint, and yamllint all pass.

Push `main` and verify these repository workflows pass:

- `hygiene / actionlint + yamllint`;
- `hygiene / offline validation`;
- `smoke / verdict`; and
- `required-repository-policy / verify`.

## Activate governance dependencies

Follow [Enterprise setup](ENTERPRISE_SETUP.md) to enable branch/tag protection, immutable
releases, Actions restrictions, required workflows, and OIDC repository-property policy.
Roll organization rulesets out in Evaluate mode before Active mode.

Do not enable cloud-dependent consumer workflows until `bootstrap`, `github-config`, and the
required WIF negative authorization tests are qualified.

## Publish the first production contract

Follow [Workflow release bootstrap](workflow-release-bootstrap.md). The current first
production contract is `v3.0.0`; the older `v1` bootstrap language is obsolete.

## Verify

- `v3.0.0` points to the reviewed `main` commit and is an annotated tag.
- The GitHub Release is published and protected by immutable-release policy.
- Starter workflows reference `@v3.0.0`.
- `python3 tools/check_workflow_contracts.py` still matches every checked-in snapshot.
- A representative consumer can call a non-cloud reusable workflow from the release.

## Recover

If qualification fails, leave consumers on their existing release, correct `main` through a
pull request, and repeat validation. If a bad immutable release is published, do not move or
delete its tag; publish a corrected patch release and update consumers through reviewed pull
requests.
