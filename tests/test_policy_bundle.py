#!/usr/bin/env python3
# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary

from __future__ import annotations

import importlib.util
import shutil
import tarfile
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "policy_bundle.py"
SPEC = importlib.util.spec_from_file_location("policy_bundle", MODULE_PATH)
assert SPEC and SPEC.loader
policy_bundle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(policy_bundle)
ROOT = MODULE_PATH.parents[1]


class PolicyBundleTest(unittest.TestCase):
    def test_canonical_bundle_verifies_and_build_is_reproducible(self) -> None:
        manifest = policy_bundle.load_manifest()
        self.assertEqual(policy_bundle.verify_sources(manifest, ROOT), [])
        with tempfile.TemporaryDirectory() as temporary:
            first = Path(temporary) / "first.tar.gz"
            second = Path(temporary) / "second.tar.gz"
            first_digest = policy_bundle.build_bundle(
                policy_bundle.DEFAULT_MANIFEST, manifest, ROOT, first
            )
            second_digest = policy_bundle.build_bundle(
                policy_bundle.DEFAULT_MANIFEST, manifest, ROOT, second
            )
            self.assertEqual(first_digest, second_digest)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with tarfile.open(first, "r:gz") as archive:
                names = archive.getnames()
            self.assertIn("manifest.json", names)
            self.assertIn("LICENSE", names)
            self.assertIn("actions/validate-repository-home/validate.py", names)

    def test_sync_repairs_only_declared_target_artifacts(self) -> None:
        manifest = policy_bundle.load_manifest()
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            (target / "contracts").mkdir()
            (target / "contracts" / "repository.yaml").write_text(
                "---\nrepository: bootstrap\n", encoding="utf-8"
            )
            changed = policy_bundle.synchronize(manifest, ROOT, "bootstrap", target)
            self.assertIn(Path("LICENSE"), changed)
            self.assertEqual(
                policy_bundle.verify_target(manifest, ROOT, "bootstrap", target), []
            )
            (target / "LICENSE").write_text("drift\n", encoding="utf-8")
            errors = policy_bundle.verify_target(manifest, ROOT, "bootstrap", target)
            self.assertTrue(any("distributed artifact drift" in error for error in errors))

    def test_sync_rejects_mismatched_repository_identity(self) -> None:
        manifest = policy_bundle.load_manifest()
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            (target / "contracts").mkdir()
            (target / "contracts" / "repository.yaml").write_text(
                "---\nrepository: gitops\n", encoding="utf-8"
            )
            for artifact, relative in policy_bundle.distributions_for(manifest, "bootstrap"):
                destination = target / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / artifact["source"], destination)
            errors = policy_bundle.verify_target(manifest, ROOT, "bootstrap", target)
            self.assertTrue(any("does not identify bootstrap" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
