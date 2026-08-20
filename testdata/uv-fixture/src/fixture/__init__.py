"""Exists so reusable-uv-ci has something real to sync, lint, typecheck and test."""


def add(a: int, b: int) -> int:
    """Return a + b. Trivial on purpose: the smoke test proves the workflow runs."""
    return a + b
