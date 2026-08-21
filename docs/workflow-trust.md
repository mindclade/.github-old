<!-- mindclade-doc: concept@1 -->

# Mindclade · Workflow trust

> **Audience:** Workflow authors, control-repository maintainers, and security reviewers
> **Outcome:** Understand which repository owns workflow code, which controls establish trust,
> and what a caller must verify before adoption.

## Trust contract

Reusable workflow implementation lives in `.github`; required-workflow targeting and Actions
policy live in `github-config`; cloud authorization lives in `bootstrap` or
`infrastructure-live`. No repository may collapse those authorities into a caller-controlled
credential path.

| Control | Required behavior | Evidence |
| --- | --- | --- |
| Release identity | Consumer pins an existing immutable full semantic version such as `v3.0.0` | Protected tag and immutable GitHub Release |
| Caller permissions | Caller grants only the permissions the called job needs | Caller job and workflow contract snapshot |
| Third-party actions | Every external action uses a full commit SHA | Pin validator and organization Actions policy |
| Cloud authentication | Job exchanges GitHub OIDC through the approved WIF provider | Exact repository, workflow, ref, environment, and audience conditions |
| Secrets | Values remain environment-scoped and do not become workflow outputs | Protected environment and explicit secret contract |

A called workflow cannot elevate `GITHUB_TOKEN` beyond the permissions granted by its caller.
Cloud credentials are runner-local to the job that performs OIDC authentication and must not
escape through reusable-workflow outputs or artifacts.

## Consumer checklist

Before adopting or upgrading a workflow:

1. Review the caller-visible contract and changelog for the exact release.
2. Pin the full semantic version; do not use `main`, a branch, or a moving major alias.
3. Grant only the documented caller permissions and protected environment.
4. Verify expected job IDs because rulesets require job checks, not step names.
5. Run positive qualification and a denied wrong-repository, wrong-ref, or wrong-workflow test
   for any WIF-enabled path.

## Related documentation

- [GitHub platform architecture](architecture.md)
- [OIDC and WIF contract](WIF.md)
- [Reusable workflow contracts](WORKFLOW_CONTRACTS.md)
- [Shared workflow release policy](release-policy.md)
