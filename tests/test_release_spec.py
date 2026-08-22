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
    def test_v5_spec_is_complete(self) -> None:
        value = release_spec.validate_spec(ROOT / "contracts/releases/v5.0.0.json")
        self.assertEqual(value["publication"]["required_approvals"], 2)

    def test_attestation_binds_exact_source_and_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "attestation.json"
            source = "a" * 40
            spec = ROOT / "contracts/releases/v5.0.0.json"
            release_spec.attest(spec, source, output)
            release_spec.verify(spec, output, source)
            value = json.loads(output.read_text(encoding="utf-8"))
            self.assertIn(".github/workflows/reusable-gitops-promote.yml", value["files"])

    def test_wrong_source_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "attestation.json"
            spec = ROOT / "contracts/releases/v5.0.0.json"
            release_spec.attest(spec, "a" * 40, output)
            with self.assertRaisesRegex(release_spec.SpecError, "annotated tag"):
                release_spec.verify(spec, output, "b" * 40)

    def test_omitted_or_extra_attested_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "attestation.json"
            spec = ROOT / "contracts/releases/v5.0.0.json"
            release_spec.attest(spec, "a" * 40, output)
            value = json.loads(output.read_text(encoding="utf-8"))
            value["files"].pop(next(iter(value["files"])))
            output.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(release_spec.SpecError, "inventory"):
                release_spec.verify(spec, output, "a" * 40)


if __name__ == "__main__":
    unittest.main()
