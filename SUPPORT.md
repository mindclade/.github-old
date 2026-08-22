<!-- mindclade-doc: support@1 -->

# Mindclade support

| Document control | Value |
| --- | --- |
| Owner | Mindclade Engineering |
| Version | 1.0 |
| Last reviewed | August 21, 2026 |

This is the canonical organization routing policy. GitHub does not inherit community files from
an internal `.github` repository, so every governed repository carries a local `SUPPORT.md`
that preserves these boundaries and adds repository-specific routes.

## Routing

| Need | Channel |
|---|---|
| Defect in a repository | Use that repository's bug-report form with sanitized reproduction evidence. |
| Design or cross-component proposal | Use the inherited design-proposal discussion form. |
| Security vulnerability | Follow [`SECURITY.md`](SECURITY.md); never open an issue or discussion. |
| Biosecurity-control bypass or unsafe model behavior | Email `biosecurity@mindclade.com`. |
| Internal operational incident | Use the owning service's runbook and incident-response channel. |
| Contractual customer support | Use the support channel named in the applicable agreement. |

GitHub issues do not carry an SLA. Do not publish credentials, customer data, model weights,
restricted biological content, or sequences of concern in support requests. Prefer sanitized
job, trace, request, or artifact identifiers over copying sensitive payloads.

Repository-specific runbooks and customer agreements override this general routing policy.
