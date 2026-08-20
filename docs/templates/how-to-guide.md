<!-- mindclade-doc-template: how-to@1 -->

# <Goal-oriented title>

> **Audience:** <Who performs this task>  
> **Outcome:** <Observable result when the procedure succeeds>  
> **Risk:** <Low, moderate, high, or critical, with the main reason>

## Before you begin

- Required access: <roles or protected environment>.
- Required tools: <pinned toolchain>.
- Required evidence: <ticket, plan, backup, or approval>.
- Stop condition: <condition that makes proceeding unsafe>.

## Procedure

1. Start each step with an action verb.
2. State where commands run and what they change.
3. Put copyable commands in fenced blocks.

```sh
<command>
```

Expected result: `<signal the operator can verify>`.

## Verify

List independent checks that prove the desired state, not merely that the command exited
successfully.

## Roll back or recover

State the safe rollback boundary. If rollback can be destructive or is not possible, say so
and link to the recovery runbook.

## Troubleshooting

### `<observable symptom or exact error>`

- Likely cause: <cause>.
- Check: `<diagnostic command>`.
- Corrective action: <safe action>.

## Related documentation

- <Authoritative reference or architecture page.>

