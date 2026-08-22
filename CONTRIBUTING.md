<!-- mindclade-doc: contributing@1 -->

# Contributing to Mindclade

This is the canonical organization contribution policy. GitHub does not inherit community
files from an internal `.github` repository, so every governed repository carries a local
`CONTRIBUTING.md`. Each local file preserves the authorization and intellectual-property
terms below and adds only the workflow, risk, and validation facts specific to that repository.

Change an organization-wide rule here first, version the common-document contract, and migrate
all local files in reviewed pull requests. Repository-specific guidance changes in its owning
repository and must not silently weaken the common terms.

## Before you start

For anything that crosses a component boundary, changes a public contract, or is expensive to
reverse: open a design discussion first. A discussion that ends in "we decided not to" saved
you the implementation.

For a bug fix or a self-contained change, just open the PR.

## Ground rules

**Never commit** credentials, private keys, production configuration, customer data, model
weights, restricted biological sequences, or adversarial safety corpora. Push protection blocks
the common shapes. It is not a substitute for attention.

**Pin what you depend on.** Actions to a commit SHA, Terraform modules to a semver tag,
container images to a digest. A mutable reference is an unreviewed change with a delayed fuse.

**Small, coherent PRs.** One reviewable idea. A 40-file PR that mixes a refactor with a
behavior change gets read as neither.

## Commit messages

Conventional Commits — the type prefix drives changelog generation and release tooling:

```text
feat(control-plane): add per-tenant rate limit override
fix(sdk-python): retry on 429 with jitter
chore(deps): bump golangci-lint to 2.6.2
```

Types: `feat`, `fix`, `perf`, `refactor`, `test`, `docs`, `build`, `ci`, `chore`. Append `!`
before the colon for a breaking change, and explain the break in the body.

## Pull requests

The PR template is not a formality. Two parts get read closely:

- **Validation** — the exact commands you ran and their results. "Tests pass" is not evidence;
  the command and its output is.
- **Release and operations** — rollout, compatibility, observability, and rollback. Write
  `None` when the change genuinely cannot affect a running environment. Do not leave it blank.

Every PR needs at least one approval, a clean required-check run, all conversations resolved,
signed commits, and linear history. Those are enforced by org rulesets, so you will not be able
to merge without them.

Paths under `rendered/production/**`, `policy/**`, and `*.tf` need two approvals plus code-owner
review. That is deliberate friction on the things that are expensive to get wrong.

## Signing your commits

Signed commits are required org-wide. Set it up once:

```sh
git config --global commit.gpgsign true
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
```

Then add the same public key to your GitHub account as a **signing key** — this is a separate
entry from the authentication key, and adding it only as an auth key produces commits that show
as unverified.

## Reviewing

A review is a decision, not a comment thread. Approve, request changes, or say explicitly that
you are not the right reviewer and name who is.

Distinguish blocking from non-blocking. Prefix anything optional with `nit:` so the author can
tell what actually stands between them and merge.

## Getting help

- Something broken in a repo → an issue on that repo
- A vulnerability → [`SECURITY.md`](SECURITY.md), never an issue
- How the org is governed → [`GOVERNANCE.md`](GOVERNANCE.md)
- Anything else → [`SUPPORT.md`](SUPPORT.md)


## Contributor authorization and intellectual property

A contribution may be submitted only by a person authorized under a current
written employment, contractor, assignment, or other contribution agreement
with Mindclade, LLC. Before opening or updating a pull request, the contributor
must confirm that:

- they have the right and authority to submit every part of the contribution;
- first-party work is covered by the contributor's controlling written
  agreement with Mindclade, LLC.;
- third-party code, data, models, media, fonts, specifications, and generated
  material are identified with their source, version, license, provenance, and
  required notices;
- the contribution contains no material whose confidentiality, license,
  consent, acceptable-use terms, export controls, or other restrictions
  prohibit submission; and
- the change description and validation evidence are complete and accurate.

By submitting or updating a pull request, the contributor represents that these
statements are true. Submission is not acceptance and does not by itself alter
ownership, grant a license, or replace the controlling written agreement.
Signed commits establish source identity and integrity; they are not a
substitute for the required written agreement.

If authorization or ownership is unclear, stop before submission and use the
legal or contract channel named in the applicable agreement. Do not place
confidential material in a public issue or an unapproved email.
