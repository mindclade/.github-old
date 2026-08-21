# Reusable workflow contracts

Reusable workflows in `mindclade/.github` are organization APIs. Consumers pin immutable
full-semver releases, so changes are released deliberately rather than flowing from `main`.

## What is part of the contract

`contracts/workflows/*.json` snapshots these externally significant fields:

- `workflow_call` input names, types, requiredness, and defaults;
- `workflow_call` secret names and requiredness;
- declared workflow outputs;
- job IDs;
- top-level explicit permissions;
- per-job explicit permissions.

Implementation steps, action versions, comments, descriptions, and shell internals are not
snapshotted. They can be patched without pretending the caller API changed, subject to normal
security/review requirements.

## Validation

Run:

```sh
python3 tools/check_workflow_contracts.py
```

The checker is intentionally dependency-free and parses only the narrow YAML surface above.
`tools/validate_repo.py` invokes it too, and `hygiene.yml` runs both commands explicitly.

A mismatch fails with a unified diff between the checked-in contract and the current workflow.

## Changing a contract

Do not refresh snapshots merely to make CI green. First classify the change:

- adding a required input/secret, removing or renaming an input/output/job, tightening a
  default, or changing permissions in a caller-visible way is breaking;
- adding an optional input with a backward-compatible default may be minor;
- implementation-only behavior fixes that preserve the API are patch changes.

After the version decision and review, refresh snapshots:

```sh
python3 tools/check_workflow_contracts.py --update
python3 tools/check_workflow_contracts.py
python3 tools/validate_repo.py
```

Review every JSON diff. The snapshot update and workflow change should land in the same pull
request with the intended semver release documented in `CHANGELOG.md`.

## Release references

Starter workflows intentionally remain pinned to the published `v3.0.0` contract. The ARC
artifact-authority work is candidate source only; no caller may adopt it until a separate,
reviewed v4 release is published from the final protected-main commit. Moving an existing
release tag is forbidden. Publish a new patch/minor/major release instead.

The unreleased GitOps promoter interface is a planned `v5.0.0` breaking change: callers provide
`application`, `release-kind`, `previous-release-id`, and `previous-subject-digest`. The exact
identity is validated against the GitOps closed package catalog, while the exact lineage pair
replaces the v4 `rollback-digest` input and proves the rollback target rather than merely naming
an otherwise-unattributed digest. The previous release must be numerically older than the
candidate. Do not point a caller at v5 until that immutable release exists and its corresponding
infrastructure WIF workflow identity has been reviewed.

## Nix qualification releases

`reusable-nix-qualification.yml` keeps the required-check context stable at
`nix / verdict`. Pull requests without Nix-owned changes still reach that verdict, while
merge queues, manual runs, and weekly schedules always execute qualification.

The draft v4.0 `reusable-nix-flake.yml` contract establishes a locked, runner-selectable flake
check. The draft v4.1 `reusable-nix-qualification.yml` contract adds internal change detection,
isolated CI-shell validation, an always-present verdict, native aarch64-linux and
aarch64-darwin runners, and two independent x86_64-linux rebuilds whose derivations, store
paths, and SRI output hashes must agree.
Consumers may move to `@v4.1.0` only after an operator publishes that immutable release;
neither this documentation nor a branch commit creates or moves a release tag.

Nix owns host tooling and reproducibility evidence. Bazel remains authoritative for the
monorepo build/test graph and application container images, and this workflow does not create
parallel NixOS, nix-darwin, Home Manager, or Nix container-image authority.
