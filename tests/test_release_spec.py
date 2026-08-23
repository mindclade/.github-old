#!/usr/bin/env python3
# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "validate-release-spec.py"
SPEC = importlib.util.spec_from_file_location("release_spec", MODULE_PATH)
assert SPEC and SPEC.loader
release_spec = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release_spec)


class ReleaseSpecTests(unittest.TestCase):
    def test_v5_spec_covers_every_release_surface(self) -> None:
        value = release_spec.validate_spec(ROOT / "contracts/releases/v5.0.0.json")
        files = release_spec.expand_surfaces(value)
        self.assertEqual(value["schema_version"], 2)
        self.assertEqual(value["publication"]["required_approvals"], 2)
        self.assertIn("actions/validate-repository-home/validate.py", files)
        self.assertIn(".github/workflows/required-repository-policy.yml", files)
        self.assertIn("contracts/policy-bundle/manifest.json", files)
        self.assertIn(
            ".github/workflows/reusable-nixos-gce-image-publish.yml", files
        )
        self.assertIn("tools/validate-release-spec.py", files)
        self.assertIn("tools/verify_release_tag.py", files)

    def test_attestation_binds_exact_source_and_recursive_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "attestation.json"
            source = "a" * 40
            spec = ROOT / "contracts/releases/v5.0.0.json"
            release_spec.attest(spec, source, output)
            release_spec.verify(spec, output, source)
            value = json.loads(output.read_text(encoding="utf-8"))
            self.assertIn("actions/validate-repository-home/README.md", value["files"])

    def test_wrong_source_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "attestation.json"
            spec = ROOT / "contracts/releases/v5.0.0.json"
            release_spec.attest(spec, "a" * 40, output)
            with self.assertRaisesRegex(release_spec.SpecError, "annotated tag"):
                release_spec.verify(spec, output, "b" * 40)

    def test_truncated_attestation_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "attestation.json"
            spec = ROOT / "contracts/releases/v5.0.0.json"
            release_spec.attest(spec, "a" * 40, output)
            value = json.loads(output.read_text(encoding="utf-8"))
            value["files"].pop(next(iter(value["files"])))
            output.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(release_spec.SpecError, "file map"):
                release_spec.verify(spec, output, "a" * 40)

    def test_omitted_surface_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            spec_path = Path(directory) / "releases" / "v5.0.0.json"
            spec_path.parent.mkdir()
            value = json.loads(
                (ROOT / "contracts/releases/v5.0.0.json").read_text(encoding="utf-8")
            )
            value["release_surfaces"]["policy_tools"].pop()
            spec_path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(release_spec.SpecError, "incomplete"):
                release_spec.validate_spec(spec_path)

    def test_unpublished_v4_is_retired_and_not_publishable(self) -> None:
        retired = ROOT / "contracts/releases/retired/v4.0.0.json"
        self.assertFalse((ROOT / "contracts/releases/v4.0.0.json").exists())
        self.assertEqual(
            json.loads(retired.read_text(encoding="utf-8"))["status"],
            "superseded-unpublished",
        )
        with self.assertRaises(release_spec.SpecError):
            release_spec.validate_spec(retired)


if __name__ == "__main__":
    unittest.main()
