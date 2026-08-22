#!/usr/bin/env python3
# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary

from __future__ import annotations

import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "reusable-nix-qualification.yml"
CALLER = ROOT / ".github" / "workflows" / "nix-qualification.yml"


class NixQualificationTests(unittest.TestCase):
    def test_shared_contract_is_locked_and_native(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("nix flake check --no-update-lock-file --show-trace", text)
        self.assertIn("nix flake metadata --no-write-lock-file", text)
        self.assertIn("EXPECTED_SYSTEM: x86_64-linux", text)
        self.assertIn("EXPECTED_SYSTEM: aarch64-linux", text)
        self.assertIn("EXPECTED_SYSTEM: aarch64-darwin", text)
        self.assertIn("runs-on: ubuntu-24.04-arm", text)
        self.assertIn("runs-on: macos-26", text)

    def test_rebuilds_are_independent_and_compared(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        workflow = yaml.load(text, Loader=yaml.BaseLoader)
        jobs = workflow["jobs"]
        self.assertEqual(text.count("nix build --no-link --rebuild"), 2)
        self.assertEqual(jobs["rebuild_a"]["runs-on"], "ubuntu-24.04")
        self.assertEqual(jobs["rebuild_b"]["runs-on"], "ubuntu-22.04")
        self.assertNotEqual(
            jobs["rebuild_a"]["runs-on"], jobs["rebuild_b"]["runs-on"]
        )
        for job_name, expected_version in (
            ("rebuild_a", "test \"${VERSION_ID}\" = 24.04"),
            ("rebuild_b", "test \"${VERSION_ID}\" = 22.04"),
        ):
            run = jobs[job_name]["steps"][-2]["run"]
            self.assertIn(expected_version, run)
            self.assertIn("runner-image", run)
        compare_run = jobs["compare_rebuilds"]["steps"][-1]["run"]
        self.assertIn('test "${image_a}" = ubuntu-24.04', compare_run)
        self.assertIn('test "${image_b}" = ubuntu-22.04', compare_run)
        self.assertIn('test "${image_a}" != "${image_b}"', compare_run)
        self.assertIn("nix hash path --sri", text)
        self.assertIn("diff -u", text)

    def test_required_verdict_is_always_present(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        verdict = text.split("\n  verdict:\n", maxsplit=1)[1]
        self.assertIn("    name: verdict", verdict)
        self.assertIn("    if: always()", verdict)

    def test_first_party_caller_has_unfiltered_triggers(self) -> None:
        text = CALLER.read_text(encoding="utf-8")
        self.assertIn("  pull_request:\n", text)
        self.assertIn("  merge_group:\n", text)
        self.assertIn("  workflow_dispatch:\n", text)
        self.assertIn("  schedule:\n", text)
        self.assertNotIn("    paths:", text)


if __name__ == "__main__":
    unittest.main()
