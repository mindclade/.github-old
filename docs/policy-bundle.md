<!-- mindclade-doc: reference@1 -->

# Signed policy bundle and acceptance evidence

> **Audience:** Legal, Security, Platform, release engineering, and repository owners
> **Outcome:** Change, publish, distribute, and reference one versioned policy set without
> weakening independent review or confusing source text with executed agreements.

## Canonical contract

`contracts/policy-bundle/manifest.json` is the sole bundle manifest. It assigns a version and
SHA-256 digest to the complete proprietary `LICENSE`, `LEGAL.md`, conduct policy, named source
header template, repository-home validator, SPDX LicenseRef enricher, third-party notice
validator, and bundle schemas. The manifest deliberately does not replace independently licensed
third-party material or repository-specific notices.

`tools/policy_bundle.py verify` fails if a canonical artifact or declared repository copy differs
by one byte. `sync --write` changes only declared distribution paths. The synchronization
workflow uses a narrowly scoped GitHub App to open reviewable pull requests; it never pushes to
the default branch.

`contracts/policy-bundle/version-history.json` is append-only. Every version binds one exact
manifest SHA-256. Pull-request validation compares the file with the base commit, rejects any
changed prior record, and rejects changed artifact digests unless a strictly newer version is
appended. A version identifier can therefore never name two accepted manifests.

Synchronization uses two independent source identities. The immutable, signed `v5.0.0` release
supplies the adoption validator and verifies its attached source manifest. The exact protected
`main` commit that started the synchronization run supplies the current policy bytes only after
the workflow reproduces its archive byte-for-byte and verifies the retained GitHub/Sigstore
attestation from `publish-policy-bundle.yml` against that commit and `refs/heads/main`. If that
exact commit has no successful, unexpired protected publication artifact, synchronization fails
closed. Each synchronization also writes `contracts/policy-bundle/adoption.json`, binding the
consumer to the validator release commit, release tag, bundle version, manifest SHA-256, and
repository-home validator SHA-256. The released composite action verifies that record and the
local validator mirror before evaluating repository content.

## Signature and publication

The publication workflow runs only from the exact `main` commit through the protected
`workflow-release-security` environment. It creates a reproducible `tar.gz`, a SHA-256 checksum,
and a GitHub artifact attestation signed through GitHub Actions OIDC and Sigstore. A source
manifest without a successful protected workflow attestation is an unsigned candidate, not a
published policy bundle.

Verify the source and reproduce the archive locally:

```sh
python3 tools/policy_bundle.py verify
python3 tools/policy_bundle.py build \
  --output dist/mindclade-policy-bundle-2026.08.23.1.tar.gz
```

Before relying on a bundle, verify the archive checksum and its GitHub attestation against
`mindclade/.github`, the expected workflow identity, the protected `main` ref, and the exact
source commit.

## Change control

Changes to a protected legal path require three distinct approvals: one each from Legal,
Security, and Platform. Stale approvals are dismissed, review conversations must be resolved,
and the last push must be approved by someone other than its author. CODEOWNERS provides routing
and visibility; it is not treated as proof that all three functions approved.

The legal team must have qualified members before the ruleset is activated. A same-person,
empty-team, or emergency bypass does not satisfy independent legal approval. Emergency changes
follow the incident and retrospective-review process and must never silently weaken the resting
ruleset.

## Contractual acceptance

Employment, contractor, customer, vendor, and other controlling agreements should identify the
bundle by both version and manifest SHA-256. Acceptance evidence must conform to
`contracts/policy-bundle/acceptance-record.schema.json` and remain in an approved contract,
identity, or records system—not Git.

The evidence record uses opaque references and binds together:

- the controlling agreement and authorized subject type;
- the exact bundle version, manifest digest, and signed-attestation reference;
- the acceptance time and method;
- the evidence object digest and capturing system; and
- the retention class, retention date, and legal-hold state.

Repository access text and pull-request acknowledgements are supporting controls. They do not
replace a controlling written agreement or its retained acceptance record. Counsel must approve
agreement language, retention periods, jurisdictional treatment, and production activation.

## Activation checklist

1. Legal approves the bundle contents and agreement incorporation language.
2. Security and Platform approve the manifest, validators, signing workflow, and App scope.
3. The `mindclade-policy-sync` App is created with only selected-repository `contents:write` and
   `pull_requests:write`, and its key is stored in the protected workflow environment.
4. The independent-review ruleset is applied and audited against connected GitHub state.
5. The protected publication workflow produces an attestation and retained archive.
6. Acceptance systems begin recording the exact published bundle version and digest.
7. Synchronization pull requests pass each repository's full validation before merge.

Do not represent source configuration, a local test, or an unexecuted workflow as proof that the
ruleset, App, signature, agreement, or acceptance system is active.
