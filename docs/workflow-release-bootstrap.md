# Shared workflow contract bootstrap

1. Commit the `.github` repository to protected `main`.
2. Complete its required checks and create the protected `v1` workflow-contract tag.
3. Apply `github-config` tag rules before allowing downstream changes.
4. Downstream repositories reference `Mindclade/.github/.github/workflows/<workflow>@v1`.
5. Breaking workflow contracts use a new protected major tag. Existing major tags cannot be moved or deleted.

Third-party Actions remain pinned to immutable 40-character commit SHAs or OCI digests.
