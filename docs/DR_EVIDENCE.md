<!-- mindclade-doc: how-to-guide@1 -->

# Publish disaster-recovery evidence

The reusable `reusable-dr-evidence.yml` workflow is the only shared automation authorized to
publish completed disaster-recovery reports. It accepts scratch and staging reports only. A
production target is an abort condition, not a supported input.

## Protection contract

Configure separate `scratch` and `staging` GitHub environments in each caller. Require a named
observer as an environment reviewer and prevent self-review. Store `WIF_PROVIDER_DR_EVIDENCE`,
`SA_DR_EVIDENCE_WRITER`, `DR_EVIDENCE_PROJECT`, and `DR_EVIDENCE_BUCKET` as protected environment
variables. The service account may create objects in the evidence prefix but may not delete,
overwrite, change retention, or administer the bucket.

The primary operator must be the dispatching GitHub actor. The report must bind that actor as
`primary`, bind a different login as `observer`, match the protected environment, and include the
caller's exact commit SHA. Environment approval supplies the independent review boundary. New
reports use schema v3 and must also bind the execution packet to an exact Mindclade GitHub pull
request or issue URL in `change_reference`.

## Evidence retention

The workflow validates report v2 or v3 before cloud authentication. Schema v2 remains accepted for
historical reports; create new execution packets with schema v3. The workflow then writes the report
to a content-addressed GCS object using a generation-zero precondition, so a prior object cannot be
replaced. The evidence bucket is separately governed with a seven-year retention policy and
multi-region placement. A 90-day GitHub Actions artifact is retained as a complementary execution
record; GCS is the durable archive.

## Caller example

```yaml
---
jobs:
  evidence:
    # Replace only after a coordinated immutable release publishes this workflow.
    uses: mindclade/.github/.github/workflows/reusable-dr-evidence.yml@<published-release-tag>
    with:
      report-path: drills/reports/staging-gke-20260820.json
      environment: staging
      primary-operator: operator-login
      observer-operator: observer-login
    permissions:
      contents: read
      id-token: write
```

Never construct a passing report ahead of a drill. Populate timestamps, observed RPO/RTO, command
records, evidence hashes, failures, and corrective actions from the actual execution. Validate it
locally with:

```sh
python3 tools/validate_drill_report.py path/to/report.json
```
