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


def module(name: str, path: Path):  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


writer = module("policy_adoption", ROOT / "tools/policy_adoption.py")
verifier = module(
    "verify_adoption", ROOT / "actions/validate-repository-home/verify_adoption.py"
)


class PolicyAdoptionTests(unittest.TestCase):
    def test_record_binds_release_manifest_and_validator(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            manifest = workspace / "contracts/policy-bundle/manifest.json"
            mirror = workspace / "scripts/validate-repository-home.py"
            manifest.parent.mkdir(parents=True)
            mirror.parent.mkdir(parents=True)
            manifest.write_bytes((ROOT / "contracts/policy-bundle/manifest.json").read_bytes())
            mirror.write_bytes(
                (ROOT / "actions/validate-repository-home/validate.py").read_bytes()
            )
            record = writer.create_record(manifest, mirror, "v5.0.0", "a" * 40)
            record_path = workspace / "contracts/policy-bundle/adoption.json"
            record_path.write_text(json.dumps(record), encoding="utf-8")
            verifier.verify(
                workspace,
                ROOT / "actions/validate-repository-home",
                "a" * 40,
                "contracts/policy-bundle/adoption.json",
                "scripts/validate-repository-home.py",
            )

    def test_different_action_ref_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            manifest = workspace / "contracts/policy-bundle/manifest.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_bytes((ROOT / "contracts/policy-bundle/manifest.json").read_bytes())
            validator = ROOT / "actions/validate-repository-home/validate.py"
            record = writer.create_record(manifest, validator, "v5.0.0", "a" * 40)
            record_path = workspace / "contracts/policy-bundle/adoption.json"
            record_path.write_text(json.dumps(record), encoding="utf-8")
            with self.assertRaisesRegex(verifier.AdoptionError, "action ref"):
                verifier.verify(
                    workspace,
                    ROOT / "actions/validate-repository-home",
                    "b" * 40,
                    "contracts/policy-bundle/adoption.json",
                    "",
                )


if __name__ == "__main__":
    unittest.main()
