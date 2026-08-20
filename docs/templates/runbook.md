<!-- mindclade-doc-template: runbook@1 -->

# <Observable failure>

> **Use when:** <symptom or alert>  
> **Impact:** <affected users/systems>  
> **Primary owner:** `<team>`  
> **Escalate:** <severity condition and destination>

## Safety rules

- Stop automated mutation before manual recovery.
- Preserve the failing revision, logs, timestamps, and affected resource identifiers.
- Diagnose with read-only commands before changing state.
- Never paste secrets, credentials, customer data, or raw sensitive plan/state output into a
  ticket or chat.

## Prerequisites

- Required access: <access>.
- Required tools: <tools>.
- Required evidence: <incident/change reference>.

## Diagnose

1. <Read-only diagnostic step.>

```sh
<diagnostic command>
```

Expected result and interpretation: <what each branch means>.

## Mitigate

Describe the lowest-risk action that limits impact while diagnosis continues.

## Recover

Number exact recovery steps. Label destructive or irreversible operations and require a
second reviewer before them.

## Verify recovery

- <Service or control-plane health check.>
- <No-drift or no-change check.>
- <Negative authorization or failure-path check, when relevant.>

## Roll back

State when rollback is safe, when forward recovery is required, and how to verify either path.

## Escalation and handoff

List the evidence the next responder needs: incident ID, failing revision, affected scope,
timeline, commands run, outputs retained, mutations performed, and current risk.

## Prevention

Record the durable code, test, alert, or documentation change that should prevent recurrence.

