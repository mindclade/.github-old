#!/usr/bin/env python3
# Copyright © 2026 Mindclade, LLC. All Rights Reserved.
# Mindclade Proprietary and Confidential.
# SPDX-License-Identifier: LicenseRef-Mindclade-Proprietary

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


def run_scripts(text: str) -> list[str]:
    lines = text.splitlines()
    scripts: list[str] = []
    index = 0
    while index < len(lines):
        match = re.match(r"^(\s*)run:\s*(.*)$", lines[index])
        if match is None:
            index += 1
            continue
        indentation, body = match.groups()
        if body not in {"|", ">"}:
            scripts.append(body)
            index += 1
            continue
        start = index + 1
        index = start
        while index < len(lines):
            line = lines[index]
            if line and len(line) - len(line.lstrip()) <= len(indentation):
                break
            index += 1
        scripts.append("\n".join(lines[start:index]))
    return scripts


class WorkflowSecurityTests(unittest.TestCase):
    def test_uv_inputs_are_not_interpolated_into_shell_scripts(self) -> None:
        text = (WORKFLOWS / "reusable-uv-ci.yml").read_text(encoding="utf-8")
        scripts = "\n".join(run_scripts(text))

        self.assertNotIn("${{ inputs.packages }}", scripts)
        self.assertNotIn("${{ inputs.pytest-args }}", scripts)
        self.assertEqual(text.count("PACKAGES: ${{ inputs.packages }}"), 2)
        self.assertEqual(text.count("PYTEST_ARGS: ${{ inputs.pytest-args }}"), 1)
        self.assertIn('read -r -a package_args <<< "${PACKAGES:-}"', scripts)
        self.assertIn('read -r -a pytest_args <<< "${PYTEST_ARGS:-}"', scripts)

    def test_qualification_image_ref_is_not_interpolated_into_shell(self) -> None:
        text = (WORKFLOWS / "reusable-arc-oci-qualify.yml").read_text(
            encoding="utf-8"
        )
        scripts = "\n".join(run_scripts(text))

        self.assertNotIn("${{ inputs.image-ref }}", scripts)
        self.assertEqual(
            text.count("EXPECTED_IMAGE_REF: ${{ inputs.image-ref }}"),
            2,
        )
        self.assertEqual(scripts.count('--expected-image-ref "$EXPECTED_IMAGE_REF"'), 2)

    def test_dependency_review_covers_merge_queue_and_fails_closed(self) -> None:
        text = (WORKFLOWS / "required-security-baseline.yml").read_text(
            encoding="utf-8"
        )
        dependency_review = text.split("\n  dependency-review:\n", maxsplit=1)[1].split(
            "\n  action-pin-policy:\n", maxsplit=1
        )[0]
        verdict = text.split("\n  verdict:\n", maxsplit=1)[1]

        self.assertNotRegex(dependency_review, r"(?m)^    if:")
        self.assertIn("github.event.merge_group.base_sha", dependency_review)
        self.assertIn("github.event.merge_group.head_sha", dependency_review)
        self.assertNotIn("success|skipped", verdict)
        self.assertIn('[ "${DEPENDENCY_REVIEW}" != "success" ]', verdict)

    def test_actionlint_does_not_allow_retired_attest_runner(self) -> None:
        text = (ROOT / ".github" / "actionlint.yaml").read_text(encoding="utf-8")
        self.assertNotIn("mindclade-arc-qualify-attest", text)

    def test_nix_cache_population_keeps_signing_and_pull_requests_out(self) -> None:
        text = (WORKFLOWS / "reusable-nix-cache-populate.yml").read_text(
            encoding="utf-8"
        )
        scripts = "\n".join(run_scripts(text))

        self.assertIn("environment: nix-cache-publication", text)
        self.assertIn("group: nix-cache-population-${{ github.repository }}", text)
        self.assertIn("cancel-in-progress: false", text)
        self.assertIn("persist-credentials: false", text)
        self.assertNotIn("id-token: write", text)
        self.assertNotIn("pull_request", text)
        self.assertNotIn("merge_group", text)
        self.assertNotIn("SIGNING_KEY", text)
        self.assertNotIn("RS256_SECRET", text)
        self.assertNotIn("${{ inputs.server-endpoint }}", scripts)
        self.assertNotIn("${{ inputs.cache-name }}", scripts)
        self.assertNotIn("${{ inputs.trusted-public-key }}", scripts)
        self.assertNotIn("cache-write-token:", text)
        self.assertNotIn("${{ secrets.NIX_CACHE_WRITE_TOKEN }}", scripts)
        self.assertIn(
            "ATTIC_CACHE_WRITE_TOKEN: ${{ secrets.NIX_CACHE_WRITE_TOKEN }}", text
        )
        self.assertIn('test "${ACTUAL_REF_PROTECTED}" = "true"', scripts)
        self.assertIn("python3 ci/nix_cache/populate.py --execute", scripts)

    def test_nix_native_qualification_retains_cross_platform_evidence(self) -> None:
        text = (WORKFLOWS / "reusable-nix-qualification.yml").read_text(
            encoding="utf-8"
        )

        for system in ("x86_64-linux", "aarch64-linux", "aarch64-darwin"):
            self.assertIn(f"EXPECTED_SYSTEM: {system}", text)
        self.assertEqual(text.count("mindclade-nix-native-evidence-v1"), 3)
        self.assertEqual(text.count("Record native qualification evidence"), 3)
        self.assertEqual(text.count("path: ${{ runner.temp }}/nix-native-evidence"), 3)
        self.assertEqual(text.count("retention-days: 30"), 5)
        self.assertNotIn("continue-on-error: true", text)


if __name__ == "__main__":
    unittest.main()
