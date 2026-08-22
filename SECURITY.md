<!-- mindclade-doc: security@1 -->

# Mindclade security policy

| Document control | Value |
| --- | --- |
| Owner | Mindclade Security |
| Version | 1.0 |
| Last reviewed | August 21, 2026 |
| Applies to | Mindclade-owned code, services, infrastructure, and web properties |

## Reporting a vulnerability

**Do not open an issue or discussion.** Internal visibility is not a security boundary: reports
posted there are immediately readable by organization members, have no coordinated-disclosure
workflow, and remain in repository history and APIs.

Use one of these private channels:

| Channel | Use it for |
|---|---|
| GitHub private vulnerability reporting | Preferred for code or infrastructure vulnerabilities. Open the advisory on the affected repository so the report, private fork, remediation work, and any CVE remain attached to the correct codebase. |
| `security@mindclade.com` | Security reports that cannot be submitted through GitHub. |
| `biosecurity@mindclade.com` | Screening bypasses, unsafe generations, or other dual-use model behavior. |

Include the affected component and revision, reproduction steps, impact, and a minimal proof of
concept. Do not send credentials, customer data, model weights, restricted biological content,
or sequences of concern. A sanitized job or request identifier is preferred when it lets the
team retrieve the relevant run internally.

Mindclade does not currently advertise a public PGP key. Use GitHub private vulnerability
reporting for sensitive technical material rather than assuming ordinary email is end-to-end
encrypted.

## Response targets

These are operational targets, not contractual support terms. Contractual commitments, where
applicable, are defined in the customer agreement.

| Stage | Target |
|---|---|
| Human acknowledgement | Within 2 business days |
| Initial triage and severity | Within 5 business days |
| Status updates | At least every 7 days while actively remediating |
| Coordinated disclosure | Agreed with the reporter; normally no earlier than 90 days after triage |

Critical issues are escalated immediately through the incident-response process. When a target
will be missed, the security team communicates the revised plan before the target expires.

## Safe harbor

Mindclade will not pursue legal action for good-faith research performed under this policy when
the researcher:

- tests only systems, accounts, and data they own or are explicitly authorized to test;
- stops after establishing impact and does not exfiltrate data, pivot, or disrupt service;
- avoids privacy violations, destructive testing, social engineering, and denial of service;
- reports promptly and allows reasonable time for remediation before disclosure; and
- complies with applicable law.

This safe harbor applies only to the researcher's actions against systems and data controlled by
Mindclade and within the scope stated below. It does not authorize access to third-party systems
or data; bind a third party, service provider, law-enforcement agency, or regulator; waive rights
Mindclade does not own; promise a bounty or payment; or excuse unlawful conduct. Mindclade cannot
authorize activity prohibited by applicable law or by a third party that owns an affected system
or data. Policy changes apply prospectively and do not withdraw safe harbor from research that
qualified under the policy in effect when it was performed.

Ask `security@mindclade.com` before testing when scope or ownership is unclear. Written
authorization from Mindclade does not substitute for any permission required from a third party.

## Scope

In scope are Mindclade-owned code, APIs, SDKs, inference services, infrastructure, and public
web properties. Out of scope are findings that require an already-compromised endpoint or
privileged local attacker, physical attacks, social engineering, volumetric denial of service,
scanner-only findings with no demonstrated impact, and missing hardening headers with no
credible exploit path.

Ordinary accuracy or quality defects belong in the owning repository's model-behavior form.
A biosecurity-control bypass is a security issue and must use a private channel.

## Contributor obligations

Never commit credentials, private keys, production configuration, customer data, model weights,
restricted biological content, or adversarial safety corpora. If a secret is committed, rotate
or revoke it first; history rewriting alone is not remediation.
