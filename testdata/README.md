# testdata

Minimal fixture projects for `smoke.yml`, which calls the reusable CI workflows against them
on a schedule and on changes to the workflows themselves.

Each fixture is the smallest project its toolchain accepts, with one passing test. They exist
to prove the *workflows* still run end to end — checkout, toolchain setup, lint, test — not to
exercise the toolchains. A fixture failure means a reusable workflow broke, and it means that
BEFORE a tag was cut, instead of after, in six consuming repositories.

Lockfiles here are real and committed, because the workflows enforce lockfile freshness and a
fixture without one would fail for the wrong reason.
