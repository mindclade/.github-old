<!-- mindclade-doc: how-to@1 -->

# Import and activate the GitHub platform repository

> **Audience:** GitHub Enterprise owners and platform/security maintainers
> **Outcome:** `mindclade/.github` is imported on protected `main`, its offline and smoke checks
> pass, and the next consolidated immutable production workflow release is ready to qualify.
> **Risk:** Critical—this repository supplies organization-wide workflow implementation.

## Before you begin

- Preserve the destination repository's `.git` directory and existing audit history.
- Confirm the repository is owned by `Mindclade`, named `.github`, uses `main`, and has
  `internal` visibility as declared in `contracts/repository.yaml`.
- Create the `platform` and `security` teams before enabling CODEOWNERS enforcement.
- Keep consumer repositories pinned to their existing workflow release until qualification is
  complete.
- Do not create a v5 tag before the coordinated release-evidence review, tag protection, and
  immutable-release enforcement are complete.

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

## Prepare the next production contract

Continue using the published `v3.0.0` contract. The historical v4 source record is retired
unpublished under `contracts/releases/retired/v4.0.0.json` and is not a publishable release.
`contracts/releases/v5.0.0.json` defines the consolidated source candidate but does not authorize
a tag or publication. Follow [Workflow release bootstrap](workflow-release-bootstrap.md).

## Verify

- `v3.0.0` remains the active immutable consumer contract.
- The historical v4 record remains retired unpublished, while the v5 source manifest validates
  and no v5 tag exists before protected connected qualification.
- Starter workflows reference `@v3.0.0`.
- `python3 tools/check_workflow_contracts.py` still matches every checked-in snapshot.
- A representative consumer can call a non-cloud reusable workflow from the release.

## Roll back or recover

If qualification fails, leave consumers on their existing release, correct `main` through a
pull request, and repeat validation. If a bad immutable release is published, do not move or
delete its tag; publish a corrected patch release and update consumers through reviewed pull
requests.
