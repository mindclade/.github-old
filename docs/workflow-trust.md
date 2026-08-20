<!-- mindclade-doc: concept@1 -->

# Workflow trust

Reusable workflows are immutable-versioned, least-privilege, and explicit about secrets. Cloud authentication uses OIDC and must be constrained by repository, workflow identity, ref, and protected environment. Reusable workflow implementation lives here; required-workflow targeting lives in `github-config`.

Consumers pin a full semantic version such as `v3.0.0`; moving major aliases and branches are
not trust anchors. A called workflow cannot elevate `GITHUB_TOKEN` beyond the permissions its
caller grants, and cloud credentials are runner-local to the job that performs OIDC
authentication.

See [GitHub platform architecture](architecture.md), [OIDC and WIF](WIF.md), and
[Shared workflow release policy](release-policy.md) for the authoritative lifecycle.
