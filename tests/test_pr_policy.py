#!/usr/bin/env python3
# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_pr_policy", ROOT / "tools/validate_pr_policy.py"
)
assert SPEC and SPEC.loader
policy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(policy)

CHECKED = """
- [x] I am authorized under a current written agreement with Mindclade, LLC. to submit.
- [X] I identified every third-party component, dataset, model, font, media, and source.
- [x] I updated `LICENSE`, `NOTICE`, the SBOM, or other license evidence as needed.
"""
RELEASE_COMMIT = "a" * 40


class PullRequestPolicyTests(unittest.TestCase):
    def errors(self, body: str, *, title: str = "change", draft: bool = False) -> list[str]:
        event = {"pull_request": {"body": body, "title": title, "draft": draft}}
        return policy.validate_body(
            event, "2026.08.21.4", "v5.0.0", RELEASE_COMMIT
        )

    def test_checked_authorization_passes(self) -> None:
        self.assertEqual(self.errors(CHECKED), [])

    def test_checked_canonical_template_wrapping_passes(self) -> None:
        body = """
- [x] I am authorized under a current written agreement with Mindclade, LLC. to
      submit every part of this contribution.
- [x] I identified every third-party component, dataset, model, font, media,
      specification, or generated artifact and preserved its source and license.
- [x] I updated `LICENSE`, `NOTICE`, the SBOM, or other license evidence when
      the included or distributed material changed.
"""
        self.assertEqual(self.errors(body), [])

    def test_drafts_do_not_block_on_incomplete_template(self) -> None:
        self.assertEqual(self.errors("DO NOT MERGE", draft=True), [])

    def test_hold_and_unchecked_authorization_are_rejected(self) -> None:
        errors = self.errors("- [ ] I am authorized\n", title="DO NOT MERGE")
        self.assertTrue(any("hold marker" in error for error in errors))
        self.assertEqual(sum("authorization remains unchecked" in error for error in errors), 3)

    def test_stale_or_unpublished_bundle_marker_is_rejected(self) -> None:
        body = CHECKED + """
<!-- mindclade-policy-bundle: version=2026.08.21.3; release=v5.0.0; release_commit=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa; status=candidate -->
"""
        errors = self.errors(body)
        self.assertTrue(any("stale version" in error for error in errors))
        self.assertTrue(any("status=published" in error for error in errors))

    def test_exact_published_bundle_marker_passes(self) -> None:
        body = CHECKED + """
<!-- mindclade-policy-bundle: version=2026.08.21.4; release=v5.0.0; release_commit=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa; status=published -->
"""
        self.assertEqual(self.errors(body), [])

    def test_governed_change_requires_exact_release_commit(self) -> None:
        missing = policy.validate_body(
            {"pull_request": {"body": CHECKED, "title": "change", "draft": False}},
            "2026.08.21.4",
            "v5.0.0",
            RELEASE_COMMIT,
            True,
        )
        self.assertTrue(any("require exactly one" in error for error in missing))

        wrong = CHECKED + """
<!-- mindclade-policy-bundle: version=2026.08.21.4; release=v5.0.0; release_commit=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb; status=published -->
"""
        errors = policy.validate_body(
            {"pull_request": {"body": wrong, "title": "change", "draft": False}},
            "2026.08.21.4",
            "v5.0.0",
            RELEASE_COMMIT,
            True,
        )
        self.assertTrue(any("unexpected release commit" in error for error in errors))

    def test_manifest_distribution_paths_require_provenance(self) -> None:
        manifest = ROOT / "contracts/policy-bundle/manifest.json"
        self.assertTrue(
            policy.requires_provenance(manifest, "mindclade/bootstrap", ["LICENSE"])
        )
        self.assertTrue(
            policy.requires_provenance(
                manifest,
                "mindclade/bootstrap",
                ["contracts/policy-bundle/adoption.json"],
            )
        )
        self.assertFalse(
            policy.requires_provenance(
                manifest, "mindclade/bootstrap", ["docs/README.md"]
            )
        )

    def test_canonical_source_does_not_require_prepublication_provenance(self) -> None:
        manifest = ROOT / "contracts/policy-bundle/manifest.json"
        self.assertFalse(
            policy.requires_provenance(
                manifest,
                "mindclade/.github",
                ["contracts/policy-bundle/manifest.json"],
            )
        )


if __name__ == "__main__":
    unittest.main()
