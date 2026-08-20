#!/usr/bin/env python3
# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_release_readiness", ROOT / "tools" / "validate_release_readiness.py"
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ReleaseReadinessTest(unittest.TestCase):
    def manifest(self) -> dict[str, object]:
        return json.loads(
            (ROOT / "contracts" / "releases" / "v4.0.0.json").read_text(
                encoding="utf-8"
            )
        )

    def test_checked_in_source_evidence_is_valid(self) -> None:
        errors, tag_status = MODULE.validate_manifest(self.manifest(), ROOT)
        self.assertEqual(errors, [])
        self.assertIn(tag_status, {"absent", "present"})

    def test_tampered_required_file_digest_is_rejected(self) -> None:
        manifest = self.manifest()
        manifest["required_files"]["CHANGELOG.md"] = "sha256:" + "0" * 64
        errors, _ = MODULE.validate_manifest(manifest, ROOT)
        self.assertTrue(any("CHANGELOG.md mismatch" in error for error in errors))

    def test_connected_evidence_cannot_be_marked_optional(self) -> None:
        manifest = self.manifest()
        manifest["connected_evidence"]["required"] = False
        errors, _ = MODULE.validate_manifest(manifest, ROOT)
        self.assertIn(
            "connected evidence must remain required and enumerate every release gate",
            errors,
        )


if __name__ == "__main__":
    unittest.main()
