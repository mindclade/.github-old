# Governance

How decisions get made across `Mindclade`, and where each rule physically lives. A repo
with its own `GOVERNANCE.md` overrides this — `mindclade-internal-monorepo` does, and describes
its package-level ownership model there.

## The rule: if it governs, it is code

Nothing in this organisation is governed by a setting somebody clicked. Every control is
declared in a repository, reviewed as a diff, and checked nightly for drift. A ruleset silently
disabled in the UI is indistinguishable from one that never existed, which is exactly why
drift detection is the point rather than a nicety.

| What | Declared in | Applied by |
|---|---|---|
| Org settings, teams, rulesets, environments | [`github-config`](https://github.com/mindclade/github-config) | Terraform, CI-applied behind an environment gate |
| GCP org hierarchy, state backend, WIF, break-glass | [`bootstrap`](https://github.com/mindclade/bootstrap) | Terraform, human-applied |
| Live GCP infrastructure | [`infrastructure-live`](https://github.com/mindclade/infrastructure-live) | Terragrunt, CI-applied behind an environment gate |
| Cluster state and admission policy | [`gitops`](https://github.com/mindclade/gitops) | ArgoCD |
| Org-wide CI, templates, community health | [`.github`](https://github.com/mindclade/.github) | Inheritance and `uses:` |
| Member-only organization profile | [`.github-private`](https://github.com/mindclade/.github-private) | GitHub member-profile rendering |
| Package ownership and promotion policy | Monorepo `governance/` | `just policy` |

Enterprise-account settings that no provider can manage — SAML, SCIM, enterprise policies —
are the one exception. They are configured in the UI and tracked against a written checklist
in `github-config/docs/enterprise-manual-controls.md`, reviewed on the same cadence as
everything else.

## Who decides what

**Any engineer** decides how to implement work inside their own component, and merges with one
approval and green checks.

**Code owners** decide on changes to what they own. CODEOWNERS is per-repo and, in the
monorepo, generated from the ownership registry rather than hand-edited.

**`@security`** must approve changes to rulesets, admission policy, IAM, and anything under
`policy/**`. This is a hard gate, not a courtesy review.

**`@platform` and `@security` jointly** approve production infrastructure and
`rendered/production/**`. Two approvals, code-owner review required.

**Leadership** decides on things that cross all of the above: which environments exist, what
the enterprise policy is, and who holds break-glass access.

## Changing something expensive to reverse

Open a design discussion before writing code when the change crosses a component boundary,
alters a public contract, or is hard to undo. State the problem without reference to your fix,
the constraints that rule options out, the alternatives you rejected and why, and the blast
radius if you are wrong. "Irreversible" is a valid answer and should be written down as one.

Architecture decisions that stick are recorded under `docs/decisions/` in the relevant repo.

## Bypass

Rulesets support delegated bypass, and some people hold it. Two conditions apply without
exception: every bypass is logged and reviewed, and every grant has an expiry. A standing
permanent bypass is a deleted rule with extra steps.

Break-glass access to GCP carries no standing permissions, alerts on any use, and grants for
one hour. Each use is reviewed after the fact — not to assign blame, but because an
unexamined emergency path stops being an emergency path and becomes the normal one.

## Review cadence

| What | How often | Who |
|---|---|---|
| Drift on every Terraform repo | Nightly, automated; an issue opens on delta | Owning team |
| Enterprise manual-control checklist | Monthly | `@security` |
| Access review — who has what, and why | Quarterly | `@security` + leadership |
| Break-glass and bypass usage | Quarterly, and after every use | `@security` |
| Cold-start drill: rebuild the org from zero | Annually, executed by someone who did not write it | `@platform` |

That last one matters more than it looks. A runbook nobody has executed is a hypothesis.
