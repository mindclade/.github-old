# Mindclade common-document contract

<!-- mindclade-doc: documentation-standard@1 -->

| Document control | Value |
| --- | --- |
| Owner | Mindclade Engineering |
| Product owner | Mindclade Platform |
| Version | 1.0 |
| Effective | August 21, 2026 |
| Brand distribution | `mindclade/.github-private/mindclade-brand-assets` · MONO family |

## Objective

Every governed repository must present one coherent, locally available set of
top-level documents that tells an authorized reader what the repository is,
how to contribute, how decisions are made, where to get help, how to report a
vulnerability or conduct concern, what rights apply, what third-party terms
remain in force, and what materially changed.

This contract is both a publication standard and a validation interface. A
document is not complete merely because a file with the expected name exists.
It must identify its authority, preserve repository-specific facts, route the
reader to an actionable next step, and satisfy the machine checks below.

## Users and outcomes

| Reader | Required outcome |
| --- | --- |
| New contributor | Reaches a verified first-success path and knows the authorization required to submit work |
| Reviewer or approver | Can determine authority, evidence, approval, rollout, rollback, and exception requirements |
| Operator | Can route a defect, incident, recovery, or support need without disclosing sensitive material |
| Security reporter | Reaches a private channel and understands scope, response targets, and safe harbor |
| Legal or compliance reviewer | Can resolve every first-party SPDX identifier and locate third-party precedence and notices |
| Release consumer | Can distinguish unreleased work from a published, qualified artifact |

## Required root set

| File | Contract | Standardization rule |
| --- | --- | --- |
| `README.md` | `repository-home@2` | Branded, repository-specific, bounded to 850 prose words, local images only |
| `CONTRIBUTING.md` | `contributing@1` | Repository workflow plus the canonical authorization and IP section |
| `SECURITY.md` | `security@1` | Private reporting, repository scope, canonical policy link, sensitive-data stop condition |
| `SUPPORT.md` | `support@1` | Repository routes, no implied SLA, security separation, sensitive-data stop condition |
| `CODE_OF_CONDUCT.md` | `code-of-conduct@1` | Exact estate policy, private reporting, non-retaliation, conflict-safe enforcement |
| `GOVERNANCE.md` | `governance@1` | Authority, decision rights, evidence, exceptions, and review cadence |
| `CHANGELOG.md` | `changelog@1` | Unreleased state is explicit; history is never fabricated or silently rewritten |
| `LEGAL.md` | `legal-and-reliance@1` | Exact estate policy for authority, precedence, reliance, representations, and counsel review |
| `LICENSE` | `mindclade-license@2` | Exact estate proprietary terms, protected-disclosure notice, and resolvable custom SPDX identifier |
| `NOTICE` | `mindclade-notice@1` | Repository identity, first-party notice, third-party precedence, artifact obligations |
| `THIRD_PARTY_NOTICES.md` | generated notice evidence | Deterministic complete license text, attribution, version, source URL, and provenance for declared third-party material |
| `AGENTS.md` | repository instructions | Local implementation and safety instructions; never a substitute for legal terms |

Every repository also carries `.github/PULL_REQUEST_TEMPLATE.md`. The template records an
explicit contributor-authorization affirmation, third-party disclosure, and the obligation to
update `LICENSE`, `NOTICE`, SBOM, or other license evidence when distributed material changes.

GitHub applies default community files only from a public `.github`
repository. Mindclade's `.github` repository is internal, so each governed
repository carries its own local community files. The local files may preserve
repository-specific routes, but the document marker and mandatory policy
language are invariant.

## Legal and licensing rules

1. `LicenseRef-Mindclade-Proprietary` always resolves to the complete root
   `LICENSE`; no repository may use a one-line substitute.
2. The copyright notice identifies the owner as `Mindclade, LLC.` and includes
   the copyright symbol and first-publication year.
3. A repository notice never claims ownership of third-party code, fonts,
   datasets, models, media, specifications, or standards.
4. Third-party terms control for third-party material. Their notices,
   attribution, provenance, consent, and use restrictions are preserved.
5. A contribution is accepted only from a contributor whose controlling
   written agreement provides the required authority and rights. Commit
   signing proves identity and integrity; it is not an IP assignment.
6. No repository document invents a governing law, court, corporate signatory,
   support commitment, confidentiality relationship, or counsel approval.
7. A customer, employment, contractor, nondisclosure, or other controlling
   written agreement prevails over repository text where the two conflict.
8. `LEGAL.md` defines the estate-wide reliance boundary. Technical documents
   do not become warranties, SLAs, certifications, privacy notices, access
   grants, or regulated-use approvals merely because they are reviewed or
   published.
9. Adapted content preserves the upstream attribution, license link, and a
   description of Mindclade's modifications. Vendored distributions preserve
   their controlling license text next to the vendored material.
10. `LICENSE` is the sole root filename beginning with `LICENSE`. Repositories
    that enforce source headers keep the exact reusable snippet at
    `.github/MINDCLADE_PROPRIETARY_SOURCE_HEADER.txt`; that template identifies
    itself as a header, carries `LicenseRef-Mindclade-Proprietary`, and is not a
    second license.
11. `contracts/third-party-materials.json` is the reviewed inventory overlay for
    repository-resident third-party material. The policy-bundle generator rejects
    missing or abbreviated license text, missing attribution, absent versions,
    non-HTTPS sources, stale hashes, and unreviewed release-SBOM packages. Every
    shared-workflow SPDX 2.3 SBOM carries the complete extracted proprietary
    LicenseRef and a digest-bound first-party artifact package before attestation.
12. The signed `mindclade-policy-bundle` versions the exact license, legal and
    conduct policies, source header, validators, and evidence schemas. A source
    manifest is not published until its protected workflow produces a verifiable
    artifact attestation.

These controls state repository terms and authorization conditions explicitly;
they do not guarantee enforceability in every jurisdiction or circumstance.
They are not a substitute for review by qualified counsel for the company,
transaction, jurisdiction, or workforce involved.

## Editorial and brand rules

- Use `Mindclade` and the legal name `Mindclade, LLC.` consistently.
- Root README artwork comes only from the checked-in MONO brand distribution and is
  vendored locally with verified digests.
- Policy documents use descriptive headings, sentence-case prose, accessible
  tables, meaningful link text, and one level-one heading.
- Dates are absolute and written as `Month D, YYYY` in legal or policy document
  control; changelog entry dates use ISO `YYYY-MM-DD`.
- Do not use decorative remote badges, tracking images, animated GIFs, or
  color as the only carrier of meaning.
- Do not assert that a scaffold, plan, render, test, or document is deployment
  or production qualification evidence unless the owning qualification
  contract says so.

## Acceptance criteria

A governed repository passes only when all of the following are true:

- all twelve required root files and the pull-request template exist, are nonempty UTF-8 text, and end in a
  newline;
- each versioned file contains exactly one expected document-control marker;
- the root license matches the canonical `mindclade-license@2` digest;
- no second root license-like filename exists, and any source-header template
  matches its canonical digest and identifies the root `LICENSE` as controlling;
- the legal-reliance and conduct policies match their canonical estate digests;
- the notice names the repository from `contracts/repository.yaml` and states
  third-party precedence and the Contributor Covenant attribution;
- `THIRD_PARTY_NOTICES.md` exactly matches its reviewed provenance contract and
  contains complete digest-pinned license text for every declared material;
- contribution terms contain the authorization, rights, third-party, and
  signed-commit limitations;
- security and support files route vulnerabilities away from public issues,
  identify response times as non-contractual operational targets, bound safe
  harbor to authorized scope, and do not claim that Mindclade publishes a PGP
  key;
- all files named by `required_paths` in the repository contract exist;
- unqualified certification, compliance, guarantee, or response-time claims are
  absent unless a current annotation identifies scope, owner, evidence, review
  date, and expiry;
- the repository-home validator and its negative regression tests pass; and
- repository-specific validation passes without weakening or skipping another
  production gate.

## Change control

Changing an invariant, marker version, required file, legal term, or validation
rule requires:

1. a pull request in `mindclade/.github` describing the compatibility and legal
   impact;
2. distinct Legal, Security, and Platform approvals for every protected legal
   path, with stale-review dismissal and approval of the last push;
3. a version increment and migration plan for all governed repositories;
4. synchronized validators and negative tests; and
5. changelog entries that distinguish adoption from publication.

Repository-specific operational content changes through the owning
repository's normal approval path. No change to this document authorizes a
production apply, deployment, access grant, or legal execution.
