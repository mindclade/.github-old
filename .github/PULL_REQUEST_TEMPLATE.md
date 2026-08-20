## Summary

Describe the outcome and the smallest coherent vertical slice implemented here.

## Ownership and boundaries

- Owning component/team:
- Public contract or artifact changes:
- Cross-component dependency changes:

## Validation

- [ ] Formatting and static analysis passed for every changed language.
- [ ] Affected tests passed.
- [ ] Lockfiles, generated files, and repository metadata are current.
- [ ] Documentation and operational evidence were updated where required.
- [ ] This change introduces no secrets, customer data, model weights, generated build
      output, or restricted biological content.

List the exact commands and results:

```text

```

## Release and operations

Describe rollout, compatibility, observability, security, and rollback impact. Write `None`
when the change cannot affect a release or a running environment.

<!--
Infrastructure and org-configuration changes carry extra requirements. Delete this block
unless the PR touches one of them.

Terraform / Terragrunt:
  - [ ] Plan output attached, and it matches what this PR claims to do.
  - [ ] No resource is being destroyed and recreated unintentionally — check for
        `must be replaced` in the plan.
  - [ ] Module sources are pinned to a semver tag, never to a branch.

github-config:
  - [ ] Ruleset changes name every repository whose merge requirements they alter.
  - [ ] Any bypass grant states who holds it, why, and when it expires.

gitops:
  - [ ] `rendered/**` was produced by CI, not hand-edited.
  - [ ] Promotion PRs copy manifests bit-identically; the only diff is the namespace overlay.
-->
