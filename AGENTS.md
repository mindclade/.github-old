# Agent operating guide

## Purpose and authority

This repository owns shared workflow implementations, workflow contracts, organization profile,
and community-health assets. Read BLUEPRINT.md, README.md, CONTRIBUTING.md, and
docs/WORKFLOW_CONTRACTS.md before editing. github-config owns the rulesets and settings that
require these workflows.

## Working rules

- Preserve workflow_call interfaces or release a documented compatibility change.
- Use explicit least-privilege permissions, immutable third-party Action pins, and
  persist-credentials false unless a reviewed write path requires otherwise.
- Never place cloud policy, repository settings, secrets, or deployment desired state here.
- Treat release tags and reusable-workflow identity as trust surfaces. Do not publish or move a
  tag from an agent session.
- Update contracts/workflows with every reusable workflow interface change.

## Validation

    nix develop .#ci --command make validate
    nix flake check --no-update-lock-file

Consumer qualification against an immutable released tag is required before a workflow release
is considered deployable.

## Done

Workflow lint, contract parity, pin validation, and repository validation pass; permissions and
consumer compatibility are documented; release publication remains an explicit operator action.
