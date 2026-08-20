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

Starter workflows intentionally pin `v3.0.0`, the first production contract of this
repository. Subsequent consumers may be upgraded by Renovate, but moving an existing release
tag is forbidden. Publish a new patch/minor/major release instead.
