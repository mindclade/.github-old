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

The checker uses the pinned PyYAML runtime with a GitHub-compatible safe loader and projects only
the narrow YAML surface above. It rejects duplicate keys and malformed permission contracts.
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

Starter workflows intentionally remain pinned to the published `v3.0.0` contract until v5 is
qualified and published. The ARC, Nix, DR, and promotion work is one candidate `v5.0.0` source
contract; no caller may adopt it until the exact tag is qualified and the protected publication
job succeeds. Moving an existing release tag is forbidden.

The v5 GitOps promoter requires `application`, `release-kind`, `producer-evidence-digest`, and
`rollback-strategy`. A bootstrap rollback is legal only for `v1.0.0` and carries no previous
lineage; every later release must provide an exact numerically older `previous-release-id` and
nonzero `previous-subject-digest`. Do not point a caller at v5 until that immutable release exists
and its corresponding infrastructure WIF identity has been reviewed and applied.

## Nix qualification releases

`reusable-nix-qualification.yml` keeps the required-check context stable at
`nix / verdict`. Pull requests without Nix-owned changes still reach that verdict, while
merge queues, manual runs, and weekly schedules always execute qualification.

The v5 `reusable-nix-flake.yml` contract establishes a locked, runner-selectable flake check.
The v5 `reusable-nix-qualification.yml` contract adds internal change detection,
isolated CI-shell validation, an always-present verdict, native aarch64-linux and
aarch64-darwin runners, and two independent x86_64-linux rebuilds on Ubuntu 24.04 and 22.04.
The workflow records both host-image versions, rejects identical image evidence, and requires
the derivations, store paths, and SRI output hashes to agree across those environments.
Consumers may move to `@v5.0.0` only after an operator publishes that immutable release;
neither this documentation nor a branch commit creates or moves a release tag.

The subtree mirror may destructively refresh its documented target branch, but its App-backed
tagger is not a qualified cryptographic signer. Every nonempty `tag` input therefore fails before
the branch is rewritten. Target-tag activation remains blocked until a separate signed release
authority can bind the exact source, split, subtree, and workflow provenance and pass connected
positive and negative tests. Existing target tags are never repaired or replaced.

Nix owns host tooling and reproducibility evidence. Bazel remains authoritative for the
monorepo build/test graph and application container images, and this workflow does not create
parallel NixOS, nix-darwin, Home Manager, or Nix container-image authority.

`reusable-nix-cache-populate.yml` is a separate, activation-blocked publication API. It accepts
only the canonical monorepo's protected-main `nix-cache.yml` caller and only push, schedule, or
manually approved dispatch events. Its protected `nix-cache-publication` job receives one
cache-scoped write token from that environment, never from `workflow_call`; it receives no cloud
credential, cache-administration token, server JWT key, or Nix signing key. The called repository's
machine contract remains disabled until the
private Attic endpoint, public key, read authentication, GCS/HMAC boundary, database recovery,
token claims, and cold/warm/tamper tests have connected evidence. No v5 tag or merged source alone
activates the workflow because no caller is present while that contract is blocked.
